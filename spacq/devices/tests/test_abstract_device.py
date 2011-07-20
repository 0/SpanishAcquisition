from nose.tools import eq_
from unittest import main, TestCase

from spacq.interface.resources import Resource

from .. import abstract_device


class AbstractDeviceTest(TestCase):
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
			abstract_device.AbstractDevice(gpib_board=0, gpib_pad=2000)
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

		try:
			# Assuming that board number 15 is not used.
			abstract_device.AbstractDevice(gpib_board=15, gpib_pad=0)
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

	def testFindResource(self):
		"""
		Attempt to find a resource.
		"""

		dev = abstract_device.AbstractDevice(ip_address='192.0.2.123', autoconnect=False)
		subdev1 = abstract_device.AbstractSubdevice(dev)
		subdev2 = abstract_device.AbstractSubdevice(dev)
		subdev3 = abstract_device.AbstractSubdevice(subdev1)
		res1 = Resource(object(), '__class__')
		res2 = Resource(object(), '__str__')
		res3 = Resource(object(), '__doc__')

		dev.subdevices['subdev1'] = subdev1
		dev.resources['res1'] = res1
		dev.subdevices['subdev2'] = subdev2
		subdev1.subdevices['subdev3'] = subdev3
		subdev3.resources['res2'] = res2
		subdev3.resources['res3'] = res3

		# Success.
		found = dev.find_resource(('subdev1', 'subdev3', 'res3'))
		eq_(found.value, object.__doc__)

		# No such resource.
		try:
			dev.find_resource(('subdev1', 'res3'))
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		# No such subdevice.
		try:
			dev.find_resource(('subdev1', 'subdev2', 'res3'))
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		# Nothing to even try.
		try:
			dev.find_resource(())
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'


if __name__ == '__main__':
	main()
