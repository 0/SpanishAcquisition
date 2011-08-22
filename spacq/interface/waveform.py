import logging
log = logging.getLogger(__name__)

from collections import namedtuple
from numpy import append, array, interp, linspace

"""
A waveform generator.
"""


Waveform = namedtuple('Waveform', 'data, markers')


class Generator(object):
	"""
	A generator for arbitrary waveforms.
	"""

	# Generation should fail if the number of points exceeds this value.
	max_length = 10000000 # 1e7 (0.01 s @ 1 GHz)

	length = 0

	def __init__(self, frequency, dry_run=False):
		# The sampling frequency.
		self.frequency = frequency

		# If True, do not generate a waveform. Useful for verifying the generating code.
		self.dry_run = dry_run

		# The resulting wave, with each data point on the interval [-1.0, 1.0].
		self._wave = array([])

		# The resulting marker channels, with each channel being a sparse list represented as a dictionary.
		self._markers = {}

	@property
	def waveform(self):
		"""
		The waveform and marker data for the generated waveform.
		"""

		try:
			last_marker_point = max(pos for data in self._markers.values() for pos in data.keys())
		except ValueError:
			last_marker_point = -1

		extra_points = last_marker_point + 1 - len(self._wave)
		if extra_points > 0:
			resulting_wave = append(self._wave, [0.0] * extra_points)
		else:
			resulting_wave = self._wave

		marker_data = dict((num, self._get_marker(num, len(resulting_wave))) for num in self._markers)

		return Waveform(resulting_wave, marker_data)

	def check_length(self, additional):
		resulting_length = self.length + additional

		if resulting_length > self.max_length:
			raise ValueError('Waveform is too long; stopping at {0:n} points'.format(resulting_length))

	def append(self, values):
		self.length += len(values)

		if not self.dry_run:
			self._wave = append(self._wave, values)

	def _get_marker(self, num, length):
		"""
		Get the marker values for all data points in the waveform.
		"""

		result = []

		def last_value():
			try:
				return result[-1]
			except IndexError:
				return False

		for idx, value in sorted(self._markers[num].items()):
			if idx >= len(result):
				result.extend([last_value()] * (idx - len(result) + 1))

			result[idx] = value

		if len(result) < length:
			result.extend([last_value()] * (length - len(result)))

		return result

	def _parse_time(self, value):
		"""
		Convert a time value to a number of samples based on the frequency.
		"""

		log.debug('Parsing time "{0!r}" with frequency {1!r}'.format(value, self.frequency))
		result = int(value.value * self.frequency.value)
		log.debug('Parsed time "{0!r}" as {1} samples'.format(value, result))

		return result

	def _scale_waveform(self, data, amplitude=None, duration=None):
		"""
		Shorten or elongate a waveform in both axes.

		Due to the discrete nature of these waveforms, interpolation is used when changing duration.
		"""

		if not data:
			return data

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

	def set_next(self, value):
		"""
		Set the next point to have the given amplitude.
		"""

		self.check_length(1)
		self.append([value])

	def delay(self, value, less_points=1):
		"""
		Extend the last value of the waveform to last the length of the delay.
		"""

		delay_length = self._parse_time(value) - less_points

		self.check_length(delay_length)

		try:
			last_value = self._wave[-1]
		except IndexError:
			last_value = 0.0

		self.append([last_value] * delay_length)

	def square(self, amplitude, length):
		"""
		Generate a square pulse.
		"""

		try:
			return_to = self._wave[-1]
		except IndexError:
			return_to = 0.0

		self.set_next(amplitude)
		self.delay(length, less_points=1)
		self.set_next(return_to)

	def pulse(self, values, amplitude, duration):
		"""
		Literal amplitude values.
		"""

		data = self._scale_waveform(values, amplitude, duration)

		self.check_length(len(data))
		self.append(data)

	def marker(self, num, value):
		"""
		Set the value of a marker starting from the current position.
		"""

		if self.dry_run:
			return

		if num not in self._markers:
			self._markers[num] = {}

		self._markers[num][len(self._wave)] = value
