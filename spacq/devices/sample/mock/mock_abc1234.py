import random

from ...mock.mock_abstract_device import MockAbstractDevice
from ..abc1234 import ABC1234

"""
Mock Sample ABC1234
"""


class MockABC1234(MockAbstractDevice, ABC1234):
	"""
	Mock interface for the Sample ABC1234.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = ABC1234

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['setting'] = 'default value'

	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)

			if cmd[0] == 'some':
				if cmd[1] == 'setting':
					if query:
						result = self.mock_state['setting']
					else:
						self.mock_state['setting'] = args
					done = True
			elif cmd[0] == 'read' and query:
				result = '-1.{0:04d}0000E-02'.format(random.randint(0, 9999))
				done = True

		MockAbstractDevice.write(self, message, result, done)


name = 'ABC1234'
implementation = MockABC1234
