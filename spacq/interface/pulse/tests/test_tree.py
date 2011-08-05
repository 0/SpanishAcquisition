from nose.tools import assert_raises, eq_
from numpy.testing import assert_array_almost_equal
from os import path
from unittest import main, TestCase

from ...units import Quantity
from ..parser import Parser

from .. import tree


resource_dir = path.join(path.dirname(__file__), 'resources')


class ValidTreeTest(TestCase):
	prog = Parser()("""
		int repeat = 2
		delay abc1 = 100 ns, def2
		pulse ghi1, jkl2 = {{shape: 'square'}}
		output mno1, pqr2

		ghi1.shape = '{0}'
		ghi1.length = 8 ns
		ghi1.amplitude = -1.0 mV

		abc1
		(10 ns):pqr2

		times repeat {{
			def2
			ghi1:mno1
			(ghi1 abc1 10 ns jkl2):mno1 (def2 jkl2 def2):pqr2
		}}

		acquire

		5 ns
	""".format(path.join(resource_dir, 'non-square')))

	def testDeclarations(self):
		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(self.prog)

		expected = {
			'_acq_marker': 'acq_marker',
			'abc1': 'delay',
			'def2': 'delay',
			'ghi1': 'pulse',
			'jkl2': 'pulse',
			'mno1': 'output',
			'pqr2': 'output',
			'repeat': 'int',
		}

		eq_(env.errors, [])
		eq_(env.variables, expected)

	def testValues(self):
		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(self.prog)

		env.stage = env.stages.values
		env.traverse_tree(self.prog)

		expected = {
			('abc1',): Quantity('100 ns'),
			('ghi1', 'amplitude'): Quantity(-1, 'mV'),
			('ghi1', 'length'): Quantity(8, 'ns'),
			('ghi1', 'shape'): path.join(resource_dir, 'non-square'),
			('jkl2', 'shape'): 'square',
			('repeat',): 2,
		}

		missing = set([('_acq_marker', 'marker_num'), ('_acq_marker', 'output'), ('def2',),
				('jkl2', 'amplitude'), ('jkl2', 'length')])

		eq_(env.errors, [])
		eq_(env.values, expected)
		eq_(env.missing_values, missing)

		# Later additions (perhaps from the UI).
		updates = {
			('_acq_marker', 'marker_num'): 1,
			('_acq_marker', 'output'): 'mno1',
			('def2',): Quantity('7 ns'),
			('jkl2', 'amplitude'): Quantity(1, 'V'),
			('jkl2', 'length'): Quantity(50, 'ns'),
		}

		for name, value in updates.items():
			env.set_value(name, value)

		expected.update(updates)

		eq_(env.errors, [])
		eq_(env.values, expected)

	def testCommands(self):
		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(self.prog)

		env.stage = env.stages.commands
		env.traverse_tree(self.prog)

		eq_(env.errors, [])
		assert env.acquisition

	def testWaveforms(self):
		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(self.prog)

		env.stage = env.stages.values
		env.traverse_tree(self.prog)

		env.stage = env.stages.commands
		env.traverse_tree(self.prog)

		updates = {
			('_acq_marker', 'marker_num'): 5,
			('_acq_marker', 'output'): 'pqr2',
			('def2',): Quantity(7, 'ns'),
			('jkl2', 'amplitude'): Quantity(1, 'V'),
			('jkl2', 'length'): Quantity(50, 'ns'),
		}

		for name, value in updates.items():
			env.set_value(name, value)

		env.frequency = Quantity(1, 'GHz')
		env.stage = env.stages.waveforms
		env.traverse_tree(self.prog)

		eq_(env.errors, [])

		mno1 = env.waveforms['mno1']
		mno1_gen = env.generators['mno1']
		non_square = mno1_gen._scale_waveform([0.1, 0.5, 0.7, 1.0] + [4.2] * 3 + [3.6, 9.9],
				Quantity(-1, 'mV').value, Quantity(8, 'ns'))
		loop = [0.0] * 7 + non_square * 2 + [0.0] * 110 + [1.0] * 50 + [0.0]
		assert_array_almost_equal(mno1.data, [0.0] * 110 + loop * 2 + [0.0] * 5)

		pqr2 = env.waveforms['pqr2']
		loop = [0.0] * 22 + [1.0] * 50 + [0.0] * 112
		assert_array_almost_equal(pqr2.data, [0.0] * 110 + loop * 2 + [0.0] * 5)

		assert 1 not in pqr2.markers
		eq_(pqr2.markers[5], [False] * 478 + [True] * 5)


class InvalidTreeTest(TestCase):
	def testDeclarations(self):
		prog = Parser()("""
			int repeat = 2
			delay abc1 = 100 ns, def2
			pulse ghi1, jkl2 = {shape: 'square'}
			output mno1, pqr2

			delay abc1, def2 = 10 ms, stu3

			vwx4

			times 5 {
				int x = 9
			}
		""")

		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(prog)

		expected_errors = ['Re-decl'] * 2 + ['Declara']

		eq_(len(env.errors), len(expected_errors))

		for error, expected_error in zip(env.errors, expected_errors):
			assert error[0].startswith(expected_error), error

	def testValues(self):
		prog = Parser()("""
			int repeat = 2
			delay abc1 = 100 ns, def2
			pulse ghi1, jkl2 = {shape: 'square'}
			output mno1, pqr2

			delay abc1 = 50 ms, def2
			mno1 = "test"
			def2 = 6 ; def2 = 6 Hz
			ghi1 = 0
			ghi1.shape = 50 ms
			jkl2.amplitude = 8
			jkl2.length = 1234 A
			repeat = 6 s
			repeat = 2.0
			zzz1 = 5 ms
			zzz1.foo = 5 ms
			ghi1.something_else = 5

			times 5 {
				int x = 9
				y = 10
			}
		""")

		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(prog)

		env.errors = []
		env.stage = env.stages.values
		env.traverse_tree(prog)

		expected_errors = (['Re-assi', 'Cannot a'] + ['Must assi'] * 8 + ['Undecla', 'Unrec'] * 2 +
				['Assig'] + ['Undecl'])

		eq_(len(env.errors), len(expected_errors))

		for error, expected_error in zip(env.errors, expected_errors):
			assert error[0].startswith(expected_error), (error, expected_error)

		assert_raises(KeyError, env.set_value, ('xyz',), 'zyx')

	def testCommands(self):
		prog = Parser()("""
			int repeat = 2
			delay abc1 = 100 ns, def2
			pulse ghi1, jkl2 = {shape: 'square'}
			output mno1, pqr2

			abc1
			(10 ns):pqr2

			times repeat {
				def2
				ghi1:mno1
				(ghi1 abc1 10 ns jkl2):mno1 (10 V def2 jkl2 def2 pqr2):pqr2

				acquire
				mno1
			}

			acquire

			times ghi1 {}

			acquire

			5 ns
			1 A
		""")
		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(prog)

		env.errors = []
		env.stage = env.stages.commands
		env.traverse_tree(prog)

		expected_errors = ['Delay mu', 'Invali', 'Not a d', 'Repeate', 'Repeti', 'Repeate', 'Delay mu']

		eq_(len(env.errors), len(expected_errors))

		for error, expected_error in zip(env.errors, expected_errors):
			assert error[0].startswith(expected_error), (error, expected_error)

	def testWaveforms(self):
		prog = Parser()("""
			delay d1

			d1
		""")
		env = tree.Environment()

		env.stage = env.stages.declarations
		env.traverse_tree(prog)

		env.stage = env.stages.values
		env.traverse_tree(prog)

		env.stage = env.stages.commands
		env.traverse_tree(prog)

		env.errors = []
		env.stage = env.stages.waveforms

		assert_raises(ValueError, env.traverse_tree, prog)


class DrawThingTest(TestCase):
	def testDrawTree(self):
		"""
		Try our hand at drawing.
		"""

		prog = Parser()("""
			pulse p1 = {shape: 'something'}
			output f1

			p1.length = 5 ns

			times 5 {
				10 ns
				p1:f1
			}

			acquire
		""")

		drawing = prog.draw()

		eq_(drawing, """\
Block
 Declaration
  pulse
  Assignment
   p1
   Dictionary
    'shape': 'something'
 Declaration
  output
  Variable
   f1
 Assignment
  Attribute
   p1
   length
  5 ns
 Loop
  5
  Block
   Delay
    10 ns
   ParallelPulses
    Pulse
     PulseSequence
      p1
     f1
  Acquire
""")


if __name__ == '__main__':
	main()
