import logging
from nose.plugins.skip import SkipTest
from nose.tools import eq_
import numbers
import unittest

from testconfig import config

from devices.agilent import dm34410a


log = logging.getLogger(__name__)


class DM34410ATest(unittest.TestCase):
	def __obtain_device(self):
		"""
		Try to get a handle for a physical device.
		"""

		all_devices = config['devices'].items()
		potential_addresses = [a for (n, a) in all_devices if n.startswith('DM34410A.')]

		for address in potential_addresses:
			try:
				return dm34410a.DM34410A(**address)
			except Exception as e:
				log.info('Could not connect to device at "{0}": {1}'.format(address, e))

		raise SkipTest('Could not connect to device.')

	def testAutoZero(self):
		"""
		Test the auto zero setting.
		"""

		dm = self.__obtain_device()

		dm.auto_zero = 'once'
		eq_(dm.auto_zero, 'off')

		dm.auto_zero = 'on'
		eq_(dm.auto_zero, 'on')

		try:
			dm.auto_zero = 'something else'
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

	def testIntegrationTime(self):
		"""
		Test the integration time setting.
		"""

		dm = self.__obtain_device()

		dm.integration_time = 100
		eq_(dm.integration_time, 100)

		try:
			dm.integration_time = -999
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

	def testGetValues(self):
		"""
		Obtain some values.
		"""

		dm = self.__obtain_device()

		isinstance(dm.reading, numbers.Real)


if __name__ == '__main__':
	unittest.main()
