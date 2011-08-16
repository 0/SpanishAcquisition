from nose.tools import assert_raises, eq_
from pickle import dumps, loads
from unittest import main

from spacq.tests.tool.box import DeviceServerTestCase
from ...abstract_device import AbstractDevice

from ... import config


class DeviceConfigTest(DeviceServerTestCase):
	def obtain_device(self):
		"""
		Get a real device with which to test.
		"""

		return DeviceServerTestCase.obtain_device(self)

	def populate_config(self, cfg, addr):
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

		dev = self.obtain_device()

		cfg = config.DeviceConfig(name='Test')
		self.populate_config(cfg, dev['address'])

		cfg.manufacturer = dev['manufacturer']
		cfg.model = dev['model']

		cfg.connect()

		assert isinstance(cfg.device, AbstractDevice)

		return cfg

	def testConnectNoImplementation(self):
		"""
		Try to connect without an implementation.
		"""

		dev = self.obtain_device()

		cfg = config.DeviceConfig(name='Test')
		self.populate_config(cfg, dev['address'])

		assert_raises(config.ConnectionError, cfg.connect)

	def testConnectNoAddress(self):
		"""
		Try to connect without an address.
		"""

		dev = self.obtain_device()

		cfg = config.DeviceConfig(name='Test')

		cfg.manufacturer = dev['manufacturer']
		cfg.model = dev['model']

		assert_raises(config.ConnectionError, cfg.connect)

	def testPickle(self):
		"""
		Pickle and unpickle a device config.
		"""

		cfg = self.testConnectSuccessful()

		expected = cfg.__dict__.copy()
		del expected['_device']
		del expected['resources']

		actual = loads(dumps(cfg)).__dict__
		del actual['_device']
		del actual['resources']

		eq_(actual, expected)


if __name__ == '__main__':
	main()
