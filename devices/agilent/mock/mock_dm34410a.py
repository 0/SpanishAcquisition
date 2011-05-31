from devices.agilent.dm34410a import DM34410A
from devices.mock.mock_abstract_device import MockAbstractDevice

"""
Mock Agilent 34410A Digital Multimeter

Control a fake multimeter.
"""


class MockDM34410A(MockAbstractDevice, DM34410A):
	"""
	Mock interface for Agilent 34410A Digital Multimeter.
	"""

	def __reset(self):
		"""
		Reset to a known blank state.
		"""

		pass

	def __init__(self, *args, **kwargs):
		"""
		Pretend to connect to the DM.
		"""

		MockAbstractDevice.__init__(self, *args, **kwargs)

		self.name = 'DM34410A'
		self.__reset()

		DM34410A._setup(self)

	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)

			if cmd[0] == '*rst':
				self.__reset()
				done = True
			elif cmd[0] == 'measure':
				if cmd[1] == 'voltage' and cmd[2] == 'dc' and query:
					result = '+4.27150000E-03'
					done = True

		MockAbstractDevice.write(self, message, result, done)


if __name__ == '__main__':
	import unittest

	from tests import test_mock_awg5014b as my_tests

	unittest.main(module=my_tests)
