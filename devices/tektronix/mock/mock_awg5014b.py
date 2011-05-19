import logging
import struct

from devices.mock.mock_abstract_device import MockAbstractDevice
from devices.tektronix.awg5014b import AWG5014B

"""
Mock Tektronix AWG5014B Arbitrary Waveform Generator

Control a fake AWG's settings and output waveforms.
"""


log = logging.getLogger(__name__)


class Waveform(object):
	"""
	Mock waveform.
	"""

	def __init__(self, name, length):
		self.name = name
		self.length = length
		self._data = [0] * length

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, v):
		new_length = len(v)

		if new_length <= self.length:
			self._data[:new_length] = v


class MockChannel(object):
	"""
	A mock channel for a mock AWG.
	"""

	def __init__(self):
		self.enabled = False


class MockAWG5014B(MockAbstractDevice, AWG5014B):
	"""
	Mock interface for Tektronix AWG5014B AWG.
	"""

	def __init__(self, *args, **kwargs):
		"""
		Pretend to connect to the AWG, but do initialize with some values.
		"""

		MockAbstractDevice.__init__(self, *args, **kwargs)

		self.name = 'AWG5014B'

		AWG5014B.setup(self)

		self.mock_state['enabled'] = False

		self.mock_state['wlist'] = []
		self.mock_state['wlist'].append(Waveform('"predefined waveform"', 5))
		self.mock_state['wlist'][0].data = list(xrange(5))

		self.mock_state['channels'] = [None] # There is no channel 0.
		for ch in xrange(1, 5):
			self.mock_state['channels'].append(MockChannel())

	def find_wave(self, name):
		for wave in self.mock_state['wlist']:
			if wave.name == name:
				return wave

	def write(self, message, result=None, done=False):
		if not done:
			if message == '*rst':
				# FIXME: Should reset everything.
				done = True
			elif message.startswith('awgcontrol:'):
				submsg = message[11:]

				if submsg == 'run':
					self.mock_state['enabled'] = True
					done = True
				elif submsg == 'stop':
					self.mock_state['enabled'] = False
					done = True
				elif submsg == 'rstate?':
					result = '2' if self.mock_state['enabled'] else '0'
					done = True
			elif message.startswith('wlist:'):
				submsg = message[6:]

				if submsg == 'size?':
					result = str(len(self.mock_state['wlist']))
					done = True
				elif submsg.startswith('name?'):
					num = int(submsg.split()[1])
					name = self.mock_state['wlist'][num].name
					result = '"{0}"'.format(name[1:-1])
					done = True
				elif submsg.startswith('waveform:new'):
					name, length, type = submsg[13:].split(', ')
					length = int(length)

					if type == 'integer':
						self.mock_state['wlist'].append(Waveform(name, length))
						done = True
				elif submsg.startswith('waveform:data'):
					name, data = submsg[14:].split(', ', 1)

					self.find_wave(name).data = data

					done = True
			elif message.startswith('source'):
				source = int(message[6])
				channel = self.mock_state['channels'][source]

				submsg = message[8:]

				if submsg.startswith('waveform'):
					if submsg[8] == '?':
						result = channel.waveform_name
						done = True
					else:
						name = submsg.split(None, 1)[1]
						channel.waveform_name = name
						done = True
			elif message.startswith('output'):
				output = int(message[6])
				channel = self.mock_state['channels'][output]

				submsg = message[8:]

				if submsg.startswith('state'):
					if submsg[5] == '?':
						result = '1' if channel.enabled else '0'
						done = True
					else:
						state = submsg.split(None, 1)[1]
						channel.enabled = (state == '1')
						done = True

		MockAbstractDevice.write(self, message, result, done)


if __name__ == '__main__':
	import unittest

	from tests import test_mock_awg5014b as my_tests

	unittest.main(module=my_tests)
