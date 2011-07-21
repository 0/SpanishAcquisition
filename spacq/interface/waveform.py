import csv
from functools import wraps
from numpy import cos, deg2rad, interp, linspace, sin
from os import chdir, getcwd
import struct
import wave

"""
A waveform generator.
"""


def read_wave(path):
	"""
	Read waveform data from a WAVE file.

	Each point returned is on the interval [-1.0, 1.0].
	"""

	input = wave.open(path, 'r')

	bytes_per_sample = input.getsampwidth()

	if bytes_per_sample == 1:
		unpack_format = '<%db'
	elif bytes_per_sample == 2:
		unpack_format = '<%dh'
	elif bytes_per_sample == 4:
		unpack_format = '<%dl'
	elif bytes_per_sample == 8:
		unpack_format = '<%dq'
	else:
		raise ValueError('Invalid sample width: %d' % (bytes_per_sample))

	bits = 8 * bytes_per_sample - 1
	min_value = -float(2 ** bits)
	max_value = +float(2 ** bits - 1)
	value_range = max_value - min_value

	data = []

	new_data_len = -1
	while new_data_len != 0:
		new_data = input.readframes(1024)
		new_data_len = len(new_data) / bytes_per_sample

		raw_data = struct.unpack(unpack_format % (new_data_len), new_data)
		data += [2 * float(x - min_value) / value_range - 1.0 for x in raw_data]

	return data


def command(commands):
	"""
	Decoractor for wave-generating command methods.
	"""

	def wrapper(f):
		commands[f.__name__] = f

		return f

	return wrapper


def includes(f):
	"""
	Decorator for command methods which include files.

	These commands need to have the current working directory changed.
	"""

	@wraps(f)
	def wrapped(self, *args, **kwargs):
		if self.cwd is not None:
			old_cwd = getcwd()
			chdir(self.cwd)

			try:
				return f(self, *args, **kwargs)
			finally:
				chdir(old_cwd)
		else:
			return f(self, *args, **kwargs)

	return wrapped


class Generator(object):
	"""
	A generator for arbitrary waveforms.
	"""

	# Methods which are valid commands.
	cmds = {}

	def __init__(self, frequency, min_value=None, max_value=None):
		# The number of samples per second.
		self.frequency = frequency

		self.min_value = min_value
		self.max_value = max_value

		# The resulting wave, with each data point on the interval [-1.0, 1.0].
		self.wave = []

		# The resulting marker channels, with each channel being a sparse list represented as a dictionary.
		self.markers = {}

		# The path relative to which imports are done.
		self.cwd = None

	def run_commands(self, commands):
		"""
		Execute pulse commands.
		"""

		for cmd in commands:
			try:
				f = self.cmds[cmd.command]
			except KeyError as e:
				raise ValueError('Invalid command "{0}".'.format(str(e)))

			f(self, *cmd.arguments)

	def get_marker(self, num):
		"""
		Get the marker values for all data points in the waveform.
		"""

		if num not in self.markers:
			return [False] * len(self.wave)

		result = [False]

		for idx, value in sorted(self.markers[num].items()):
			if idx >= len(result):
				result.extend([result[-1]] * (idx - len(result) + 1))

			result[idx] = value

		if len(result) < len(self.wave):
			result.extend([result[-1]] * (len(self.wave) - len(result)))

		return result

	@command(cmds)
	def set(self, value):
		"""
		Set the next point to have the given amplitude.
		"""

		self.wave.append(value)

	def _parse_time(self, value):
		"""
		Convert a time value to a number of samples based on the frequency.
		"""

		return int(value.value * self.frequency)

	@command(cmds)
	def delay(self, value, less_points=0):
		"""
		Extend the last value of the waveform to last the length of the delay.
		"""

		delay_length = self._parse_time(value) - less_points
		self.wave.extend([self.wave[-1]] * delay_length)

	@command(cmds)
	def square(self, amplitude, length):
		"""
		Generate a square pulse.
		"""

		return_to = self.wave[-1]

		self.set(amplitude)
		self.delay(length, less_points=1)
		self.set(return_to)

	@command(cmds)
	def sweep(self, start, stop, length):
		"""
		Linear sweep.
		"""

		num_samples = self._parse_time(length)
		self.wave.extend(list(linspace(start, stop, num_samples)))

	def _scale_waveform(self, data, amplitude=None, duration=None):
		"""
		Shorten or elongate a waveform in both axes.

		Due to the discrete nature of these waveforms, interpolation is used when changing duration.
		"""

		new_data = data[:]

		# Change amplitude.
		if amplitude is not None:
			new_data = [amplitude * x for x in new_data]

		# Change duration.
		if duration is not None:
			duration = self._parse_time(duration)
			actual_duration = len(new_data)

			points = linspace(0, 1, duration)
			actual_points = linspace(0, 1, actual_duration)

			new_data = interp(points, actual_points, new_data)
			new_data = [round(x, 5) for x in new_data]

		return new_data

	@command(cmds)
	@includes
	def include_wave(self, path, amplitude=None, duration=None):
		"""
		Include the values from an external WAVE-formatted wave.
		"""

		data = self._scale_waveform(read_wave(path), amplitude, duration)
		self.wave.extend(data)

	@command(cmds)
	@includes
	def include_ampph(self, path, axis, amplitude=None, duration=None):
		"""
		Include the values from an external amplitude/phase CSV file.
		"""

		amplitudes = []
		phases = []

		with open(path, 'r') as f:
			for amp, ph in csv.reader(f):
				# Normalize values.
				amplitudes.append(float(amp) / 100)
				phases.append(deg2rad(float(ph)))

		if axis == 'abs':
			data = amplitudes[:]
		elif axis == 'real':
			data = amplitudes * cos(phases)
		elif axis == 'imag':
			data = amplitudes * sin(phases)
		else:
			raise ValueError('Invalid axis: {0}'.format(axis))

		data = self._scale_waveform(data, amplitude, duration)
		self.wave.extend(data)

	@command(cmds)
	def marker(self, num, value):
		"""
		Set the value of a marker starting from the current position.
		"""

		if value not in ['high', 'low']:
			raise ValueError('Invalid value: {0}'.format(value))

		if num not in self.markers:
			self.markers[num] = {}

		self.markers[num][len(self.wave)] = (value == 'high')
