from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from devices import abstract_device


# TODO: Move this to a configuration file.
REAL_DEVICE = {'ip_address': '192.168.0.10'}
#REAL_DEVICE = {'board': 0, 'pad': 5}


class AbstractDeviceTest(unittest.TestCase):
	def testInitNoAddress(self):
		"""
		No address specified.
		"""

		try:
			dev = abstract_device.AbstractDevice()
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

	def testInitNotFoundIP(self):
		"""
		Invalid or non-existent IP address.
		"""

		try:
			dev = abstract_device.AbstractDevice(ip_address='1234')
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

		try:
			# Address within TEST-NET-1 is not likely to exist.
			dev = abstract_device.AbstractDevice(ip_address='192.0.2.123')
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'


	def testInitNotFoundGPIB(self):
		"""
		Invalid or non-existent GPIB address.

		Note: There doesn't seem to be a way of disabling the error output from libgpib.
		"""

		try:
			# Valid PADs are on [0, 30] (5 bits; 31 is reserved).
			dev = abstract_device.AbstractDevice(board=0, pad=2000)
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

		try:
			# Assuming that board number 15 is not used.
			dev = abstract_device.AbstractDevice(board=15, pad=0)
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

	def testAskRaw(self):
		"""
		Converse briefly with a real device.
		"""

		try:
			dev = abstract_device.AbstractDevice(**REAL_DEVICE)
		except:
			raise SkipTest('Could not connect to device.')

		msg = dev.ask_raw('*idn?')
		eq_(msg[-1], '\n')


if __name__ == '__main__':
	unittest.main()
