import struct

from ...mock.mock_abstract_device import MockAbstractDevice
from ...tools import BlockData
from ..awg5014b import AWG5014B

"""
Mock Tektronix AWG5014B Arbitrary Waveform Generator

Control a fake AWG's settings and output waveforms.
"""


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

	def __init__(self, *args, **kwargs):
		"""
		Pretend to connect to the AWG, but do initialize with some values.
		"""

		self.mocking = AWG5014B

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['run_mode'] = 'continuous'
		self.mock_state['run_state'] = '0'
		self.mock_state['frequency'] = 1.2e9 # Hz

		self.mock_state['wlist'] = []
		self.mock_state['wlist'].append(Waveform('"predefined waveform"', 5))
		self.mock_state['wlist'][0].data = list(xrange(5))

		self.mock_state['channels'] = [None] # There is no channel 0.
		for _ in xrange(1, 5):
			self.mock_state['channels'].append(MockChannel())

	def find_wave(self, name):
		"""
		Find a Waveform object by name.
		"""

		for wave in self.mock_state['wlist']:
			if wave.name == name:
				return wave

	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)

			if cmd[0] == '*trg':
				done = True
			elif cmd[0] == 'awgcontrol':
				if cmd[1] == 'run':
					if self.mock_state['run_mode'] in ['triggered', 'gated']:
						self.mock_state['run_state'] = '1'
					else:
						self.mock_state['run_state'] = '2'
					done = True
				elif cmd[1] == 'stop':
					self.mock_state['run_state'] = '0'
					done = True
				elif cmd[1] == 'rstate' and query:
					result = self.mock_state['run_state']
					done = True
				elif cmd[1] == 'rmode':
					if query:
						result = self.mock_state['run_mode']
						done = True
					else:
						mode = args
						self.mock_state['run_mode'] = mode

						if self.mock_state['run_state'] != '0':
							if mode in ['triggered', 'gated']:
								self.mock_state['run_state'] = '1'
							else:
								self.mock_state['run_state'] = '2'
						done = True
			elif cmd[0] == 'wlist':
				if cmd[1] == 'size' and query:
					result = str(len(self.mock_state['wlist']))
					done = True
				elif cmd[1] == 'name' and query:
					num = args
					name = self.mock_state['wlist'][int(num)].name
					result = '"{0}"'.format(name[1:-1])
					done = True
				elif cmd[1] == 'waveform' and cmd[2] == 'new':
					name, length, kind = [arg.strip() for arg in args.split(',')]
					length = int(length)

					if kind == 'integer':
						self.mock_state['wlist'].append(Waveform(name, length))
						done = True
				elif cmd[1] == 'waveform' and cmd[2] == 'data':
					if query:
						name = args

						wave = self.find_wave(name)

						data = wave.data
						data = [datum + marker * 2 ** 14 for (datum, marker) in zip(data, wave.marker1)]
						data = [datum + marker * 2 ** 15 for (datum, marker) in zip(data, wave.marker2)]

						waveform_length = len(data)
						packed_data = struct.pack('<{0}H'.format(waveform_length), *data)
						result = BlockData.to_block_data(packed_data)
					else:
						name, block_data = args.split(',', 1)
						name = name.strip()
						block_data = block_data.lstrip()
						packed_data = BlockData.from_block_data(block_data)
						waveform_length = len(packed_data) / 2
						data = struct.unpack('<{0}H'.format(waveform_length), packed_data)

						wave = self.find_wave(name)
						wave.data = [x & 2 ** 14 - 1 for x in data]
						wave.marker1 = [1 if x & 2 ** 14 else 0 for x in data]
						wave.marker2 = [1 if x & 2 ** 15 else 0 for x in data]

					done = True
				elif cmd[1] == 'waveform' and cmd[2] == 'delete':
					self.mock_state['wlist'].remove(self.find_wave(args))
					done = True
			elif cmd[0].startswith('source'):
				source = int(cmd[0][6])
				channel = self.mock_state['channels'][source]

				if cmd[1] == 'waveform':
					if query:
						result = channel.waveform_name
					else:
						name = args
						channel.waveform_name = name
						if name == '""':
							channel.enabled = False
					done = True
				elif cmd[1] == 'frequency':
					if query:
						result = self.mock_state['frequency']
					else:
						frequency = args
						self.mock_state['frequency'] = float(frequency)
					done = True
				elif cmd[1] == 'voltage':
					if query:
						result = channel.voltage
					else:
						voltage = args
						channel.voltage = float(voltage)
					done = True
				elif cmd[1].startswith('marker'):
					marker_num = int(cmd[1][6])
					marker = channel.markers[marker_num]

					if cmd[2] == 'delay':
						if query:
							result = marker.delay
						else:
							delay = args
							marker.delay = float(delay)
						done = True
					elif cmd[2] == 'voltage' and cmd[3] == 'high':
						if query:
							result = marker.high
						else:
							voltage = args
							marker.high = float(voltage)
						done = True
					elif cmd[2] == 'voltage' and cmd[3] == 'low':
						if query:
							result = marker.low
						else:
							voltage = args
							marker.low = float(voltage)
						done = True
			elif cmd[0].startswith('output'):
				output = int(cmd[0][6])
				channel = self.mock_state['channels'][output]

				if cmd[1] == 'state':
					if query:
						result = str(int(channel.enabled))
					else:
						state = args
						channel.enabled = (state == '1')
					done = True

		MockAbstractDevice.write(self, message, result, done)


name = 'AWG5014B'
implementation = MockAWG5014B
