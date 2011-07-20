from nose.tools import assert_raises, eq_
from unittest import main, TestCase

from .. import mock_abstract_device


class MockAbstractDeviceTest(TestCase):
	def testInit(self):
		"""
		Should always succeed.
		"""

		mock_abstract_device.MockAbstractDevice()
		mock_abstract_device.MockAbstractDevice(ip_address='1234')
		mock_abstract_device.MockAbstractDevice(board=12345, pad=67890)

	def testNotImplemented(self):
		"""
		Ensure that an exception is raised for a non-implemented reqest.
		"""

		dev = mock_abstract_device.MockAbstractDevice()

		assert_raises(NotImplementedError, dev.ask_raw, 'This isn\'t right.')

	def testAskRaw(self):
		"""
		Converse briefly with a fake device.
		"""

		dev = mock_abstract_device.MockAbstractDevice()

		msg = dev.ask_raw('*idn?')
		eq_(msg, 'MockAbstractDevice\n')

	def testMulti(self):
		"""
		Ensure that requests for multi-command messages work.
		"""

		dev = mock_abstract_device.MockAbstractDevice()

		expected = ['42', '42', 'MockAbstractDevice']

		dev.multi_command_start()
		dev.ask('system:version?')
		dev.write('*rst')
		dev.write('system:preset')
		dev.ask('system:version?')
		dev.ask('*idn?')
		result = dev.multi_command_stop()

		eq_(result, expected)


if __name__ == '__main__':
	main()
