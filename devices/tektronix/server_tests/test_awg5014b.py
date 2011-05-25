from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from testconfig import config
from tests.tools import AssertHandler

from devices.tektronix import awg5014b


class AWG5014BTest(unittest.TestCase):
	def __obtain_device(self):
		"""
		Try to get a handle for a physical device. 
		"""

		try:
			return awg5014b.AWG5014B(**config['devices']['awg'])
		except Exception as e:
			raise SkipTest('Could not connect to device.', e)

	def testMarkerValues(self):
		"""
		Set the various marker values.
		"""

		awg = self.__obtain_device()

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

		awg = self.__obtain_device()

		# Setup
		min_val, max_val = awg.value_range
		step = (max_val - min_val) / 20

		existing_waveforms = awg.waveform_names

		data1 = list(xrange(min_val, max_val, step))
		data2 = list(xrange(max_val - 1, min_val - 1, -step))

		log.flush()
		awg.create_waveform(
			'Test 1',
			data=data1,
			markers={
				1: ([1, 1, 1, 0, 0] * len(data1))[:len(data1)],
				2: ([0, 0, 0, 1, 1] * len(data1))[:len(data1)],
				3: [1, 2, 3, 4],
			}
		)
		log.assert_logged('warning', 'marker 3 ignored: \[1, 2, 3, 4\]')

		awg.create_waveform(
			'Test 2',
			data=data2
		)

		awg.sampling_rate = 2e8 # Hz

		awg.channels[1].waveform_name = 'Test 1'
		awg.channels[1].enabled = True
		awg.channels[1].amplitude = 0.8

		awg.channels[2].waveform_name = 'Test 2'
		awg.channels[2].enabled = True
		awg.channels[2].amplitude = 0.4

		awg.channels[3].waveform_name = 'Test 2'
		awg.channels[3].enabled = True

		awg.channels[4].waveform_name = 'Test 1'

		del awg.channels[3].waveform_name

		awg.run_mode = 'triggered'
		awg.enabled = True

		# Verify
		eq_(awg.sampling_rate, 2e8)

		eq_(awg.waveform_names, existing_waveforms + ['Test 1', 'Test 2'])

		eq_(awg.get_waveform('Test 1'), data1)
		eq_(awg.get_waveform('Test 2'), data2)

		for ch in [1, 2]:
			eq_(awg.channels[ch].enabled, True)
		for ch in [3, 4]:
			eq_(awg.channels[ch].enabled, False)

		for ch in [1, 4]:
			eq_(awg.channels[ch].waveform_name, 'Test 1')
		eq_(awg.channels[2].waveform_name, 'Test 2')
		eq_(awg.channels[3].waveform_name, '')

		eq_(awg.run_mode, 'triggered')
		eq_(awg.waiting_for_trigger, True)
		eq_(awg.enabled, True)

		awg.trigger()


if __name__ == '__main__':
	unittest.main()
