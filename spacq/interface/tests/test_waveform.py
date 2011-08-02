from nose.tools import assert_raises, eq_
from numpy.testing import assert_array_almost_equal
from unittest import main, TestCase

from ..units import Quantity

from .. import waveform


class GeneratorTest(TestCase):
	def testEmpty(self):
		"""
		Generate an empty waveform.
		"""

		wg = waveform.Generator(frequency=Quantity(1, 'Hz'))

		eq_(list(wg.wave), [])

	def testWaveform(self):
		"""
		Generate a non-empty waveform.
		"""

		wg = waveform.Generator(frequency=Quantity(2, 'Hz'))

		wg.delay(Quantity(2, 's'))
		wg.marker(1, 'high')
		wg.marker(2, 'high')
		wg.pulse([], 0.5, Quantity(1, 's'))
		wg.pulse([1.0, 0.0, -1.0], 1.0, Quantity(3, 's'))
		wg.marker(1, 'low')
		wg.square(-0.5, Quantity(2, 's'))

		expected = [0.0, 0.0, 0.0, 1.0, 0.6, 0.2, -0.2, -0.6, -1.0, -0.5, -0.5, -0.5, -0.5, -1.0]

		assert_array_almost_equal(wg.wave, expected, 4)
		eq_(wg.get_marker(1), [False] * 3 + [True] * 6 + [False] * 5)
		eq_(wg.get_marker(2), [False] * 3 + [True] * 11)
		eq_(wg.get_marker(3), [False] * 14)

	def testTooLong(self):
		"""
		Try to create a waveform that is far too long.
		"""

		wg = waveform.Generator(frequency=Quantity(1, 'GHz'))

		wg.delay(Quantity(1, 'ns'))
		wg.delay(Quantity(1, 'us'))
		wg.delay(Quantity(1, 'ms'))
		assert_raises(ValueError, wg.delay, Quantity(1, 's'))


if __name__ == '__main__':
	main()
