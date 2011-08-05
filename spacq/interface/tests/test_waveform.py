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

		eq_(list(wg.waveform.data), [])
		eq_(wg.waveform.markers, {})

	def testWaveform(self):
		"""
		Generate a non-empty waveform.
		"""

		wg = waveform.Generator(frequency=Quantity(2, 'Hz'))

		wg.delay(Quantity(2, 's'))
		wg.marker(1, True)
		wg.marker(2, True)
		wg.pulse([], 0.5, Quantity(1, 's'))
		wg.pulse([1.0, 0.0, -1.0], 1.0, Quantity(3, 's'))
		wg.marker(1, False)
		wg.square(-0.5, Quantity(2, 's'))

		expected = [0.0, 0.0, 0.0, 1.0, 0.6, 0.2, -0.2, -0.6, -1.0, -0.5, -0.5, -0.5, -0.5, -1.0]

		wave, markers = wg.waveform
		assert_array_almost_equal(wave, expected, 4)
		eq_(markers[1], [False] * 3 + [True] * 6 + [False] * 5)
		eq_(markers[2], [False] * 3 + [True] * 11)
		assert 3 not in markers

	def testEndWithMarker(self):
		"""
		Marker data is longer than waveform data.
		"""

		wg = waveform.Generator(frequency=Quantity(1, 'mHz'))

		wg.marker(1, True)
		wg.marker(2, False)

		wave, markers = wg.waveform
		eq_(wave, [0.0])
		eq_(markers, {1: [True], 2: [False]})

	def testTooLong(self, dry_run=False):
		"""
		Try to create a waveform that is far too long.
		"""

		wg = waveform.Generator(frequency=Quantity(1, 'GHz'), dry_run=dry_run)

		wg.delay(Quantity(1, 'ns'))
		wg.delay(Quantity(1, 'us'))
		wg.delay(Quantity(1, 'ms'))
		assert_raises(ValueError, wg.delay, Quantity(0.01, 's'))

	def testDryRun(self):
		"""
		testTooLong, but as a dry run.
		"""

		self.testTooLong(dry_run=True)


if __name__ == '__main__':
	main()
