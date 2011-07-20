from nose.tools import assert_almost_equal, eq_
from numpy import interp, linspace
from os import path
from unittest import main, TestCase

from ..pulse import Program
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

		try:
			wg.absolute_wave
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError'

		wg.min_value, wg.max_value = 0, 1

		eq_(wg.absolute_wave, [])

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

		eq_(wg.absolute_wave, [0, 0, 100, 80, 60, 40, 20, 0, -20, -40, -60, -80, -100, -50,
			-50, -100, 0, 100, -100, 0, 0, 25, 50, 0, -50, -25, 0, 0, 0, -50, 0, 0, 0, 25, 0, -25, 0,
			0, 50, 100, 50, 0])
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
		wave_points = [(x + 1.0) / 2.0 * 1024 for x in wave_points]
		wave_points = [int(x) for x in interp(linspace(0, 1, 402), linspace(0, 1, 201), wave_points)]

		eq_(wg.absolute_wave, [512] * 51 + [int(x) for x in linspace(512, 1024, 100)] + [0] * 50 + [1024] + wave_points)
		eq_(wg.get_marker(1), [True] * 51 + [False] * 553)
		eq_(wg.get_marker(2), [True] * 202 + [False] * 402)


if __name__ == '__main__':
	main()
