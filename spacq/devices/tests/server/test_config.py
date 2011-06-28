from nose.plugins.skip import SkipTest
import unittest

from testconfig import config as tc
from ...abstract_device import AbstractDevice

from ... import config


class DeviceConfigTest(unittest.TestCase):
	def __obtain_device(self):
		"""
		Get a real device with which to test.
		"""

		for name, device in tc['devices'].items():
			if 'address' in device and 'implementation_path' in device:
				return device

		raise SkipTest('No suitable device found.')

	def __populate_config(self, cfg, addr):
		"""
		Given an address dictionary, populate the DeviceConfig.
		"""

		if 'ip_address' in addr:
			cfg.address_mode = cfg.address_modes.ethernet
			cfg.ip_address = addr['ip_address']
		elif 'gpib_pad' in addr:
			cfg.address_mode = cfg.address_modes.gpib
			try:
				cfg.gpib_board = addr['gpid_board']
			except KeyError:
				pass
			cfg.gpib_pad = addr['gpib_pad']
			try:
				cfg.gpib_sad = addr['gpid_sad']
			except KeyError:
				pass
		elif 'usb_resource' in addr:
			cfg.address_mode = cfg.address_modes.usb
			cfg.usb_resource = addr['usb_resource']

	def testConnectSuccessful(self):
		"""
		Connect normally.
		"""

		dev = self.__obtain_device()

		cfg = config.DeviceConfig()
		self.__populate_config(cfg, dev['address'])

		cfg.implementation_path = dev['implementation_path']

		cfg.connect()

		assert isinstance(cfg.device, AbstractDevice)

	def testConnectNoImplementation(self):
		"""
		Try to connect without an implementation.
		"""

		dev = self.__obtain_device()

		cfg = config.DeviceConfig()
		self.__populate_config(cfg, dev['address'])

		try:
			cfg.connect()
		except config.ConnectionError:
			pass
		else:
			assert False, 'Expected ConnectionError.'

	def testConnectNoAddress(self):
		"""
		Try to connect without an address.
		"""

		dev = self.__obtain_device()

		cfg = config.DeviceConfig()

		cfg.implementation_path = dev['implementation_path']

		try:
			cfg.connect()
		except config.ConnectionError:
			pass
		else:
			assert False, 'Expected ConnectionError.'


if __name__ == '__main__':
	unittest.main()
