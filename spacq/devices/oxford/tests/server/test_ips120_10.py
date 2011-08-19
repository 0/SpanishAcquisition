from nose.tools import eq_
from time import time
from unittest import main

from spacq.interface.units import Quantity
from spacq.tests.tool.box import DeviceServerTestCase

from ... import ips120_10


class IPS120_10Test(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=ips120_10.IPS120_10,
				manufacturer='Oxford Instruments', model='IPS120-10')

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

		start_field = ips.field

		# Sweep slowly.
		ips.sweep_rate = Quantity(0.1 / 60, 'T.s-1')

		field1 = Quantity(0.005, 'T')

		start_time = time()
		ips.field = field1
		elapsed_time = time() - start_time

		eq_(ips.set_point, field1)
		eq_(ips.field, field1)

		expected_time = 60 * abs(field1 - start_field).value / 0.1
		assert elapsed_time >= expected_time, 'Took {0} s, expected at least {1} s.'.format(elapsed_time, expected_time)

		# Make sure it stayed on.
		assert ips.heater_on

		# Turn it off next time.
		ips.perma_hot = False

		# Sweep quickly.
		ips.sweep_rate = Quantity(0.5 / 60, 'T.s-1')

		field2 = Quantity(-0.015, 'T')

		start_time = time()
		ips.field = field2
		elapsed_time = time() - start_time

		eq_(ips.field, field2)

		expected_time = 60 * abs(field2 - field1).value / 0.5
		assert elapsed_time >= expected_time, 'Took {0} s, expected at least {1} s.'.format(elapsed_time, expected_time)

		# Make sure it turned off.
		assert not ips.heater_on

		ips.perma_hot = True

		# Reset back to zero.
		field3 = Quantity(0.0, 'T')

		start_time = time()
		ips.field = field3
		elapsed_time = time() - start_time

		eq_(ips.field, field3)

		expected_time = 60 * abs(field3 - field2).value / 0.5
		assert elapsed_time >= expected_time, 'Took {0} s, expected at least {1} s.'.format(elapsed_time, expected_time)


if __name__ == '__main__':
	main()
