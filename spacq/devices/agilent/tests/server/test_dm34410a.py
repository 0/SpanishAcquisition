from nose.tools import eq_
from unittest import main

from spacq.tests.tool.box import DeviceServerTestCase

from ... import dm34410a


class DM34410ATest(DeviceServerTestCase):
	def obtain_device(self):
		dev = DeviceServerTestCase.obtain_device(self, impl=dm34410a.DM34410A,
				manufacturer='Agilent', model='34410A')
		dev.reset()

		return dev

	def testAutoZero(self):
		"""
		Test the auto zero setting.
		"""

		dm = self.obtain_device()

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

		dm = self.obtain_device()

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

		dm = self.obtain_device()

		dm.reading.assert_dimensions('V')


if __name__ == '__main__':
	main()
