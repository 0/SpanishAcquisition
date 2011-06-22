from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from ..mock.mock_abstract_device import MockAbstractDevice
from testconfig import config as tc

from .. import config


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

	def testDiffResources(self):
		"""
		Try changing up some resources.
		"""

		cfg1 = config.DeviceConfig()
		cfg2 = config.DeviceConfig()
		eq_(cfg1.diff_resources(cfg2), (set(), set(), set()))

		cfg2.resources['something'] = 'new'
		eq_(cfg1.diff_resources(cfg2), (set(['something']), set(), set()))

		cfg1.resources['for'] = 'now'
		eq_(cfg1.diff_resources(cfg2), (set(['something']), set(), set(['for'])))

		cfg1.resources['something'] = 'now'
		eq_(cfg1.diff_resources(cfg2), (set(), set(['something']), set(['for'])))


if __name__ == '__main__':
	unittest.main()
