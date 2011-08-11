from nose.tools import eq_
from unittest import main

from spacq.interface.units import Quantity
from spacq.tests.tool.box import DeviceServerTestCase

from ... import smf100a


class SMF100ATest(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=smf100a.SMF100A, model_name='SMF100A')

	def testScenario(self):
		"""
		Change the settings.
		"""

		sg = self.obtain_device()
		sg.reset()

		assert not sg.enabled
		eq_(sg.frequency.value, 1e9)
		eq_(sg.power, -30.0)

		sg.frequency = Quantity(5.6789, 'GHz')
		sg.power = -2.0
		sg.enabled = True

		assert sg.enabled
		eq_(sg.frequency.value, 5.6789e9)
		eq_(sg.power, -2.0)


if __name__ == '__main__':
	main()
