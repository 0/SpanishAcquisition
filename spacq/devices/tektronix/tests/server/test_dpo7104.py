import logging
log = logging.getLogger(__name__)

from nose.tools import eq_
from unittest import main

from spacq.interface.units import Quantity
from spacq.tests.tool.box import DeviceServerTestCase

from ... import dpo7104


class DPO7104Test(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=dpo7104.DPO7104,
				manufacturer='Tektronix', model='DPO7104')

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

		dpo.channels[1].scale = dpo.channels[4].scale = Quantity(500, 'mV')
		dpo.channels[1].offset = dpo.channels[4].offset = Quantity(1, 'V')

		# Many records.
		dpo.time_scale = Quantity(100, 'ns')
		dpo.sample_rate = Quantity(40, 'GHz')
		eq_(dpo.record_length, 4e3)

		dpo.acquire()
		ws.append(dpo.channels[1].waveform)
		ws.append(dpo.channels[4].waveform)

		eq_(dpo.time_scale.value, 1e-7)
		eq_(dpo.sample_rate.value, 4e10)

		eq_(len(ws[0]), 4e3)
		eq_(len(ws[1]), 4e3)

		# Long sample.
		dpo.acquisition_mode = 'sample'

		dpo.time_scale = Quantity(10, 's')
		dpo.sample_rate = Quantity(0.1, 'kHz')
		eq_(dpo.record_length, 1e3)

		dpo.acquire()
		ws.append(dpo.channels[1].waveform)
		ws.append(dpo.channels[4].waveform)

		eq_(dpo.time_scale.value, 1e1)
		eq_(dpo.sample_rate.value, 1e2)
		eq_(len(ws[2]), 1e3)
		eq_(len(ws[3]), 1e3)

		# Check the channels.
		assert     dpo.channels[1].enabled
		assert not dpo.channels[2].enabled
		assert not dpo.channels[3].enabled
		assert     dpo.channels[4].enabled
		# Check the data.
		assert all(x >= -1.5 and x <= 3.5 for w in ws for _, x in w)


if __name__ == '__main__':
	main()
