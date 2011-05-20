from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from testconfig import config

from devices.tektronix import awg5014b


class AWG5014BTest(unittest.TestCase):
	def testScenario(self):
		"""
		Run through a simple scenario.

		Note: Verification should also be done manually based on the AWG output.
		"""

		try:
			awg = awg5014b.AWG5014B(**config['devices']['awg'])
		except Exception as e:
			raise SkipTest('Could not connect to AWG.', e)

		# Setup
		min_val, max_val = awg.value_range
		step = (max_val - min_val) / 20

		existing_waveforms = awg.waveform_names

		data1 = list(xrange(min_val, max_val, step))
		data2 = list(xrange(max_val - 1, min_val - 1, -step))

		awg.create_waveform(
			'Test 1',
			data=data1,
			markers={
				1: ([1, 1, 1, 0, 0] * len(data1))[:len(data1)],
				2: ([0, 0, 0, 1, 1] * len(data1))[:len(data1)],
			}
		)
		awg.create_waveform(
			'Test 2',
			data=data2
		)

		awg.channels[1].waveform_name = 'Test 1'
		awg.channels[1].enabled = True

		awg.channels[2].waveform_name = 'Test 2'
		awg.channels[2].enabled = True

		awg.channels[3].waveform_name = 'Test 2'
		awg.channels[3].enabled = True

		awg.channels[4].waveform_name = 'Test 1'

		del awg.channels[3].waveform_name

		awg.enabled = True

		# Verify
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

		eq_(awg.enabled, True)


if __name__ == '__main__':
	unittest.main()
