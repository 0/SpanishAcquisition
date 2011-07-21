from nose.tools import assert_almost_equal, assert_raises, eq_
from numpy import interp, linspace
from numpy.testing import assert_array_almost_equal
from os import path
from unittest import main, TestCase

from ..pulse.commands import Program
from ..units import Quantity

from .. import waveform


resource_dir = path.join(path.dirname(__file__), 'resources')


class ReadWaveTest(TestCase):
	def testRead(self):
		"""
		Try to read a simple wave file.
		"""

		wave = waveform.read_wave(path.join(resource_dir, '01.wav'))

		expected = [0.0, 1.0, -1.0, 0.0]

		for w, e in zip(wave, expected):
			assert_almost_equal(w, e, 4)


class GeneratorTest(TestCase):
	def testEmpty(self):
		"""
		Generate an empty waveform.
		"""

		wg = waveform.Generator(frequency=1)

		eq_(wg.wave, [])

	def testWaveform(self):
		"""
		Generate a non-empty waveform.
		"""

		wg = waveform.Generator(frequency=1, min_value=-100, max_value=100)
		wg.cwd = resource_dir

		wg.set(0.0)
		wg.delay(Quantity(1, 's'))
		wg.marker(1, 'high')
		wg.marker(2, 'high')
		wg.sweep(1.0, -1.0, Quantity(11, 's'))
		wg.marker(1, 'low')
		wg.square(-0.5, Quantity(2, 's'))
		wg.include_wave('01.wav')
		wg.include_wave('01.wav', 0.5, Quantity(7, 's'))
		wg.marker(2, 'low')
		wg.include_ampph('02.csv', 'real')
		wg.include_ampph('02.csv', 'imag')
		wg.include_ampph('02.csv', 'abs', 2.0)

		expected = [0.0, 0.0, 1.0, 0.8, 0.6, 0.4, 0.2, 0.0, -0.2, -0.4, -0.6, -0.8, -1.0, -0.5, -0.5,
				-1.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.25, 0.5, 0.0, -0.5, -0.25, 0.0, 0.0, 0.0, -0.5, 0.0,
				0.0, 0.0, 0.25, 0.0, -0.25, 0.0, 0.0, 0.5, 1.0, 0.5, 0.0]

		print wg.wave
		print expected

		assert_array_almost_equal(wg.wave, expected, 4)
		eq_(wg.get_marker(1), [0] * 2 + [1] * 11 + [0] * 29)
		eq_(wg.get_marker(2), [0] * 2 + [1] * 25 + [0] * 15)

	def testFromFile(self):
		"""
		Generate a waveform from a program stored in a file.
		"""

		wg = waveform.Generator(frequency=1e9, min_value=0, max_value=1024)
		wg.cwd = resource_dir

		prog_lines = open(path.join(resource_dir, '04.pulse')).readlines()
		prog = Program('\n'.join(prog_lines))

		prog.set_parameter('wave_amplitude', 1.0)

		wg.run_commands(prog.evaluated.commands)

		wave_points = waveform.read_wave(path.join(resource_dir, '03.wav'))
		wave_points = interp(linspace(0, 1, 402), linspace(0, 1, 201), wave_points)

		expected = [0.0] * 51 + list(linspace(0.0, 1.0, 100)) + [-1.0] * 50 + [1.0] + list(wave_points)

		assert_array_almost_equal(wg.wave, expected, 4)
		eq_(wg.get_marker(1), [True] * 51 + [False] * 553)
		eq_(wg.get_marker(2), [True] * 202 + [False] * 402)
		eq_(wg.get_marker(3), [False] * 604)

	def testInvalid(self):
		"""
		Try a few invalid things.
		"""

		wg = waveform.Generator(frequency=1)

		assert_raises(IOError, wg.include_wave, '01.wav')
		assert_raises(ValueError, wg.run_commands, Program('this "is not a command"').commands)
		assert_raises(ValueError, wg.marker, 0, 'medium')

		wg.cwd = resource_dir
		assert_raises(ValueError, wg.include_ampph, '02.csv', 'fake')


if __name__ == '__main__':
	main()
