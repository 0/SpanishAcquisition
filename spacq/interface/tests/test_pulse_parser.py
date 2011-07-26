from nose.tools import eq_
from os import path
from pyparsing import ParseException
from unittest import main, TestCase

from .. import pulse_parser


resource_dir = path.join(path.dirname(__file__), 'resources')


class ParserTest(TestCase):
	def testValid(self):
		"""
		Run down the happy path, line by line.
		"""

		prog = [
			# Lone declaration.
			('int test',
				('Declaration', ['int',
					('Variable', ['test'])])),
			# Declaration with some initialization.
			('delay d1=+5ms,d2,\td3 = -7e2   ns2.J',
				('Declaration', ['delay',
					('Assignment', ['d1', ('Quantity', [5, 'ms'])]),
					('Variable', ['d2']),
					('Assignment', ['d3', ('Quantity', [-7e2, 'ns2.J'])])])),
			# Assignment of value.
			('test = -99',
				('Assignment', ['test', -99])),
			# Assignment of multiple values.
			('long_pulse = {shape: \'filename\', length: 1 Ps}',
				('Assignment', ['long_pulse', ('Dictionary', [
					('DictionaryItem', ['shape', 'filename']),
					('DictionaryItem', ['length', ('Quantity', [1, 'Ps'])])])])),
			# Assignment of identifier.
			('d2 = d3',
				('Assignment', ['d2', 'd3'])),
			# Comments.
			('  output f1 ,f2\t # outputs',
				('Declaration', ['output',
					('Variable', ['f1']),
					('Variable', ['f2'])])),
			# Delay.
			('10 us',
				('Delay', [('Quantity', [10, 'us'])])),
			# Variable delay.
			('d5 #Comment: a = 5',
				('Delay', ['d5'])),
			# Attribute assignment.
			('p1.length = 50.0 as',
				('Assignment', [
					('Attribute', ['p1', 'length']),
					('Quantity', [50.0, 'as'])])),
			# Pulse command.
			('some_pulse:f1',
				('ParallelPulses', [
					('Pulse', [('PulseSequence', ['some_pulse']), 'f1'])])),
			# Parallel pulses.
			('a_pulse:outputA another_pulse:outputB',
				('ParallelPulses', [
					('Pulse', [('PulseSequence', ['a_pulse']), 'outputA']),
					('Pulse', [('PulseSequence', ['another_pulse']), 'outputB'])])),
			# Multiple pulse commands.
			('(several commands with a 99 fs delay):formula1 lone_command:indy500',
				('ParallelPulses', [
					('Pulse', [('PulseSequence', [
						'several', 'commands', 'with', 'a',
						('Delay', [('Quantity', [99, 'fs'])]),
						'delay']), 'formula1']),
					('Pulse', [('PulseSequence', ['lone_command']), 'indy500'])])),
			# Acquire.
			('\tacquire   #',
				('Acquire', []))
		]

		pp = pulse_parser.Parser()

		for line, ast in prog:
			try:
				result = pp.parseString(line).asList()
			except ParseException:
				print line
				raise

			eq_(result[0], ast)

	def testMultiple(self):
		"""
		Several lines at once.
		"""

		prog = """
		# Declare:
		int placeholder = 0
		delay settle, end_delay = 10 ns
		pulse first_square, wobble
		output f1, f2

		# Configure:
		first_square = {shape: 'square', length: 1 ms}
		wobble.length = 50 us
		wobble.amplitude = 1 mV

		# Execute:
		10 us
		first_square:f1 (wobble +1e-3 us wobble):f2
		settle # Wait before the acquisition.
		acquire
		end_delay
		"""

		expected = [
			('Declaration', ['int',
				('Assignment', ['placeholder', 0])]),
			('Declaration', ['delay',
				('Variable', ['settle']),
				('Assignment', ['end_delay', ('Quantity', [10, 'ns'])])]),
			('Declaration', ['pulse',
				('Variable', ['first_square']),
				('Variable', ['wobble'])]),
			('Declaration', ['output',
				('Variable', ['f1']),
				('Variable', ['f2'])]),
			('Assignment', ['first_square',
				('Dictionary', [
					('DictionaryItem', ['shape', 'square']),
					('DictionaryItem', ['length', ('Quantity', [1, 'ms'])])])]),
			('Assignment', [
				('Attribute', ['wobble', 'length']),
				('Quantity', [50, 'us'])]),
			('Assignment', [
				('Attribute', ['wobble', 'amplitude']),
				('Quantity', [1, 'mV'])]),
			('Delay', [('Quantity', [10, 'us'])]),
			('ParallelPulses', [
				('Pulse', [('PulseSequence', ['first_square']), 'f1']),
				('Pulse', [('PulseSequence', [
					'wobble',
					('Delay', [('Quantity', [+1e-3, 'us'])]),
					'wobble']), 'f2'])]),
			('Delay', ['settle']),
			('Acquire', []),
			('Delay', ['end_delay']),
		]

		pp = pulse_parser.Parser()

		result = pp.parseString(prog).asList()

		eq_(result, expected)

	def testLoop(self):
		"""
		Repeat!
		"""

		prog = """
		times 5 {
			d1
			p1:f1 p2:f2
		}

		times M {
			d2

			times N {
				p2:f1 p1:f2
			}
		}
		"""

		expected = [
			('Loop', [5, ('Block', [
				('Delay', ['d1']),
				('ParallelPulses', [
					('Pulse', [('PulseSequence', ['p1']), 'f1']),
					('Pulse', [('PulseSequence', ['p2']), 'f2'])])])]),
			('Loop', ['M', ('Block', [
				('Delay', ['d2']),
				('Loop', ['N', ('Block', [
					('ParallelPulses', [
						('Pulse', [('PulseSequence', ['p2']), 'f1']),
						('Pulse', [('PulseSequence', ['p1']), 'f2'])])])])])]),
		]

		pp = pulse_parser.Parser()

		result = pp.parseString(prog).asList()

		eq_(result, expected)

	def testOneLine(self):
		"""
		Line breaks are optional.
		"""

		prog = 'int x=5;delay d1;;d1;d1;times x{d1;d1;};times x{d1}d1'

		expected = [
			('Declaration', ['int',
				('Assignment', ['x', 5])]),
			('Declaration', ['delay',
				('Variable', ['d1'])]),
			('Delay', ['d1']),
			('Delay', ['d1']),
			('Loop', ['x', ('Block', [
				('Delay', ['d1']),
				('Delay', ['d1'])])]),
			('Loop', ['x', ('Block', [
				('Delay', ['d1'])])]),
			('Delay', ['d1']),
		]

		pp = pulse_parser.Parser()

		result = pp.parseString(prog).asList()

		eq_(result, expected)

	def testFromFile(self):
		"""
		Parse an entire file.
		"""

		expected = [
			('Declaration', ['int',
				('Assignment', ['bumps', 2])]),
			('Declaration', ['delay',
				('Assignment', ['bump_spacing', ('Quantity', [100, 'ns'])]),
				('Variable', ['settle']),
				('Assignment', ['end_delay', ('Quantity', [10, 'ns'])])]),
			('Declaration', ['pulse',
				('Variable', ['first_square']),
				('Variable', ['wobble'])]),
			('Declaration', ['pulse',
				('Assignment', ['last_square', ('Dictionary', [
					('DictionaryItem', ['shape', 'square'])])])]),
			('Declaration', ['pulse',
				('Assignment', ['manipulator', ('Dictionary', [
					('DictionaryItem', ['shape', '/path/to/filename'])])])]),
			('Declaration', ['output',
				('Variable', ['f1']),
				('Variable', ['f2'])]),
			('Assignment', ['first_square',
				('Dictionary', [
					('DictionaryItem', ['shape', 'square']),
					('DictionaryItem', ['length', ('Quantity', [1, 'ms'])])])]),
			('Assignment',
				[('Attribute', ['wobble', 'length']),
					('Quantity', [50, 'us'])]),
			('Assignment',
				[('Attribute', ['wobble', 'amplitude']),
					('Quantity', [1, 'mV'])]),
			('Delay', [('Quantity', [10, 'us'])]),
			('ParallelPulses', [
				('Pulse', [('PulseSequence', ['first_square']), 'f1']),
				('Pulse', [('PulseSequence', ['wobble']), 'f2'])]),
			('Loop', ['bumps', ('Block', [
				('Delay', ['bump_spacing']),
				('Loop', [2, ('Block', [
					('ParallelPulses', [
						('Pulse', [('PulseSequence', ['first_square']), 'f1']),
						('Pulse', [('PulseSequence', ['wobble']), 'f2'])])])])])]),
			('Delay', ['settle']),
			('Acquire', []),
			('ParallelPulses', [
				('Pulse', [('PulseSequence', ['last_square']), 'f1']),
				('Pulse', [('PulseSequence', ['manipulator', 'end_delay', 'manipulator']), 'f2'])]),
			('Delay', ['end_delay']),
		]

		pp = pulse_parser.Parser()

		result = pp.parseFile(path.join(resource_dir, '01.pulse')).asList()

		eq_(result, expected)

	def testInvalid(self):
		"""
		Try the error detection and reporting.
		"""

		prog = [
			('int a b', 'Expected end of text (at char 6), (line:1, col:7)'),
		]

		pp = pulse_parser.Parser()

		for line, err in prog:
			try:
				pp.parseString(line).asList()
			except ParseException as e:
				eq_(str(e), err)
			else:
				assert False, 'Expected ParseException'


if __name__ == '__main__':
	main()
