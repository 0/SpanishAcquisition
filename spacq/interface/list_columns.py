from pyparsing import (delimitedList, ParseBaseException, Regex, Suppress)
from re import IGNORECASE

"""
Tools for parsing list columns on import.
"""


def ListParser():
	"""
	A parser for list columns, where each list is composed of pairs of values.
	"""

	value = Regex(r'[-+]?[0-9]+(?:\.[0-9]*)?(?:e[-+]?[0-9]+)?', IGNORECASE)
	value.setParseAction(lambda toks: float(toks[0]))

	item = Suppress('(') + value + Suppress(',') + value + Suppress(')')
	item.setParseAction(tuple)

	lst = Suppress('[') + delimitedList(item) + Suppress(']')
	lst.setParseAction(list)

	def parse(s):
		try:
			return lst.parseString(s).asList()
		except ParseBaseException as e:
			raise ValueError(e)

	return parse
