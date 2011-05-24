import logging
import struct

from devices.abstract_device import BlockData
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


class MockMarker(object):
	"""
	A mock marker for a mock channel.
	"""

	def __init__(self):
		self.delay = 0.0 # s
		self.low = 0.0 # V
		self.high = 1.0 # V


class MockChannel(object):
	"""
	A mock channel for a mock AWG.
	"""

	def __init__(self):
		self.enabled = False
		self.waveform_name = ''
		self.voltage = 1.0

		self.markers = [None] # There is no marker 0.
		for _ in xrange(1, 3):
			self.markers.append(MockMarker())


class MockAWG5014B(MockAbstractDevice, AWG5014B):
	"""
	Mock interface for Tektronix AWG5014B AWG.
	"""

	def __reset(self):
		"""
		Reset to a known blank state.
		"""

		self.mock_state['run_mode'] = 'continuous'
		self.mock_state['run_state'] = '0'
		self.mock_state['frequency'] = 1.2e9 # Hz

		self.mock_state['wlist'] = []
		self.mock_state['wlist'].append(Waveform('"predefined waveform"', 5))
		self.mock_state['wlist'][0].data = list(xrange(5))

		self.mock_state['channels'] = [None] # There is no channel 0.
		for _ in xrange(1, 5):
			self.mock_state['channels'].append(MockChannel())

	def __init__(self, *args, **kwargs):
		"""
		Pretend to connect to the AWG, but do initialize with some values.
		"""

		MockAbstractDevice.__init__(self, *args, **kwargs)

		self.name = 'AWG5014B'

		AWG5014B.setup(self)

		self.__reset()

	def find_wave(self, name):
		"""
		Find a Waveform object by name.
		"""

		for wave in self.mock_state['wlist']:
			if wave.name == name:
				return wave

	def write(self, message, result=None, done=False):
		if not done:
			if message == '*rst':
				self.__reset()
				done = True
			elif message == '*trg':
				done = True
			elif message.startswith('awgcontrol:'):
				submsg = message[11:]

				if submsg == 'run':
					if self.mock_state['run_mode'] in ['triggered', 'gated']:
						self.mock_state['run_state'] = '1'
					else:
						self.mock_state['run_state'] = '2'
					done = True
				elif submsg == 'stop':
					self.mock_state['run_state'] = '0'
					done = True
				elif submsg == 'rstate?':
					result = self.mock_state['run_state']
					done = True
				elif submsg.startswith('rmode'):
					if submsg[5] == '?':
						result = self.mock_state['run_mode']
						done = True
					else:
						mode = submsg.split(None, 1)[1]
						self.mock_state['run_mode'] = mode

						if self.mock_state['run_state'] != '0':
							if mode in ['triggered', 'gated']:
								self.mock_state['run_state'] = '1'
							else:
								self.mock_state['run_state'] = '2'
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
					if submsg[13] == '?':
						name = submsg[15:]

						wave = self.find_wave(name)

						data = wave.data
						data = [datum + marker * 2 ** 14 for (datum, marker) in zip(data, wave.marker1)]
						data = [datum + marker * 2 ** 15 for (datum, marker) in zip(data, wave.marker2)]

						waveform_length = len(data)
						packed_data = struct.pack('<{0}H'.format(waveform_length), *data)
						result = BlockData.to_block_data(packed_data)
					else:
						name, block_data = submsg[14:].split(', ', 1)
						packed_data = BlockData.from_block_data(block_data)
						waveform_length = len(packed_data) / 2
						data = struct.unpack('<{0}H'.format(waveform_length), packed_data)

						wave = self.find_wave(name)
						wave.data = [x & 2 ** 14 - 1 for x in data]
						wave.marker1 = [1 if x & 2 ** 14 else 0 for x in data]
						wave.marker2 = [1 if x & 2 ** 15 else 0 for x in data]

					done = True
			elif message.startswith('source'):
				source = int(message[6])
				channel = self.mock_state['channels'][source]

				submsg = message[8:]

				if submsg.startswith('waveform'):
					if submsg[8] == '?':
						result = channel.waveform_name
					else:
						name = submsg.split(None, 1)[1]
						channel.waveform_name = name
						if name == '""':
							channel.enabled = False
					done = True
				elif submsg.startswith('frequency'):
					if submsg[9] == '?':
						result = self.mock_state['frequency']
					else:
						frequency = submsg.split(None, 1)[1]
						self.mock_state['frequency'] = float(frequency)
					done = True
				elif submsg.startswith('voltage'):
					if submsg[7] == '?':
						result = channel.voltage
					else:
						voltage = submsg.split(None, 1)[1]
						channel.voltage = float(voltage)
					done = True
				elif submsg.startswith('marker'):
					marker_num = int(submsg[6])
					marker = channel.markers[marker_num]

					if submsg[8:].startswith('delay'):
						if submsg[13] == '?':
							result = marker.delay
						else:
							marker.delay = float(submsg[14:])
						done = True
					elif submsg[8:].startswith('voltage:high'):
						if submsg[20] == '?':
							result = marker.high
						else:
							marker.high = float(submsg[21:])
						done = True
					elif submsg[8:].startswith('voltage:low'):
						if submsg[19] == '?':
							result = marker.low
						else:
							marker.low = float(submsg[20:])
						done = True
			elif message.startswith('output'):
				output = int(message[6])
				channel = self.mock_state['channels'][output]

				submsg = message[8:]

				if submsg.startswith('state'):
					if submsg[5] == '?':
						result = '1' if channel.enabled else '0'
					else:
						state = submsg.split(None, 1)[1]
						channel.enabled = (state == '1')
					done = True

		MockAbstractDevice.write(self, message, result, done)


if __name__ == '__main__':
	import unittest

	from tests import test_mock_awg5014b as my_tests

	unittest.main(module=my_tests)
