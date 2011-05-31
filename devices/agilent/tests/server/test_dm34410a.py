from nose.plugins.skip import SkipTest
import numbers
import unittest

from testconfig import config

from devices.agilent import dm34410a


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
				print e

		raise SkipTest('Could not connect to device.')

	def testGetValues(self):
		"""
		Obtain some values.
		"""

		dm = self.__obtain_device()

		isinstance(dm.dc_voltage, numbers.Real)


if __name__ == '__main__':
	unittest.main()
