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

		ws = []

		# 1 is enabled by default.
		# 2 and 3 are disabled by default.
		dpo.channels[4].enabled = True

		# Many records.
		dpo.horizontal_scale = 1e-7
		dpo.sample_rate = 4e10
		eq_(dpo.record_length, 4e4)

		dpo.acquire()
		ws.append(dpo.channels[1].waveform)
		ws.append(dpo.channels[4].waveform)

		eq_(dpo.horizontal_scale, 1e-7)
		eq_(dpo.sample_rate, 4e10)

		eq_(len(ws[0]), 4e4)
		eq_(len(ws[1]), 4e4)

		# Long sample.
		dpo.horizontal_scale = 1e0
		dpo.sample_rate = 1e2
		eq_(dpo.record_length, 1e3)

		dpo.acquire()
		ws.append(dpo.channels[1].waveform)
		ws.append(dpo.channels[4].waveform)

		eq_(dpo.horizontal_scale, 1e0)
		eq_(dpo.sample_rate, 1e2)
		eq_(len(ws[2]), 1e3)
		eq_(len(ws[3]), 1e3)

		# Check the channels.
		assert     dpo.channels[1].enabled
		assert not dpo.channels[2].enabled
		assert not dpo.channels[3].enabled
		assert     dpo.channels[4].enabled
		# Check the data.
		assert all(x >= -1.0 and x <= 1.0 for w in ws for x in w)
