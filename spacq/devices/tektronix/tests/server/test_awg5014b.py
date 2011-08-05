import logging
log = logging.getLogger(__name__)

from nose.tools import eq_
from numpy import linspace
from numpy.testing import assert_array_almost_equal
from unittest import main

from spacq.tests.tool.box import AssertHandler, DeviceServerTestCase

from ... import awg5014b


class AWG5014BTest(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=awg5014b.AWG5014B, model_name='AWG5014B')

	def testMarkerValues(self):
		"""
		Set the various marker values.
		"""

		awg = self.obtain_device()
		awg.reset()

		awg.channels[1].markers[1].delay = 1e-9 # s
		awg.channels[1].markers[1].high = 0.5 # V
		awg.channels[1].markers[2].delay = 0.1e-9 # s
		awg.channels[2].markers[1].low = -0.1 # V

		eq_(awg.channels[1].markers[1].delay, 1e-9)
		eq_(awg.channels[1].markers[2].delay, 0.1e-9)
		eq_(awg.channels[2].markers[1].delay, 0)
		eq_(awg.channels[2].markers[2].delay, 0)

		eq_(awg.channels[1].markers[1].high, 0.5)
		eq_(awg.channels[1].markers[2].high, 1)
		eq_(awg.channels[2].markers[1].high, 1)
		eq_(awg.channels[2].markers[2].high, 1)

		eq_(awg.channels[1].markers[1].low, 0)
		eq_(awg.channels[1].markers[2].low, 0)
		eq_(awg.channels[2].markers[1].low, -0.1)
		eq_(awg.channels[2].markers[2].low, 0)

	def testScenario(self):
		"""
		Run through a simple scenario.

		Note: Verification should also be done manually based on the AWG output.
		"""

		log = AssertHandler()

		awg = self.obtain_device()
		awg.reset()

		assert not awg.enabled

		# Setup
		existing_waveforms = awg.waveform_names

		data1 = linspace(-1.0, 1.0, 21)
		data2 = linspace(1.0, -1.0, 21)

		log.flush()
		awg.channels[1].set_waveform(data1, {
			1: ([1, 1, 1, 0, 0] * len(data1))[:len(data1)],
			2: ([0, 0, 0, 1, 1] * len(data1))[:len(data1)],
			3: [1, 2, 3, 4],
		})
		log.assert_logged('warning', 'marker 3 ignored: \[1, 2, 3, 4\]')

		awg.channels[2].set_waveform(data2, name='Test 2')

		awg.sampling_rate = 2e8 # Hz

		awg.channels[1].enabled = True
		awg.channels[1].amplitude = 0.8

		awg.channels[2].enabled = True
		awg.channels[2].amplitude = 0.4

		awg.channels[3].waveform_name = 'Test 2'
		awg.channels[3].enabled = True

		awg.channels[4].waveform_name = 'Channel 1'

		del awg.channels[3].waveform_name

		awg.run_mode = 'triggered'
		awg.enabled = True

		# Verify
		eq_(awg.sampling_rate, 2e8)

		eq_(awg.waveform_names, existing_waveforms + ['Channel 1', 'Test 2'])

		assert_array_almost_equal(awg.get_waveform('Channel 1'), data1, 4)
		eq_(awg.channels[1].amplitude, 0.8)
		assert_array_almost_equal(awg.get_waveform('Test 2'), data2, 4)
		eq_(awg.channels[2].amplitude, 0.4)

		for ch in [1, 2]:
			eq_(awg.channels[ch].enabled, True)
		for ch in [3, 4]:
			eq_(awg.channels[ch].enabled, False)

		for ch in [1, 4]:
			eq_(awg.channels[ch].waveform_name, 'Channel 1')
		eq_(awg.channels[2].waveform_name, 'Test 2')
		eq_(awg.channels[3].waveform_name, '')

		eq_(awg.run_mode, 'triggered')
		eq_(awg.waiting_for_trigger, True)
		eq_(awg.enabled, True)

		awg.trigger()


if __name__ == '__main__':
	main()
