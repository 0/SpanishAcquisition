from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from testconfig import config
from tests.tools import AssertHandler

from devices import abstract_device


class BlockDataTest(unittest.TestCase):
	def testToAndFromBlockData(self):
		"""
		Routine conversions.
		"""

		binary_data = ''.join([chr(x) for x in xrange(256)])

		data = [
			('', '#10'),
			(' ', '#11 '),
			('something longer', '#216something longer'),
			('and binary data: ' + binary_data, '#3273and binary data: ' + binary_data)
		]

		for d, b in data:
			eq_(abstract_device.BlockData.to_block_data(d), b)
			eq_(abstract_device.BlockData.from_block_data(b), d)

	def testFromIndefiniteBlockData(self):
		"""
		Indefinite inputs.
		"""

		binary_data = ''.join([chr(x) for x in xrange(256)])

		data = [
			('', '#0\n'),
			(' ', '#0 \n'),
			('something longer', '#0something longer\n'),
			('and binary data: ' + binary_data, '#0and binary data: ' + binary_data + '\n')
		]

		for d, b in data:
			eq_(abstract_device.BlockData.from_block_data(b), d)

	def testFromSlightlyBadData(self):
		"""
		Not valid, but parsable inputs.
		"""

		data = [
			('Too ', '#14Too long.', 'extra data ignored: long.'),
		]

		log = AssertHandler()

		for d, b, msg in data:
			log.flush()
			eq_(abstract_device.BlockData.from_block_data(b), d)
			log.assert_logged('warning', msg)

	def testFromBadBlockData(self):
		"""
		Invalid inputs.
		"""

		data = ['', '123Off to a bad start!', '#', '#0', '#0non-terminated',
				'#X123', '#1', '#29', '#24test', '#44444Too short.']

		for b in data:
			try:
				abstract_device.BlockData.from_block_data(b)
			except abstract_device.BlockDataError:
				pass
			else:
				assert False, 'Expected BlockDataError.'


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
			abstract_device.AbstractDevice(usb_address='NOT::USB::RAW')
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'

		try:
			# Unlikely VID/PID/serial combination.
			abstract_device.AbstractDevice(usb_address='USB::1234::5678::01234567::RAW')
		except abstract_device.DeviceNotFoundError:
			pass
		else:
			assert False, 'Expected DeviceNotFoundError.'


	def testAskRaw(self):
		"""
		Converse briefly with real devices.
		"""

		found_any = False

		# Try all devices to which a connection can be established.
		for name, device in config['devices'].items():
			if not (name.endswith('.eth') or name.endswith('.gpib')):
				continue

			try:
				dev = abstract_device.AbstractDevice(**device)
			except:
				continue

			msg = dev.ask_raw('*idn?')
			eq_(msg[-1], '\n')

			found_any = True

		if not found_any:
			raise SkipTest('Could not connect to any device.')


if __name__ == '__main__':
	unittest.main()
