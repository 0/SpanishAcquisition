from pyparsing import (alphanums, alphas, delimitedList, nums, CaselessLiteral, Combine,
		Forward, Keyword, LineEnd, Literal, OneOrMore, Optional, ParseBaseException, ParseException,
		ParserElement, QuotedString, SkipTo, StringEnd, Suppress, Word, ZeroOrMore)

from ..units import Quantity
from .tool.box import find_location, format_error
from .tree import (Acquire, Assignment, Attribute, Block, Declaration, Delay, Dictionary,
		DictionaryItem, Loop, ParallelPulses, Pulse, PulseSequence, Variable)

"""
A parser for pulse programs.
"""


class PulseError(Exception):
	"""
	A problem with the pulse program.
	"""

	pass

class PulseSyntaxError(PulseError):
	"""
	Could not parse pulse program.
	"""

	pass


def read_quantity(s, loc, toks):
	"""
	Attempt to create a Quantity object.
	"""

	try:
		return Quantity(toks[0], toks[1])
	except ValueError as e:
		raise ParseException(s, loc, e)


def Parser(raw=False):
	"""
	Create a pulse program parser.

	If raw is True, returns the pyparsing parser object.
	Otherwise, returns a function which takes a string and returns an AST.
	"""

	old_whitespace = ParserElement.DEFAULT_WHITE_CHARS

	try:
		# Handle line breaks manually.
		ParserElement.setDefaultWhitespaceChars(ParserElement.DEFAULT_WHITE_CHARS.replace('\n', ''))

		# Keywords.
		## Types.
		DELAY, INT, OUTPUT, PULSE = Keyword('delay'), Keyword('int'), Keyword('output'), Keyword('pulse')

		## Syntax.
		ACQUIRE = Keyword('acquire').suppress().setName('acquire')
		TERMINATOR = (LineEnd() | ';').suppress().setName('terminator')
		TIMES = Keyword('times').suppress().setName('times')

		# Values.
		identifier = Word(alphas + '_', alphanums + '_')
		identifier.setName('identifier')

		## Numbers.
		### Integer.
		unparsed_inum = Word('+-' + nums, nums)
		inum = unparsed_inum.copy().setParseAction(lambda x: int(x[0]))
		inum.setName('inum')

		### Floating point.
		dot = Literal('.')
		e = CaselessLiteral('e')

		fractional_part = dot + Word(nums, nums)
		exponent_part = e + inum

		fnum = Combine(unparsed_inum + (fractional_part + Optional(exponent_part) | exponent_part))
		fnum.setParseAction(lambda x: float(x[0]))
		fnum.setName('fnum')

		number = fnum | inum

		## Quantities.
		# Unit symbol cannot start with "e".
		unit_symbol = Combine(Word(alphas.replace('E', '').replace('e', ''), alphas) + Optional(Word(nums)))
		unit_symbols = delimitedList(unit_symbol, delim='.', combine=True)
		quantity = (number + unit_symbols).setParseAction(read_quantity)
		quantity.setName('quantity')

		## Strings.
		string = QuotedString(r'"', escChar=r'\\') | QuotedString(r"'", escChar=r'\\')

		value = quantity | number | string

		## Dictionaries.
		dictionary_item = (identifier('key') + Suppress(':') + value('value')).setParseAction(DictionaryItem)
		dictionary = Suppress('{') + Optional(delimitedList(dictionary_item)) + Suppress('}')
		dictionary.setParseAction(Dictionary)

		# Variables.
		type = DELAY | INT | OUTPUT | PULSE

		attribute = (identifier('variable') + Suppress('.') - identifier('name')).setParseAction(Attribute)

		identifier_assignment = identifier('target') + Suppress('=') - (dictionary | value)('value')
		identifier_assignment.setName('identifier_assignment')

		attribute_assignment = attribute('target') + Suppress('=') - (value)('value')
		attribute_assignment.setName('attribute_assignment')

		assignment = (identifier_assignment | attribute_assignment).setParseAction(Assignment)

		declaration_list = delimitedList(assignment | identifier('name').setParseAction(Variable))
		declaration = (type('type') + declaration_list('variables')).setParseAction(Declaration)

		# Commands.
		## Acquire.
		acquire = ACQUIRE.setParseAction(Acquire)

		## Delay.
		delay = (quantity | identifier)('length').setParseAction(Delay)

		## Pulse.
		pulse_sequence = (Suppress('(') + OneOrMore(identifier | delay) + Suppress(')')) | identifier
		pulse_sequence.setParseAction(PulseSequence)
		pulse = (pulse_sequence('sequence') + Suppress(':') + identifier('target')).setParseAction(Pulse)
		pulses = OneOrMore(pulse).setParseAction(ParallelPulses)

		command = acquire | pulses | delay

		# Blocks.
		block = Forward().setParseAction(Block)
		loop_block = (TIMES + (identifier | inum)('times') + block('block')).setParseAction(Loop)

		# Statements.
		statement = Optional(assignment | declaration | command)
		# The last statement does not require a terminator.
		statements = ZeroOrMore(loop_block | statement + TERMINATOR) + statement

		block << (Suppress('{') + statements + Suppress('}'))

		parser = (statements + StringEnd().suppress()).setParseAction(Block)

		# Comments.
		comment = Literal('#') + SkipTo(LineEnd())
		parser.ignore(comment)

		if raw:
			return parser
		else:
			def parseString(s):
				s = s.expandtabs()

				try:
					return parser.parseString(s)[0]
				except ParseBaseException as e:
					raise PulseSyntaxError([format_error(e.msg, *find_location(s, e.loc))])

			return parseString
	finally:
		ParserElement.setDefaultWhitespaceChars(old_whitespace)
