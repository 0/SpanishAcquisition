from nose.tools import assert_raises, eq_
from unittest import main, TestCase

from ...units import Quantity

from .. import commands


class ParameterTest(TestCase):
	def testRepr(self):
		"""
		Ensure that the held value is correctly represented.
		"""

		# For eval().
		Parameter = commands.Parameter

		parm = commands.Parameter('Test')

		eq_(parm.name, 'Test')
		assert parm.value is None
		eq_(eval(repr(parm)), parm)

		parm.value = 1234

		eq_(parm.name, 'Test')
		eq_(parm.value, 1234)
		eq_(eval(repr(parm)), parm)


class CommandTest(TestCase):
	def testRepr(self):
		"""
		Ensure that the command is properly represented.
		"""

		# For eval().
		Command = commands.Command

		cmd = commands.Command('cmd', range(5))

		eq_(cmd.command, 'cmd')
		eq_(cmd.arguments, [0, 1, 2, 3, 4])
		eq_(eval(repr(cmd)), cmd)


class ParserTest(TestCase):
	def testParser(self):
		"""
		Try to turn text into a list of sensible commands.
		"""

		pp = commands.Parser()

		prog = """
			set 0.0 # End a line with a comment.
			delay 500   ns # Argument with whitespace.
			no_arg
			sweep 0.0, 1.0, 1 ms # Multiple arguments.
			# Empty line:

			set 0.5 # Multiple # comment # markers.
			   delay 100    ns        # Extra whitespace.
			freq 1.23456789GHz,5#Less whitespace.
			delay 1 s

			marker 1, :high # A symbol.
			include "path", :imag # And a string.

			# How about some parameters?
			set parameter1, and_another_one
			delay a_time, :long
			reuse parameter0, parameter1   ,     parameter2
		"""

		expected = [commands.Command(cmd, args) for (cmd, args) in [
			('set', [0.0]),
			('delay', [Quantity(500.0, 'ns')]),
			('no_arg', []),
			('sweep', [0.0, 1.0, Quantity(1.0, 'ms')]),
			('set', [0.5]),
			('delay', [Quantity(100.0, 'ns')]),
			('freq', [Quantity(1.23456789, 'GHz'), 5]),
			('delay', [Quantity(1.0, 's')]),
			('marker', [1, 'high']),
			('include', ['path', 'imag']),
			('set', [commands.Parameter('parameter1'), commands.Parameter('and_another_one')]),
			('delay', [commands.Parameter('a_time'), 'long']),
			('reuse', [commands.Parameter('parameter0'), commands.Parameter('parameter1'), commands.Parameter('parameter2')]),
		]]

		result = pp.parse_program(prog)

		eq_(result, expected)

	def testInvalid(self):
		"""
		Unparseable things.
		"""

		pp = commands.Parser()

		assert_raises(ValueError, pp.parse_program, 'this is not valid')


class ProgramTest(TestCase):
	def testNoParameters(self):
		"""
		Try using only hardcoded values.
		"""

		cmds = [
			commands.Command('test0', []),
			commands.Command('test1', [1]),
			commands.Command('test2', [2, 3]),
		]

		prog = commands.Program(cmds)

		eq_(prog.all_parameters, set())
		eq_(prog.unset_parameters, set())
		eq_(prog.evaluated, prog)

	def testWithParameters(self):
		"""
		Throw in a few arguments to generate parameters.
		"""

		# For eval().
		Program, Command, Parameter = commands.Program, commands.Command, commands.Parameter

		cmds = [
			commands.Command('test0', [commands.Parameter('parm0'), commands.Parameter('parm1')]),
			commands.Command('test1', [commands.Parameter('parm2'), commands.Parameter('parm3')]),
			commands.Command('test1.5', ['not', 'parameters']),
			commands.Command('test2', [commands.Parameter('parm0'), commands.Parameter('parm2')]),
			commands.Command('test3', [commands.Parameter('parm1'), commands.Parameter('parm3')]),
		]

		prog = commands.Program(cmds)

		prog.set_parameter('parm0', 'a value')
		prog.set_parameter('parm3', 'another value')

		eq_(prog.all_parameters, set('parm{0}'.format(x) for x in [0, 1, 2, 3]))
		eq_(prog.unset_parameters, set('parm{0}'.format(x) for x in [1, 2]))

		try:
			prog.evaluated
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError'

		prog.set_parameter('parm1', -1234.5)
		prog.set_parameter('parm2', ('perhaps', 'a', 'tuple'))

		eq_(prog.all_parameters, set('parm{0}'.format(x) for x in [0, 1, 2, 3]))
		eq_(prog.unset_parameters, set())

		cmds_evaluated = [
			commands.Command('test0', ['a value', -1234.5]),
			commands.Command('test1', [('perhaps', 'a', 'tuple'), 'another value']),
			commands.Command('test1.5', ['not', 'parameters']),
			commands.Command('test2', ['a value', ('perhaps', 'a', 'tuple')]),
			commands.Command('test3', [-1234.5, 'another value']),
		]

		eq_(prog.evaluated, commands.Program(cmds_evaluated))

		eq_(eval(repr(prog)), prog)

	def testFromString(self):
		"""
		Try to create a program from text.
		"""

		prog = commands.Program('this "is", :line, 1\nand "this is line", 2')

		cmds = [
			commands.Command('this', ['is', 'line', 1]),
			commands.Command('and', ['this is line', 2]),
		]

		eq_(prog.commands, cmds)


if __name__ == '__main__':
	main()
