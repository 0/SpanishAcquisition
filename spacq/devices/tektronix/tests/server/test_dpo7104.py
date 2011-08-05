import logging
log = logging.getLogger(__name__)

from nose.tools import eq_
from unittest import main

from spacq.tests.tool.box import DeviceServerTestCase

from ... import dpo7104


class DPO7104Test(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=dpo7104.DPO7104, model_name='DPO7104')

	def testAcquire(self):
		"""
		Obtain some waveforms.
		"""

		dpo = self.obtain_device()
		dpo.reset()

		dpo.autoset()

		eq_(dpo.stopafter, 'runstop')
		assert dpo.acquiring

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


if __name__ == '__main__':
	main()
