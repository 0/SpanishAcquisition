import logging
log = logging.getLogger(__name__)

from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from testconfig import config as tc

from ... import dpo7104


class DPO7104Test(unittest.TestCase):
	def __obtain_device(self):
		"""
		Try to get a handle for a physical device.
		"""

		all_devices = tc['devices'].items()
		potential_devices = [a for (n, a) in all_devices if n.startswith('DPO7104.')]

		for device in potential_devices:
			try:
				return dpo7104.DPO7104(**device['address'])
			except Exception as e:
				log.info('Could not connect to device at "{0}": {1}'.format(device['address'], e))

		raise SkipTest('Could not connect to device.')

	def testAcquire(self):
		"""
		Obtain some waveforms.
		"""

		dpo = self.__obtain_device()

		# Many records.
		dpo.horizontal_scale = 1e-7
		dpo.sample_rate = 4e10
		eq_(dpo.record_length, 4e4)

		w1 = dpo.waveform

		eq_(dpo.horizontal_scale, 1e-7)
		eq_(dpo.sample_rate, 4e10)
		eq_(len(w1), 4e4)
		assert all(x >= -1.0 and x <= 1.0 for x in w1)

		# Long sample.
		dpo.horizontal_scale = 1e0
		dpo.sample_rate = 1e2
		eq_(dpo.record_length, 1e3)

		w2 = dpo.waveform

		eq_(dpo.horizontal_scale, 1e0)
		eq_(dpo.sample_rate, 1e2)
		eq_(len(w2), 1e3)
		assert all(x >= -1.0 and x <= 1.0 for x in w2)
