from nose.tools import eq_
from os import path
from unittest import main, TestCase

from ...units import Quantity
from ..parser import (Acquire, Assignment, Attribute, Block, Declaration,
		Delay, Dictionary, DictionaryItem, Loop, ParallelPulses, Pulse,
		PulseSequence, Variable)

from .. import parser


resource_dir = path.join(path.dirname(__file__), 'resources')


class ParserTest(TestCase):
	def testValid(self):
		"""
		Run down the happy path, line by line.
		"""

		prog = [
			# Lone declaration.
			('int test',
				Declaration({'type': 'int', 'variables': [
					Variable({'name': 'test'})]})),
			# Declaration with some initialization.
			('delay d1=+5ms,d2,\td3 = -7e2   ns2.J',
				Declaration({'type': 'delay', 'variables': [
					Assignment({'target': 'd1', 'value': Quantity(5, 'ms')}),
					Variable({'name': 'd2'}),
					Assignment({'target': 'd3', 'value': Quantity(-7e2, 'ns2.J')})]})),
			# Assignment of value.
			('test = -99',
				Assignment({'target': 'test', 'value': -99})),
			# Assignment of multiple values.
			('long_pulse = {shape: \'filename\', length: 1 Ps}',
				Assignment({'target': 'long_pulse', 'value': Dictionary([
					DictionaryItem({'key': 'shape', 'value': 'filename'}),
					DictionaryItem({'key': 'length', 'value': Quantity(1, 'Ps')})])})),
			# Comments.
			('  output f1 ,f2\t # outputs',
				Declaration({'type': 'output', 'variables': [
					Variable({'name': 'f1'}),
					Variable({'name': 'f2'})]})),
			# Delay.
			('10 us',
				Delay({'length': Quantity(10, 'us')})),
			# Variable delay.
			('d5 #Comment: a = 5',
				Delay({'length': 'd5'})),
			# Attribute assignment.
			('p1.length = 50.0 as',
				Assignment({
					'target': Attribute({'variable': 'p1', 'name': 'length'}),
					'value': Quantity(50.0, 'as')})),
			# Pulse command.
			('some_pulse:f1',
				ParallelPulses([
					Pulse({'sequence': PulseSequence(['some_pulse']), 'target': 'f1'})])),
			# Parallel pulses.
			('a_pulse:outputA another_pulse:outputB',
				ParallelPulses([
					Pulse({'sequence': PulseSequence(['a_pulse']), 'target': 'outputA'}),
					Pulse({'sequence': PulseSequence(['another_pulse']), 'target': 'outputB'})])),
			# Multiple pulse commands.
			('(several commands with a 99 fs delay):formula1 lone_command:indy500',
				ParallelPulses([
					Pulse({'sequence': PulseSequence([
						'several', 'commands', 'with', 'a',
						Delay({'length': Quantity(99, 'fs')}),
						'delay']), 'target': 'formula1'}),
					Pulse({'sequence': PulseSequence(['lone_command']), 'target': 'indy500'})])),
			# Acquire.
			('\tacquire   #',
				Acquire())
		]

		pp = parser.Parser()

		for line, ast in prog:
			try:
				result = pp(line)
			except Exception:
				print line
				raise

			eq_(result, Block([ast]))

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
		wobble.amplitude = -0.5 mV

		# Execute:
		10 us
		first_square:f1 (wobble +1e-3 us wobble):f2
		settle # Wait before the acquisition.
		acquire
		end_delay
		"""

		expected = [
			Declaration({'type': 'int', 'variables': [
				Assignment({'target': 'placeholder', 'value': 0})]}),
			Declaration({'type': 'delay', 'variables': [
				Variable({'name': 'settle'}),
				Assignment({'target': 'end_delay', 'value': Quantity(10, 'ns')})]}),
			Declaration({'type': 'pulse', 'variables': [
				Variable({'name': 'first_square'}),
				Variable({'name': 'wobble'})]}),
			Declaration({'type': 'output', 'variables': [
				Variable({'name': 'f1'}),
				Variable({'name': 'f2'})]}),
			Assignment({'target': 'first_square',
				'value': Dictionary([
					DictionaryItem({'key': 'shape', 'value': 'square'}),
					DictionaryItem({'key': 'length', 'value': Quantity(1, 'ms')})])}),
			Assignment({
				'target': Attribute({'variable': 'wobble', 'name': 'length'}),
				'value': Quantity(50, 'us')}),
			Assignment({
				'target': Attribute({'variable': 'wobble', 'name': 'amplitude'}),
				'value': Quantity(-0.5, 'mV')}),
			Delay({'length': Quantity(10, 'us')}),
			ParallelPulses([
				Pulse({'sequence': PulseSequence(['first_square']), 'target': 'f1'}),
				Pulse({'sequence': PulseSequence([
					'wobble',
					Delay({'length': Quantity(+1e-3, 'us')}),
					'wobble']), 'target': 'f2'})]),
				Delay({'length': 'settle'}),
			Acquire(),
			Delay({'length': 'end_delay'}),
		]

		pp = parser.Parser()
		result = pp(prog)

		eq_(result, Block(expected))

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
			Loop({'times': 5, 'block': Block([
				Delay({'length': 'd1'}),
				ParallelPulses([
					Pulse({'sequence': PulseSequence(['p1']), 'target': 'f1'}),
					Pulse({'sequence': PulseSequence(['p2']), 'target': 'f2'})])])}),
			Loop({'times': 'M', 'block': Block([
				Delay({'length': 'd2'}),
				Loop({'times': 'N', 'block': Block([
					ParallelPulses([
						Pulse({'sequence': PulseSequence(['p2']), 'target': 'f1'}),
						Pulse({'sequence': PulseSequence(['p1']), 'target': 'f2'})])])})])}),
		]

		pp = parser.Parser()
		result = pp(prog)

		eq_(result, Block(expected))

	def testOneLine(self):
		"""
		Line breaks are optional.
		"""

		prog = 'int x=5;delay d1;;d1;d1;times x{d1;d1;};times x{d1}d1'

		expected = [
			Declaration({'type': 'int', 'variables': [
				Assignment({'target': 'x', 'value': 5})]}),
			Declaration({'type': 'delay', 'variables': [
				Variable({'name': 'd1'})]}),
			Delay({'length': 'd1'}),
			Delay({'length': 'd1'}),
			Loop({'times': 'x', 'block': Block([
				Delay({'length': 'd1'}),
				Delay({'length': 'd1'})])}),
			Loop({'times': 'x', 'block': Block([
				Delay({'length': 'd1'})])}),
			Delay({'length': 'd1'}),
		]

		pp = parser.Parser()
		result = pp(prog)

		eq_(result, Block(expected))

	def testFromFile(self):
		"""
		Parse an entire file.
		"""

		expected = [
			Declaration({'type': 'int', 'variables': [
				Assignment({'target': 'bumps', 'value': 2})]}),
			Declaration({'type': 'delay', 'variables': [
				Assignment({'target': 'bump_spacing', 'value': Quantity(10, 'ns')}),
				Variable({'name': 'settle'}),
				Assignment({'target': 'end_delay', 'value': Quantity(15, 'ns')})]}),
			Declaration({'type': 'pulse', 'variables': [
				Variable({'name': 'first_square'}),
				Variable({'name': 'wobble'})]}),
			Declaration({'type': 'pulse', 'variables': [
				Assignment({'target': 'last_square', 'value': Dictionary([
					DictionaryItem({'key': 'shape', 'value': 'square'})])})]}),
			Declaration({'type': 'pulse', 'variables': [
				Assignment({'target': 'manipulator', 'value': Dictionary([
					DictionaryItem({'key': 'shape', 'value': 'non-square'})])})]}),
			Declaration({'type': 'output', 'variables': [
				Variable({'name': 'f1'}),
				Variable({'name': 'f2'})]}),
			Assignment({'target': 'first_square', 'value': Dictionary([
				DictionaryItem({'key': 'shape', 'value': 'square'}),
				DictionaryItem({'key': 'length', 'value': Quantity(1, 'ns')})])}),
			Assignment({
				'target': Attribute({'variable': 'wobble', 'name': 'length'}),
				'value': Quantity(8, 'ns')}),
			Assignment({
				'target': Attribute({'variable': 'wobble', 'name': 'amplitude'}),
				'value': Quantity(-1, 'mV')}),
			Delay({'length': Quantity(10, 'ns')}),
			ParallelPulses([
				Pulse({'sequence': PulseSequence(['first_square']), 'target': 'f1'}),
				Pulse({'sequence': PulseSequence(['wobble']), 'target': 'f2'})]),
			Loop({'times': 'bumps', 'block': Block([
				Delay({'length': 'bump_spacing'}),
				Loop({'times': 2, 'block': Block([
					ParallelPulses([
						Pulse({'sequence': PulseSequence(['first_square']), 'target': 'f1'}),
						Pulse({'sequence': PulseSequence(['wobble']), 'target': 'f2'})])])})])}),
					Delay({'length': 'settle'}),
			Acquire(),
			ParallelPulses([
				Pulse({'sequence': PulseSequence(['last_square']), 'target': 'f1'}),
				Pulse({'sequence': PulseSequence(['manipulator', 'end_delay', 'manipulator']), 'target': 'f2'})]),
			Delay({'length': 'end_delay'}),
		]

		pp = parser.Parser()

		with open(path.join(resource_dir, '01.pulse')) as f:
			result = pp(''.join(f.readlines()))

		eq_(result, Block(expected))

	def testInvalid(self):
		"""
		Try the error detection.
		"""

		prog = [
			'int a b', 'int a = b = c', '5:f1', 'times {d1;d2}', 'd1;{d2}d3',
			'a = b', 'c.d = e.f', 'g.h', 'd1 (d2 d3):f1', 'refresh = d1:f5',
			'times 5 V {}', '100 units',
		]

		pp = parser.Parser()

		for line in prog:
			try:
				pp(line)
			except parser.PulseSyntaxError:
				pass
			else:
				assert False, 'Expected ParseException'


if __name__ == '__main__':
	main()
