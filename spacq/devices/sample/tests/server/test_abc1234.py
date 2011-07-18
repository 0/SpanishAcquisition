from nose.tools import eq_
from numbers import Real
import unittest

from spacq.tests.tool.box import DeviceServerTestCase

from ... import abc1234


class ABC1234Test(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=abc1234.ABC1234, model_name='ABC1234')

	def testSetting(self):
		"""
		Test the setting.
		"""

		dm = self.obtain_device()

		eq_(dm.setting, 'default value')

		dm.setting = 'something else'
		eq_(dm.setting, 'something else')

		try:
			dm.setting = 'another thing'
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

	def testGetValues(self):
		"""
		Obtain some values.
		"""

		dm = self.obtain_device()

		isinstance(dm.reading, Real)


if __name__ == '__main__':
	unittest.main()
