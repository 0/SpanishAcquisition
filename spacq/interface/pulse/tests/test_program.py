from os import path
from nose.tools import assert_raises, eq_
from numpy.testing import assert_array_almost_equal, assert_array_equal
from unittest import main, TestCase

from ...units import Quantity
from ..parser import PulseSyntaxError

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
		"""
		Grab a file and load the program in it.
		"""

		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		p.set_value(('wobble', 'shape'), 'non-square')

		eq_(p.missing_values, set([name for name, value in self.missing]))
		eq_(set(p.variables), set(['bumps', 'bump_spacing', 'settle', 'end_delay', 'first_square', 'wobble', 'last_square', 'manipulator', 'f1', 'f2', '_acq_marker']))

	def testInvalid(self):
		"""
		This program isn't syntactically correct.
		"""

		assert_raises(PulseSyntaxError, program.Program.from_file, path.join(resource_dir, '02.pulse'))

	def testInvalidShapePath(self):
		"""
		A shape file which isn't there.
		"""

		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		for name, value in self.missing:
			p.set_value(name, value)

		p.set_value(('wobble', 'shape'), 'this-shape-doesn\'t-exist')

		try:
			p.generate_waveforms()
		except program.PulseError as e:
			eq_('\n'.join(e[0]), """\
error: File "this-shape-doesn't-exist" (due to "wobble") not found at column 17 on line 21:
  first_square:f1 wobble:f2
                  ^\
""")
		else:
			assert False, 'Expected PulseError'

	def testInvalidShapeFile(self):
		"""
		A shape file which isn't a shape file.
		"""

		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		for name, value in self.missing:
			p.set_value(name, value)

		assert ('wobble', 'shape') not in p.values
		p.set_value(('wobble', 'shape'), '01.pulse')
		assert ('wobble', 'shape') in p.values

		assert_raises(ValueError, p.generate_waveforms)

	def testGenerateWaveforms(self):
		"""
		Finally generate some waveforms.
		"""

		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		# Missing values.
		assert_raises(ValueError, p.generate_waveforms)

		for name, value in self.missing:
			p.set_value(name, value)

		p.set_value(('wobble', 'shape'), 'non-square')

		p.frequency = Quantity(1, 'GHz')
		eq_(p.frequency, Quantity(1, 'GHz'))
		waveforms = p.generate_waveforms()

		eq_(set(waveforms.keys()), set(['f1', 'f2']))

		f1 = waveforms['f1']
		loop = [0.0] * 10 + [0.5] + [0.0] * 7 + [0.5] + [0.0] * 7
		assert_array_equal(f1.data, [0.0] * 10 + [0.5] * 1 + [0.0] * 7 + loop * 2 + [0.0] * 20 + [-0.5] * 5 + [0.0] * 49)
		eq_(f1.markers[1], [False] * 90 + [True] * 54)

		f2 = waveforms['f2']
		f2_gen = p._env.generators['f2']
		non_square = [0.1, 0.5, 0.7, 1.0] + [4.2] * 3 + [3.6, 9.9]
		wobble = f2_gen._scale_waveform(non_square, Quantity(-1, 'mV').value, Quantity(8, 'ns'))
		manipulator = f2_gen._scale_waveform(non_square, Quantity(1, 'V').value, Quantity(12, 'ns'))
		loop = [0.0] * 10 + wobble * 2
		end = manipulator + [0.0] * 15
		assert_array_almost_equal(f2.data, [0.0] * 10 + wobble + loop * 2 + [0.0] * 20 + end * 2, 2)

	def testWaveformsDryRun(self):
		"""
		Run through waveform generation, but don't actually generate anything.
		"""

		p = program.Program.from_file(path.join(resource_dir, '01.pulse'))

		# Missing values.
		assert_raises(ValueError, p.generate_waveforms, dry_run=True)

		for name, value in self.missing:
			p.set_value(name, value)

		p.set_value(('wobble', 'shape'), 'non-square')

		# Too long.
		p.frequency = Quantity(1, 'YHz')
		assert_raises(ValueError, p.generate_waveforms, dry_run=True)

		# Just right.
		p.frequency = Quantity(1, 'GHz')
		waveforms = p.generate_waveforms(dry_run=True)

		# But nothing there.
		eq_(set(waveforms.keys()), set(['f1', 'f2']))
		eq_(list(waveforms['f1'].data), [])
		eq_(waveforms['f1'].markers, {})
		eq_(list(waveforms['f2'].data), [])
		eq_(waveforms['f2'].markers, {})


if __name__ == '__main__':
	main()
