import logging
log = logging.getLogger(__name__)

from math import ceil
from numpy import linspace
import struct

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice, AbstractSubdevice
from ..tools import str_to_bool, quantity_wrapped, quantity_unwrapped, BlockData

"""
Tektronix DPO7104 Digital Phosphor Oscilloscope

Control the DPO's settings and input waveforms.
"""


class Channel(AbstractSubdevice):
	"""
	Input channel of the DPO.
	"""

	def _setup(self):
		AbstractSubdevice._setup(self)

		# Resources.
		read_only = ['waveform']
		for name in read_only:
			self.resources[name] = Resource(self, name)

		read_write = ['enabled']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['waveform'].slow = True
		self.resources['waveform'].display_units = 'V'
		self.resources['enabled'].converter = str_to_bool

	def __init__(self, device, channel, *args, **kwargs):
		self.channel = channel

		AbstractSubdevice.__init__(self, device, *args, **kwargs)

	@property
	def acquisition_window(self):
		"""
		The minimum and maximum obtainable values in V.
		"""

		# 10 divisions total.
		max_value = 5 * self.scale.value
		min_value = -max_value

		offset = self.offset.value

		return (min_value + offset, max_value + offset)

	def transform_waveform(self, waveform):
		"""
		Transform some curve data onto the true amplitude interval in V, and intermix time values in s.
		"""

		value_min, value_max = self.device.value_range
		value_diff = value_max - value_min

		real_min, real_max = self.acquisition_window
		real_diff = real_max - real_min

		times = linspace(0, self.device.time_scale.value, len(waveform))

		return [(time, real_diff * float(x - value_min) / value_diff + real_min) for time, x in zip(times, waveform)]

	@property
	def enabled(self):
		"""
		The input state (on/off) of the channel.
		"""

		result = self.device.ask('select:ch{0}?'.format(self.channel))
		return bool(int(result))

	@enabled.setter
	def enabled(self, value):
		self.device.write('select:ch{0} {1}'.format(self.channel, 'on' if value else 'off'))

	@property
	@Synchronized()
	def waveform(self):
		"""
		A waveform acquired by the scope.

		Values are returned in the format [(time1, value1), (time2, value2), ...].
		"""

		self.device.status.append('Getting waveform for channel {0}'.format(self.channel))

		try:
			self.device.data_source = self.channel

			if self.device.fastframe:
				# Only get the last frame.
				frame = self.device.fastframe_count
			else:
				frame = 1

			self.device.fastframe_start = frame
			self.device.fastframe_stop = frame

			# Receive in chunks.
			num_data_points = self.device.record_length
			num_transmissions = int(ceil(num_data_points / self.device.max_receive_samples))

			curve = []
			for i in xrange(num_transmissions):
				self.device.data_start = int(i * self.device.max_receive_samples) + 1
				self.device.data_stop = int((i + 1) * self.device.max_receive_samples)

				curve_raw = self.device.ask_raw('curve?')
				curve.append(BlockData.from_block_data(curve_raw))

			curve = ''.join(curve)

			format_code = self.device.byte_format_letters[self.device.waveform_bytes]
			curve_data = struct.unpack('!{0}{1}'.format(num_data_points, format_code), curve)

			return self.transform_waveform(curve_data)
		finally:
			self.device.status.pop()

	@property
	@quantity_wrapped('V')
	def scale(self):
		"""
		Vertical scale for the channel, as a quantity in V.

		Note: This is for a single division, of which there are 10.
		"""

		return float(self.device.ask('ch{0}:scale?'.format(self.channel)))

	@scale.setter
	@quantity_unwrapped('V')
	def scale(self, value):
		self.device.write('ch{0}:scale {1}'.format(self.channel, value))

	@property
	@quantity_wrapped('V')
	def offset(self):
		"""
		Vertical offset for the channel, as a quantity in V.
		"""

		return float(self.device.ask('ch{0}:offset?'.format(self.channel)))

	@offset.setter
	@quantity_unwrapped('V')
	def offset(self, value):
		self.device.write('ch{0}:offset {1}'.format(self.channel, value))


class DPO7104(AbstractDevice):
	"""
	Interface for Tektronix DPO7104 DPO.
	"""

	byte_format_letters = [None, 'b', 'h']

	# The upper limit to the number of samples to be received per transmission.
	max_receive_samples = 1e7

	allowed_stopafters = ['runstop', 'sequence']
	allowed_waveform_bytes = [1, 2] # Channel data only.
	allowed_fastframe_sums = set(['none', 'average', 'envelope'])

	def _setup(self):
		AbstractDevice._setup(self)

		self.channels = [None] # There is no channel 0.
		for chan in xrange(1, 5):
			channel = Channel(self, chan)
			self.channels.append(channel)
			self.subdevices['channel{0}'.format(chan)] = channel

		# Resources.
		read_write = ['sample_rate', 'time_scale']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['sample_rate'].units = 'Hz'
		self.resources['time_scale'].units = 's'

	@Synchronized()
	def reset(self):
		"""
		Reset the device to its default state.
		"""

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	def autoset(self):
		"""
		Autoset the scaling.
		"""

		self.write('autoset execute')

	@property
	def stopafter(self):
		"""
		The acqusition mode.
		"""

		value = self.ask('acquire:stopafter?').lower()

		if value.startswith('runst'):
			return 'runstop'
		elif value.startswith('seq'):
			return 'sequence'

	@stopafter.setter
	def stopafter(self, value):
		if value not in self.allowed_stopafters:
			raise ValueError('Invalid acquisition mode: {0}'.format(value))

		self.write('acquire:stopafter {0}'.format(value))

	@property
	def waveform_bytes(self):
		"""
		Number of bytes per data point in the acquired waveforms.
		"""

		return int(self.ask('wfmoutpre:byt_nr?'))

	@waveform_bytes.setter
	def waveform_bytes(self, value):
		self.write('wfmoutpre:byt_nr {0}'.format(value))

	@property
	def value_range(self):
		"""
		Range of values possible for each data point.
		"""

		# The returned values are signed.
		bits = 8 * self.waveform_bytes - 1
		max_val = 2 ** bits

		return (-max_val, max_val - 1)

	@property
	def acquiring(self):
		"""
		Whether the device is currently acquiring data.
		"""

		result = self.ask('acquire:state?')
		return bool(int(result))

	@acquiring.setter
	def acquiring(self, value):
		self.write('acquire:state {0}'.format(str(int(value))))

	@property
	@quantity_wrapped('Hz')
	def sample_rate(self):
		"""
		The sample rate in s-1.
		"""

		return float(self.ask('horizontal:mode:samplerate?'))

	@sample_rate.setter
	@quantity_unwrapped('Hz')
	def sample_rate(self, value):
		self.write('horizontal:mode:samplerate {0}'.format(value))

	@property
	@quantity_wrapped('s')
	def time_scale(self):
		"""
		The length for a waveform.
		"""

		return float(self.ask('horizontal:divisions?')) * float(self.ask('horizontal:mode:scale?'))

	@time_scale.setter
	@quantity_unwrapped('s')
	def time_scale(self, value):
		self.write('horizontal:mode:scale {0}'.format(value / float(self.ask('horizontal:divisions?'))))

	@property
	def data_source(self):
		"""
		The source from which to transfer data.
		"""

		result = self.ask('data:source?')
		assert len(result) == 3 and result.startswith('CH')

		return int(result[2])

	@data_source.setter
	def data_source(self, value):
		self.write('data:source ch{0}'.format(value))

	@property
	def data_start(self):
		"""
		The first data point to transfer.
		"""

		return int(self.ask('data:start?'))

	@data_start.setter
	def data_start(self, value):
		self.write('data:start {0}'.format(value))

	@property
	def data_stop(self):
		"""
		The last data point to transfer.
		"""

		return int(self.ask('data:stop?'))

	@data_stop.setter
	def data_stop(self, value):
		self.write('data:stop {0}'.format(value))

	@property
	def record_length(self):
		"""
		The number of data points in a waveform.
		"""

		return int(self.ask('horizontal:mode:recordlength?'))

	@Synchronized()
	def acquire(self):
		"""
		Cause the DPO to acquire a single waveform.
		"""

		self.acquiring = True

	@property
	def fastframe(self):
		"""
		Whether fastframe is enabled.
		"""

		return bool(int(self.ask('horizontal:fastframe:state?')))

	@fastframe.setter
	def fastframe(self, value):
		return self.write('horizontal:fastframe:state {0}'.format(int(value)))

	@property
	def fastframe_sum(self):
		"""
		The fastframe summary frame.
		"""

		result = self.ask('horizontal:fastframe:sumframe?').lower()

		if result.startswith('non'):
			return 'none'
		elif result.startswith('env'):
			return 'envelope'
		elif result.startswith('ave'):
			return 'average'
		else:
			ValueError('Unknown summary mode: {0}'.format(result))

	@fastframe_sum.setter
	def fastframe_sum(self, value):
		if value not in self.allowed_fastframe_sums:
			raise ValueError('Invalid summary frame mode: {0}'.format(value))

		return self.write('horizontal:fastframe:state {0}'.format(value))

	@property
	def fastframe_count(self):
		"""
		The number of waveforms to acquire in fastframe mode.
		"""

		return int(self.ask('horizontal:fastframe:count?'))

	@fastframe_count.setter
	def fastframe_count(self, value):
		if value <= 0:
			raise ValueError('Must provide a positive integer, not "{0}"'.format(value))

		self.write('horizontal:fastframe:count {0:d}'.format(value))

	@property
	def fastframe_start(self):
		"""
		The first frame to transfer.
		"""

		return int(self.ask('data:framestart?'))

	@fastframe_start.setter
	def fastframe_start(self, value):
		self.write('data:framestart {0}'.format(value))

	@property
	def fastframe_stop(self):
		"""
		The last frame to transfer.
		"""

		return int(self.ask('data:framestop?'))

	@fastframe_stop.setter
	def fastframe_stop(self, value):
		self.write('data:framestop {0}'.format(value))

	@property
	def acquisitions(self):
		"""
		The number of acquisitions made so far on the oscilloscope.
		"""

		return int(self.ask('acquire:numacq?'))

name = 'DPO7104'
implementation = DPO7104
