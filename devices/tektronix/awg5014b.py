import logging
import struct

from devices.abstract_device import AbstractDevice, BlockData

"""
Tektronix AWG5014B Arbitrary Waveform Generator

Control the AWG's settings and output waveforms.
"""


log = logging.getLogger(__name__)


class Channel(object):
	"""
	Output channel of the AWG.
	"""

	def __init__(self, device, channel, *args, **kwargs):
		object.__init__(self, *args, **kwargs)

		self.device = device
		self.channel = channel

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


class AWG5014B(AbstractDevice):
	"""
	Interface for Tektronix AWG5014B AWG.
	"""

	def setup(self):
		self.channels = [None] # There is no channel 0.
		for chan in xrange(1, 5):
			self.channels.append(Channel(self, chan))

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')
		self.enabled = False

	def __init__(self, *args, **kwargs):
		"""
		Connect to the AWG and initialize with some values.
		"""

		AbstractDevice.__init__(self, *args, **kwargs)

		self.setup()

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
	def waveform_names(self):
		"""
		A list of all waveforms in the AWG.
		"""

		num_waveforms = int(self.ask('wlist:size?'))
		result = []

		# Waveforms on the AWG are numbered from 0.
		for i in xrange(num_waveforms):
			name = self.ask('wlist:name? {0}'.format(i))
			# Names are in quotes.
			result.append(name[1:-1])

		return result

	def get_waveform(self, name):
		log.debug('Getting waveform "{0}" from device "{1}".'.format(name, self.name))

		block_data = self.ask_raw('wlist:waveform:data? "{0}"'.format(name))
		packed_data = BlockData.from_block_data(block_data)
		waveform_length = len(packed_data) / 2
		data = struct.unpack('<{0}H'.format(waveform_length), packed_data)
		data = [x & 2 ** 14 - 1 for x in data] # Filter out marker data.

		log.debug('Got waveform "{0}" from device "{1}": {2}'.format(name, self.name, data))

		return list(data)

	def create_waveform(self, name, data, markers=None):
		"""
		Create a new waveform on the AWG.
		"""

		log.debug('Creating waveform "{0}" on device "{1}" with data: {2}'.format(name, self.name, data))

		data = list(data)
		waveform_length = len(data)
		self.write('wlist:waveform:new "{0}", {1}, integer'.format(name, waveform_length))

		if markers:
			# The markers are in the top 2 bits.
			for marker_num, marker_bit in zip([1, 2], [1 << 14, 1 << 15]):
				try:
					for i, marker_datum in enumerate(markers[marker_num]):
						if marker_datum:
							data[i] += marker_bit
					log.debug('Added marker {0} to waveform "{1}" device "{1}": {2}'.format(marker_num, name, self.name, markers[marker_num]))
				except KeyError:
					log.warning('Marker {0} ignored: {1}'.format(marker_num, markers[marker_num]))

		# Always 16-bit, unsigned, little-endian.
		packed_data = struct.pack('<{0}H'.format(waveform_length), *data)
		block_data = BlockData.to_block_data(packed_data)

		log.debug('Sending packed block waveform data for "{0}" on device "{1}": {1}'.format(name, self.name, block_data))

		self.write('wlist:waveform:data "{0}", {1}'.format(name, block_data))

	@property
	def enabled(self):
		"""
		The run state (on/off) of the AWG.
		"""

		state = self.ask('awgcontrol:rstate?')

		if state == '0':
			return False
		elif state == '2':
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


if __name__ == '__main__':
	import unittest

	from tests import test_awg5014b as my_tests

	unittest.main(module=my_tests)
