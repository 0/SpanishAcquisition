from nose.tools import eq_
import unittest

from devices.mock import mock_abstract_device


class MockAbstractDeviceTest(unittest.TestCase):
	def testInit(self):
		"""
		Should always succeed.
		"""

		mock_abstract_device.MockAbstractDevice()
		mock_abstract_device.MockAbstractDevice(ip_address='1234')
		mock_abstract_device.MockAbstractDevice(board=12345, pad=67890)

	def testAskRaw(self):
		"""
		Converse briefly with a fake device.
		"""

		dev = mock_abstract_device.MockAbstractDevice()

		msg = dev.ask_raw('*idn?')
		eq_(msg, 'AbstractDevice\n')


if __name__ == '__main__':
	unittest.main()
