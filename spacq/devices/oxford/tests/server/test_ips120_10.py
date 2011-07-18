from nose.tools import eq_
from time import time
import unittest

from spacq.tests.tool.box import DeviceServerTestCase

from ... import ips120_10


class IPS120_10Test(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=ips120_10.IPS120_10, model_name='IPS120_10')

	def testScenario(self):
		"""
		Change the sweep rate and output field.

		Note: Verification should also be done manually based on the output.
		"""

		ips = self.obtain_device()
		ips.perma_hot = True

		# Turn off the heater for now.
		ips.heater_on = False
		assert not ips.heater_on

		# Sweep slowly.
		ips.sweep_rate = 0.05

		start_time = time()
		ips.field = 0.005
		elapsed_time = time() - start_time

		eq_(ips.field, 0.005)

		expected_time = 60 * (0.005 - 0.0) / 0.05
		assert elapsed_time >= expected_time, 'Took {0} s, expected at least {1} s.'.format(elapsed_time, expected_time)

		# Make sure it stayed on.
		assert ips.heater_on

		# Turn it off next time.
		ips.perma_hot = False

		# Sweep quickly.
		ips.sweep_rate = 0.5

		start_time = time()
		ips.field = -0.015
		elapsed_time = time() - start_time

		eq_(ips.field, -0.015)

		expected_time = 60 * (-0.015 - 0.005) / 0.5
		assert elapsed_time >= expected_time, 'Took {0} s, expected at least {1} s.'.format(elapsed_time, expected_time)

		# Make sure it turned off.
		assert not ips.heater_on

		ips.perma_hot = True

		# Reset back to zero.
		start_time = time()
		ips.field = 0.0
		elapsed_time = time() - start_time

		eq_(ips.field, 0.0)

		expected_time = 60 * (0.0 - (-0.015)) / 0.5
		assert elapsed_time >= expected_time, 'Took {0} s, expected at least {1} s.'.format(elapsed_time, expected_time)


if __name__ == '__main__':
	unittest.main()
