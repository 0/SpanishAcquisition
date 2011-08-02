from numpy import append, array, interp, linspace

"""
A waveform generator.
"""


class Generator(object):
	"""
	A generator for arbitrary waveforms.
	"""

	# Generation should fail if the number of points exceeds this value.
	max_length = 10000000 # 1e7 (0.01 s @ 1 GHz)

	def __init__(self, frequency):
		# The number of samples per second.
		self.frequency = frequency

		# The resulting wave, with each data point on the interval [-1.0, 1.0].
		self.wave = array([])

		# The resulting marker channels, with each channel being a sparse list represented as a dictionary.
		self.markers = {}

	def check_length(self, additional):
		resulting_length = len(self.wave) + additional

		if resulting_length > self.max_length:
			raise ValueError('Waveform is too long; stopping at {0:n} points'.format(resulting_length))

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

	def _set(self, value):
		"""
		Set the next point to have the given amplitude.
		"""

		self.check_length(1)

		self.wave = append(self.wave, value)

	def _parse_time(self, value):
		"""
		Convert a time value to a number of samples based on the frequency.
		"""

		return int(value.value * self.frequency)

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

	def delay(self, value, less_points=1):
		"""
		Extend the last value of the waveform to last the length of the delay.
		"""

		delay_length = self._parse_time(value) - less_points

		try:
			last_value = self.wave[-1]
		except IndexError:
			last_value = 0.0

		self.check_length(delay_length)

		self.wave = append(self.wave, [last_value] * delay_length)

	def square(self, amplitude, length):
		"""
		Generate a square pulse.
		"""

		try:
			return_to = self.wave[-1]
		except IndexError:
			return_to = 0.0

		self._set(amplitude)
		self.delay(length, less_points=1)
		self._set(return_to)

	def pulse(self, values, amplitude, duration):
		"""
		Literal amplitude values.
		"""

		data = self._scale_waveform(values, amplitude, duration)

		self.check_length(len(data))

		self.wave = append(self.wave, data)

	def marker(self, num, value):
		"""
		Set the value of a marker starting from the current position.
		"""

		if value not in ['high', 'low']:
			raise ValueError('Invalid value: {0}'.format(value))

		if num not in self.markers:
			self.markers[num] = {}

		self.markers[num][len(self.wave)] = (value == 'high')
