from ...mock.mock_abstract_device import MockAbstractDevice
from ...tools import BlockData
from ..dpo7104 import DPO7104

"""
Mock Tektronix DPO7104 Digital Phosphor Oscilloscope

Control a fake DPO's settings and input waveforms.
"""


class MockDPO7104(MockAbstractDevice, DPO7104):
	"""
	Mock interface for Tektronix DPO7104 DPO.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = DPO7104

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['stopafter'] = 'runstop'
		self.mock_state['acquire_state'] = 'run'

		self.mock_state['samplerate'] = 1e10 # Hz
		self.mock_state['horizontal_scale'] = 1e-8 # s

		self.mock_state['waveform_bytes'] = 2

		self.mock_state['data_start'] = 1
		self.mock_state['data_stop'] = self.record_length

	@property
	def record_length(self):
		return int(10 * self.mock_state['samplerate'] * self.mock_state['horizontal_scale'])

	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)

			if cmd[0] == 'autoset':
				if args == 'execute':
					done = True
			elif cmd[0] == 'acquire':
				if cmd[1] == 'stopafter':
					if query:
						result = self.mock_state['stopafter']
					else:
						self.mock_state['stopafter'] = args
					done = True
				elif cmd[1] == 'state':
					if query:
						result = self.mock_state['acquire_state']
					else:
						self.mock_state['acquire_state'] = args
					done = True
			elif cmd[0] == 'horizontal':
				if cmd[1] == 'mode':
					if cmd[2] == 'samplerate':
						if query:
							result = self.mock_state['samplerate']
						else:
							self.mock_state['samplerate'] = float(args)
						done = True
					elif cmd[2] == 'scale':
						if query:
							result = self.mock_state['horizontal_scale']
						else:
							self.mock_state['horizontal_scale'] = float(args)
						done = True
					elif cmd[2] == 'recordlength' and query:
						result = self.record_length
						done = True
			elif cmd[0] == 'data':
				if cmd[1] == 'start':
					if query:
						result = self.mock_state['data_start']
					else:
						self.mock_state['data_start'] = int(args)
					done = True
				elif cmd[1] == 'stop':
					if query:
						result = self.mock_state['data_stop']
					else:
						self.mock_state['data_stop'] = int(args)
					done = True
			elif cmd[0] == 'curve' and query:
				result = BlockData.to_block_data('x' * self.record_length * self.mock_state['waveform_bytes'])
				done = True
			elif cmd[0] == 'wfmoutpre':
				if cmd[1] == 'byt_nr':
					if query:
						result = self.mock_state['waveform_bytes']
					else:
						self.mock_state['waveform_bytes'] = int(args)
					done = True

		MockAbstractDevice.write(self, message, result, done)


name = 'DPO7104'
implementation = MockDPO7104
