from ...mock.mock_abstract_device import MockAbstractDevice
from ..smf100a import SMF100A

"""
Mock SMF100A signal generator.
"""


class MockSMF100A(MockAbstractDevice, SMF100A):
	"""
	Mock interface for the R&S SMF100A.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = SMF100A

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['enabled'] = 0
		self.mock_state['power'] = 0.007 # V
		self.mock_state['frequency'] = 1e10 # Hz

	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)

			if cmd[0] == 'output':
				if cmd[1] == 'state':
					if query:
						result = self.mock_state['enabled']
					else:
						self.mock_state['enabled'] = int(args)
					done = True
			elif cmd[0] == 'source':
				if cmd[1] == 'power' and cmd[2] == 'power':
					if query:
						result = self.mock_state['power']
					else:
						self.mock_state['power'] = float(args)
					done = True
				elif cmd[1] == 'frequency' and cmd[2] == 'cw':
					if query:
						result = self.mock_state['frequency']
					else:
						self.mock_state['frequency'] = float(args)
					done = True
			elif cmd[0] == 'unit':
				done = True

		MockAbstractDevice.write(self, message, result, done)


name = 'SMF100A'
implementation = MockSMF100A
