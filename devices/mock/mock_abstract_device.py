import logging

from devices.abstract_device import AbstractDevice

"""
Mock hardware device.
"""


log = logging.getLogger(__name__)


class MockAbstractDevice(AbstractDevice):
	"""
	A class for controlling fake devices.
	"""

	output = None

	def __init__(self, *args, **kwargs):
		"""
		Connect to a device, always successfully.
		"""

		log.info('Creating mock device.')

		self.name = 'AbstractDevice'
		self.mock_state = {}

	def write(self, message, result=None, done=False):
		"""
		Act on what is being written.
		"""

		log.debug('Writing to device: {0}'.format(message))

		if not done:
			if message == '*idn?':
				result = self.name
				done = True

		if not done:
			raise NotImplementedError('Cannot understand message: {0}'.format(message))

		if result is None:
			self.output = None
		else:
			self.output = str(result) + '\n'

	def read_raw(self, **kwargs):
		"""
		Return the result of the last write operation.
		"""

		log.debug('Read from device: {0}'.format(self.output))

		return self.output


if __name__ == '__main__':
	import unittest

	from tests import test_mock_abstract_device as my_tests

	unittest.main(module=my_tests)
