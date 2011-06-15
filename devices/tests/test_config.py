from nose.plugins.skip import SkipTest
import unittest

from devices.mock.mock_abstract_device import MockAbstractDevice
from testconfig import config as tc

from devices import config


class DeviceConfigTest(unittest.TestCase):
	def __obtain_device(self):
		"""
		Get a mock device with which to test.
		"""

		for name, device in tc['devices'].items():
			if 'mock_implementation_path' in device:
				return device

		raise SkipTest('No suitable device found.')

	def testMockConnect(self):
		"""
		Connect to a mock device.
		"""

		dev = self.__obtain_device()

		cfg = config.DeviceConfig()

		# These values don't matter.
		cfg.address_mode = cfg.address_modes.ethernet
		cfg.ip_address = '127.0.0.1'

		cfg.implementation_path = dev['mock_implementation_path']

		cfg.connect()

		assert isinstance(cfg.device, MockAbstractDevice)
