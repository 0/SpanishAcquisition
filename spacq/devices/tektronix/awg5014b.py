import logging
log = logging.getLogger(__name__)

import struct

from spacq.interface.resources import Resource
from spacq.interface.units import Quantity
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice, AbstractSubdevice
from ..tools import str_to_bool, quantity_wrapped, quantity_unwrapped, BlockData

"""
Tektronix AWG5014B Arbitrary Waveform Generator

Control the AWG's settings and output waveforms.
"""


class Marker(AbstractSubdevice):
	"""
	Marker channel of an output channel.
	"""

	def _setup(self):
		AbstractSubdevice._setup(self)

		# Resources.
		read_write = ['delay', 'high', 'low']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['delay'].units = 's'
		self.resources['high'].units = 'V'
		self.resources['low'].units = 'V'

	def __init__(self, device, channel, number, *args, **kwargs):
		AbstractSubdevice.__init__(self, device, *args, **kwargs)

		self.channel = channel
		self.number = number

	@property
	@quantity_wrapped('s')
	def delay(self):
		"""
		The marker delay, as a quantity in s.
		"""

		return float(self.device.ask('source{0}:marker{1}:delay?'.format(self.channel, self.number)))

	@delay.setter
	@quantity_unwrapped('s')
	def delay(self, v):
		self.device.write('source{0}:marker{1}:delay {2}'.format(self.channel, self.number, v))

	@property
	@quantity_wrapped('V')
	def high(self):
		"""
		The marker high voltage, as a quantity in V.
		"""

		return float(self.device.ask('source{0}:marker{1}:voltage:high?'.format(self.channel, self.number)))

	@high.setter
	@quantity_unwrapped('V')
	def high(self, v):
		self.device.write('source{0}:marker{1}:voltage:high {2}'.format(self.channel, self.number, v))

	@property
	@quantity_wrapped('V')
	def low(self):
		"""
		The marker low voltage, as a quantity in V.
		"""

		return float(self.device.ask('source{0}:marker{1}:voltage:low?'.format(self.channel, self.number)))

	@low.setter
	@quantity_unwrapped('V')
	def low(self, v):
		self.device.write('source{0}:marker{1}:voltage:low {2}'.format(self.channel, self.number, v))


class Channel(AbstractSubdevice):
	"""
	Output channel of the AWG.
	"""

	# Zero-to-peak amplitude range.
	min_amplitude = 0.01 # V
	max_amplitude = 2.25 # V

	def _setup(self):
		AbstractSubdevice._setup(self)

		self.markers = [None] # There is no marker 0.
		for mark in xrange(1, 3):
			marker = Marker(self.device, self.channel, mark)
			self.markers.append(marker)
			self.subdevices['marker{0}'.format(mark)] = marker

		# Resources.
		read_write = ['waveform_name', 'enabled', 'amplitude']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['enabled'].converter = str_to_bool
		self.resources['amplitude'].units = 'V'

	def __init__(self, device, channel, *args, **kwargs):
		self.channel = channel

		AbstractSubdevice.__init__(self, device, *args, **kwargs)

	@property
	def waveform_name(self):
		"""
		The name of the output waveform for the channel.
		"""

		result = self.device.ask('source{0}:waveform?'.format(self.channel))
		# The name is in quotes.
		return result[1:-1]

	@waveform_name.setter
	def waveform_name(self, v):
		self.device.write('source{0}:waveform "{1}"'.format(self.channel, v))

	@waveform_name.deleter
	def waveform_name(self):
		self.waveform_name = ''

	@property
	def enabled(self):
		"""
		The output state (on/off) of the channel.
		"""

		result = self.device.ask('output{0}:state?'.format(self.channel))
		# The value is a string holding a digit.
		return bool(int(result))

	@enabled.setter
	def enabled(self, v):
		self.device.write('output{0}:state {1}'.format(self.channel, int(v)))

	@property
	@quantity_wrapped('V')
	def amplitude(self):
		"""
		The zero-to-peak amplitude of the channel in V.
		"""

		# Convert peak-to-peak to zero-to-peak.
		return float(self.device.ask('source{0}:voltage?'.format(self.channel))) / 2

	@amplitude.setter
	@quantity_unwrapped('V')
	def amplitude(self, v):
		# Convert zero-to-peak to peak-to-peak.
		self.device.write('source{0}:voltage {1:E}'.format(self.channel, 2 * v))

	def set_waveform(self, waveform, markers=None, name=None):
		"""
		Set the waveform on this channel.

		The waveform data should be in V.
		"""

		if name is None:
			name = 'Channel {0}'.format(self.channel)

		# Clear existing.
		if name in self.device.waveform_names:
			self.device.delete_waveform(name)

		# Normalize waveform.
		max_amp = max(abs(x) for x in waveform)
		if max_amp > self.max_amplitude:
			raise ValueError('Amplitude {0} V exceeds maximum of {1} V'.format(max_amp, self.max_amplitude))
		elif max_amp > 0:
			if max_amp < self.min_amplitude:
				max_amp = self.min_amplitude

			waveform = [x / max_amp for x in waveform]

			self.amplitude = Quantity(max_amp, 'V')

		# Create new.
		self.device.create_waveform(name, waveform, markers)
		self.waveform_name = name


class AWG5014B(AbstractDevice):
	"""
	Interface for Tektronix AWG5014B AWG.
	"""

	allowed_run_modes = set(['continuous', 'triggered', 'gated', 'sequence'])

	def _setup(self):
		AbstractDevice._setup(self)

		self.channels = [None] # There is no channel 0.
		for chan in xrange(1, 5):
			channel = Channel(self, chan)
			self.channels.append(channel)
			self.subdevices['channel{0}'.format(chan)] = channel

		# Resources.
		read_write = ['sampling_rate', 'run_mode', 'enabled']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['sampling_rate'].units = 'Hz'
		self.resources['run_mode'].allowed_values = self.allowed_run_modes
		self.resources['enabled'].converter = str_to_bool

	@Synchronized()
	def reset(self):
		"""
		Reset the device to its default state.
		"""

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	@property
	def data_bits(self):
		"""
		How many bits of each data point represent the data itself.
		"""

		return 14

	@property
	def value_range(self):
		"""
		The range of values possible for each data point.
		"""

		# The sent values are unsigned.
		return (0, 2 ** self.data_bits - 1)

	@property
	@quantity_wrapped('Hz')
	def sampling_rate(self):
		"""
		The sampling rate of the AWG in Hz.
		"""

		return float(self.ask('source1:frequency?'))

	@sampling_rate.setter
	@quantity_unwrapped('Hz')
	def sampling_rate(self, value):
		if value < 1e7 or value > 1.2e9:
			raise ValueError('Sampling rate must be between 1e7 Hz and 1.2e9 Hz, not {0:n} Hz'.format(value))

		self.write('source1:frequency {0:E}'.format(value))

	@property
	def run_mode(self):
		"""
		The run mode of the AWG. One of: continuous, triggered, gated, sequence.
		"""

		mode = self.ask('awgcontrol:rmode?').lower()

		if mode.startswith('cont'):
			return 'continuous'
		elif mode.startswith('trig'):
			return 'triggered'
		elif mode.startswith('gat'):
			return 'gated'
		elif mode.startswith('seq'):
			return 'sequence'
		else:
			ValueError('Unknown mode: {0}'.format(mode))

	@run_mode.setter
	def run_mode(self, value):
		if value not in self.allowed_run_modes:
			raise ValueError('Invalid run mode: {0}'.format(value))

		self.write('awgcontrol:rmode {0}'.format(value))

	@property
	@Synchronized()
	def waveform_names(self):
		"""
		A list of all waveforms in the AWG.
		"""

		num_waveforms = int(self.ask('wlist:size?'))

		self.multi_command_start()
		# Waveforms on the AWG are numbered from 0.
		for i in xrange(num_waveforms):
			self.ask('wlist:name? {0}'.format(i))
		names = self.multi_command_stop()

		# Names are in quotes.
		return [name[1:-1] for name in names]

	@Synchronized()
	def get_waveform(self, name):
		self.status.append('Getting waveform "{0}"'.format(name))

		try:
			log.debug('Getting waveform "{0}" from device "{1}".'.format(name, self.name))

			block_data = self.ask_raw('wlist:waveform:data? "{0}"'.format(name))
			packed_data = BlockData.from_block_data(block_data)
			waveform_length = len(packed_data) / 2
			data = struct.unpack('<{0}H'.format(waveform_length), packed_data)
			data = [x & 2 ** 14 - 1 for x in data] # Filter out marker data.

			min_value, max_value = self.value_range
			range_diff = max_value - min_value
			data = [2.0 * (x - min_value) / range_diff - 1.0 for x in data]

			log.debug('Got waveform "{0}" from device "{1}": {2!r}'.format(name, self.name, data))

			return data
		finally:
			self.status.pop()

	@Synchronized()
	def create_waveform(self, name, data, markers=None):
		"""
		Create a new waveform on the AWG.

		The waveform data should be on [-1, 1].
		"""

		self.status.append('Creating waveform "{0}"'.format(name))

		try:
			log.debug('Creating waveform "{0}" on device "{1}" with data: {2!r}'.format(name, self.name, data))

			min_value, max_value = self.value_range
			range_diff = max_value - min_value
			data = [min_value + int(range_diff * (x + 1.0) / 2.0) for x in data]

			waveform_length = len(data)
			self.write('wlist:waveform:new "{0}", {1}, integer'.format(name, waveform_length))

			if markers:
				# The markers are in the top 2 bits.
				for marker_num, marker_bit in zip([1, 2], [1 << 14, 1 << 15]):
					try:
						for i, marker_datum in enumerate(markers[marker_num]):
							if marker_datum:
								data[i] += marker_bit
						log.debug('Added marker {0} to waveform "{1}" device "{1}": {2!r}'.format(marker_num,
								name, self.name, markers[marker_num]))
					except KeyError:
						pass

				extra_markers = set(markers) - set([1, 2])
				for extra in extra_markers:
					log.warning('Marker {0} ignored: {1!r}'.format(extra, markers[extra]))

			# Always 16-bit, unsigned, little-endian.
			packed_data = struct.pack('<{0}H'.format(waveform_length), *data)
			block_data = BlockData.to_block_data(packed_data)

			log.debug('Sending packed block waveform data for "{0}" on device "{1!r}": {2}'.format(name,
					self.name, block_data))

			self.write('wlist:waveform:data "{0}", {1}'.format(name, block_data))
		finally:
			self.status.pop()

	def delete_waveform(self, name):
		"""
		Remove a waveform on the AWG.
		"""

		if name not in self.waveform_names:
			raise ValueError('No such waveform "{0}"'.format(name))

		self.write('wlist:waveform:delete "{0}"'.format(name))

	@property
	def enabled(self):
		"""
		The continuous run state (on/off) of the AWG.
		"""

		state = self.ask('awgcontrol:rstate?')

		if state == '0':
			return False
		elif state in ['1', '2']:
			# Either on or waiting for trigger.
			return True
		else:
			raise ValueError('State "{0}" not implemented.'.format(state))

	@enabled.setter
	def enabled(self, v):
		if v:
			log.debug('Enabling "{0}".'.format(self.name))

			self.write('awgcontrol:run')
		else:
			log.debug('Disabling "{0}".'.format(self.name))

			self.write('awgcontrol:stop')

	@property
	def waiting_for_trigger(self):
		"""
		Whether the AWG is waiting for a trigger.
		"""

		return '1' == self.ask('awgcontrol:rstate?')

	def trigger(self):
		"""
		Force a trigger event.
		"""

		self.write('*trg')

	def clear_channels(self):
		"""
		Delete all waveforms from all channels.
		"""

		for channel in self.channels[1:]:
			del channel.waveform_name


name = 'AWG5014B'
implementation = AWG5014B
