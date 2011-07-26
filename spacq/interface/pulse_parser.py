from pyparsing import (alphanums, alphas, delimitedList, nums, CaselessLiteral, Combine,
		Forward, Keyword, LineEnd, Literal, OneOrMore, Optional, ParserElement, QuotedString,
		SkipTo, StringEnd, Suppress, Word, ZeroOrMore)

"""
A parser for pulse programs.
"""


class Node(object):
	def __init__(self, name):
		self.name = name

	def __call__(self, tokens):
		return (self.name, tokens.asList())


def Parser():
	old_whitespace = ParserElement.DEFAULT_WHITE_CHARS

	try:
		# Handle line breaks manually.
		ParserElement.setDefaultWhitespaceChars(ParserElement.DEFAULT_WHITE_CHARS.replace('\n', ''))

		# Keywords.
		## Types.
		DELAY, INT, OUTPUT, PULSE = Keyword('delay'), Keyword('int'), Keyword('output'), Keyword('pulse')

		## Syntax.
		ACQUIRE = Keyword('acquire').suppress()
		TERMINATOR = (LineEnd() | ';').suppress()
		TIMES = Keyword('times').suppress()

		# Values.
		identifier = Word(alphas + '_', alphanums + '_')

		## Numbers.
		### Integer.
		inum = Word('+-' + nums, nums).setParseAction(lambda x: int(x[0]))

		### Floating point.
		dot = Literal('.')
		e = CaselessLiteral('e')

		fractional_part = dot + Word(nums, nums)
		exponent_part = e + inum

		fnum = Combine(inum + (fractional_part + Optional(exponent_part) | exponent_part))
		fnum.setParseAction(lambda x: float(x[0]))

		number = fnum | inum

		## Quantities.
		# Unit symbol cannot start with "e".
		unit_symbol = Combine(Word(alphas.replace('E', '').replace('e', ''), alphas) + Optional(Word(nums)))
		unit_symbols = delimitedList(unit_symbol, delim='.', combine=True)
		quantity = (number + unit_symbols).setParseAction(Node('Quantity'))

		## Strings.
		string = QuotedString(r'"', escChar=r'\\') | QuotedString(r"'", escChar=r'\\')

		value = quantity | number | string

		## Dictionaries.
		dictionary_item = (identifier + Suppress(':') + value).setParseAction(Node('DictionaryItem'))
		dictionary = Suppress('{') + Optional(delimitedList(dictionary_item)) + Suppress('}')
		dictionary.setParseAction(Node('Dictionary'))

		# Variables.
		type = DELAY | INT | OUTPUT | PULSE

		attribute = (identifier + Suppress('.') + identifier).setParseAction(Node('Attribute'))

		identifier_assignment = identifier + Suppress('=') + (dictionary | identifier | value)
		attribute_assignment = attribute + Suppress('=') + (attribute | value)
		assignment = (identifier_assignment | attribute_assignment).setParseAction(Node('Assignment'))

		declaration_list = delimitedList(assignment | identifier.copy().setParseAction(Node('Variable')))
		declaration = (type + declaration_list).setParseAction(Node('Declaration'))

		# Commands.
		## Acquire.
		acquire = ACQUIRE.setParseAction(Node('Acquire'))

		## Delay.
		delay = (quantity | identifier).setParseAction(Node('Delay'))

		## Pulse.
		pulse_sequence = (Suppress('(') + OneOrMore(identifier | delay) + Suppress(')')) | identifier
		pulse_sequence.setParseAction(Node('PulseSequence'))
		pulse = (pulse_sequence + Suppress(':') + identifier).setParseAction(Node('Pulse'))
		pulses = OneOrMore(pulse).setParseAction(Node('ParallelPulses'))

		command = acquire | pulses | delay

		# Blocks.
		block = Forward().setParseAction(Node('Block'))
		loop_block = (TIMES + (identifier | inum) + block).setParseAction(Node('Loop'))

		# Statements.
		statement = Optional(assignment | declaration | command)
		# The last statement does not require a terminator.
		statements = ZeroOrMore(loop_block | statement + TERMINATOR) + statement

		block << (Suppress('{') + statements + Suppress('}'))

		parser = statements + StringEnd()

		# Comments.
		comment = Literal('#') + SkipTo(LineEnd())
		parser.ignore(comment)

		return parser
	finally:
		ParserElement.setDefaultWhitespaceChars(old_whitespace)
