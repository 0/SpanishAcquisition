import functools
import struct

from devices.abstract_device import AbstractDevice, BlockData

"""
Tektronix AWG5014B Arbitrary Waveform Generator

Control the AWG's settings and output waveforms.
"""


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

		return self.device.ask('source%d:waveform?' % (self.channel))

	@waveform_name.setter
	def waveform_name(self, v):
		self.device.write('source%d:waveform "%s"' % (self.channel, v))

	@waveform_name.deleter
	def waveform_name(self):
		self.waveform_name = ''

	@property
	def enabled(self):
		"""
		The output state (on/off) of the channel.
		"""

		return self.device.ask('output%d:state?' % (self.channel))

	@enabled.setter
	def enabled(self, v):
		self.device.write('output%d:state %d' % (self.channel, v))


class AWG5014B(AbstractDevice):
	"""
	Interface for Tektronix AWG5014B AWG.
	"""

	def __init__(self, *args, **kwargs):
		"""
		Connect to the AWG and initialize with some values.
		"""

		AbstractDevice.__init__(self, *args, **kwargs)

		self.channels = [None] # There is no channel 0.
		for chan in xrange(1, 5):
			self.channels.append(Channel(self, chan))

		self.write('*rst')
		self.enabled = False

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

	def create_waveform(self, name, data):
		"""
		Create a new waveform on the AWG.

		Note: Markers are unsupported.
		"""

		waveform_length = len(data)
		self.write('wlist:waveform:new "%s", %d, integer' % (name, waveform_length))

		# Always 16-bit, unsigned, little-endian.
		packed_data = struct.pack('<%dH' % (waveform_length), *data)

		block_data = BlockData.to_block_data(packed_data)
		self.write('wlist:waveform:data "%s", %s' % (name, block_data))

	@property
	def enabled(self):
		"""
		The run state (on/off) of the AWG.
		"""

		state = self.ask('awgcontrol:rmode?')

		if state == '0':
			return False
		elif state == '2':
			return True
		else:
			raise ValueError('State "%s" not implemented.' % (state))

	@enabled.setter
	def enabled(self, v):
		if v:
			self.write('awgcontrol:run')
		else:
			self.write('awgcontrol:stop')


if __name__ == '__main__':
	import unittest

	from tests import test_awg5014b as my_tests

	unittest.main(module=my_tests)
