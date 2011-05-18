import unittest

from .. import abstract_device


class AbstractDeviceTest(unittest.TestCase):
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


if __name__ == '__main__':
	unittest.main()
