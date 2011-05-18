from nose.plugins.skip import SkipTest
from nose.tools import nottest
import unittest

from devices.tektronix import awg5014b
from devices.tests.test_abstract_device import REAL_DEVICE


class AWG5014BTest(unittest.TestCase):
	@nottest
	def testScenario(self):
		"""
		Run through a simple scenario.

		Note: Verification must be done manually based on the AWG output.
		"""

		try:
			awg = awg5014b.AWG5014B(**REAL_DEVICE)
		except:
			raise SkipTest('Could not connect to AWG.')

		min_val, max_val = awg.value_range

		awg.create_waveform('Test 1', xrange(min_val, max_val))
		awg.create_waveform('Test 2', xrange(max_val - 1, min_val - 1, -1))

		awg.channels[1].waveform_name = 'Test 1'
		awg.channels[1].enabled = True

		awg.channels[2].waveform_name = 'Test 2'

		awg.channels[3].waveform_name = 'Test 2'
		awg.channels[3].enabled = True

		awg.channels[4].waveform_name = 'Test 1'

		awg.enabled = True


if __name__ == '__main__':
	unittest.main()
