import unittest

from devices import abstract_device


class AbstractDeviceTest(unittest.TestCase):
	def testInitNoAddress(self):
		"""
		No address specified.
		"""

		try:
			abstract_device.AbstractDevice()
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

	def testInitNotFoundIP(self):
		"""
		Invalid or non-existent IP address.
		"""

		try:
			abstract_device.AbstractDevice(ip_address='1234')
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

		try:
			# Address within TEST-NET-1 is not likely to exist.
			abstract_device.AbstractDevice(ip_address='192.0.2.123')
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
			abstract_device.AbstractDevice(board=0, pad=2000)
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

		try:
			# Assuming that board number 15 is not used.
			abstract_device.AbstractDevice(board=15, pad=0)
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

	def testInitNotFoundUSB(self):
		"""
		Invalid or non-existent USB address.
		"""

		try:
			abstract_device.AbstractDevice(usb_resource='NOT::USB::RAW')
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

		try:
			# Unlikely VID/PID/serial combination.
			abstract_device.AbstractDevice(usb_resource='USB::1234::5678::01234567::RAW')
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'


if __name__ == '__main__':
	unittest.main()
