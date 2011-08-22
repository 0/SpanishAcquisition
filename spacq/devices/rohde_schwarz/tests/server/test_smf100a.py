from nose.tools import assert_almost_equal, eq_
from unittest import main

from spacq.interface.units import Quantity
from spacq.tests.tool.box import DeviceServerTestCase

from ... import smf100a


class SMF100ATest(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=smf100a.SMF100A,
				manufacturer='Rohde & Schwarz', model='SMF100A')

	def testScenario(self):
		"""
		Change the settings.
		"""

		sg = self.obtain_device()
		sg.reset()

		sg.write('unit:power v')

		assert not sg.enabled
		eq_(sg.frequency.value, 1e10)
		assert_almost_equal(sg.power.value, 0.007, 3)

		sg.frequency = Quantity(5.6789, 'GHz')
		sg.power = Quantity(100, 'mV')
		sg.enabled = True

		assert sg.enabled
		eq_(sg.frequency.value, 5.6789e9)
		eq_(sg.power.value, 0.1)

		sg.enabled = False
		assert not sg.enabled

	def testIllegal(self):
		"""
		These values aren't allowed.
		"""

		sg = self.obtain_device()

		sg.write('unit:power v')

		try:
			sg.power = Quantity(9.001, 'V')
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError'

		try:
			sg.frequency = Quantity(0, 'Hz')
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError'


if __name__ == '__main__':
	main()
