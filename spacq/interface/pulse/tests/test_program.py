from os import path
from nose.tools import assert_raises, eq_
from numpy.testing import assert_array_almost_equal, assert_array_equal
from unittest import main, TestCase

from ...units import Quantity

from .. import program


resource_dir = path.join(path.dirname(__file__), 'resources')


class ProgramTest(TestCase):
	missing = [
		(('_acq_marker', 'marker_num'), 1),
		(('_acq_marker', 'output'), 'f1'),
		(('first_square', 'amplitude'), Quantity(0.5, 'V')),
		(('last_square', 'amplitude'), Quantity(-0.5, 'V')),
		(('last_square', 'length'), Quantity(5, 'ns')),
		(('manipulator', 'amplitude'), Quantity(1, 'V')),
		(('manipulator', 'length'), Quantity(12, 'ns')),
		(('settle',), Quantity(20, 'ns')),
	]

	def testFromFile(self):
		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		p.env.set_value(('wobble', 'shape'), 'non-square')

		eq_(p.env.missing_values, set([name for name, value in self.missing]))

	def testInvalidShapePath(self):
		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		for name, value in self.missing:
			p.env.set_value(name, value)

		p.env.set_value(('wobble', 'shape'), 'this-shape-doesn\'t-exist')

		try:
			p.generate_waveforms(1e9)
		except program.PulseError as e:
			eq_('\n'.join(e[0]), """\
error: File "this-shape-doesn't-exist" (due to "wobble") not found at column 17 on line 21:
  first_square:f1 wobble:f2
                  ^\
""")
		else:
			assert False, 'Expected PulseError'

	def testGenerateWaveforms(self):
		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		# Missing values.
		assert_raises(ValueError, p.generate_waveforms, 1e9)

		for name, value in self.missing:
			p.env.set_value(name, value)

		p.env.set_value(('wobble', 'shape'), 'non-square')

		p.generate_waveforms(1e9)

		eq_(set(p.env.waveforms.keys()), set(['f1', 'f2']))

		f1 = p.env.waveforms['f1']
		loop = [0.0] * 10 + [0.5] + [0.0] * 7 + [0.5] + [0.0] * 7
		assert_array_equal(f1.wave, [0.0] * 10 + [0.5] * 1 + [0.0] * 7 + loop * 2 + [0.0] * 20 + [-0.5] * 5 + [0.0] * 49)
		eq_(f1.get_marker(1), [False] * 90 + [True] * 54)

		f2 = p.env.waveforms['f2']
		non_square = [0.1, 0.5, 0.7, 1.0] + [4.2] * 3 + [3.6, 9.9]
		wobble = f2._scale_waveform(non_square, Quantity(-1, 'mV').value, Quantity(8, 'ns'))
		manipulator = f2._scale_waveform(non_square, Quantity(1, 'V').value, Quantity(12, 'ns'))
		loop = [0.0] * 10 + wobble * 2
		end = manipulator + [0.0] * 15
		assert_array_almost_equal(f2.wave, [0.0] * 10 + wobble + loop * 2 + [0.0] * 20 + end * 2, 2)


if __name__ == '__main__':
	main()
