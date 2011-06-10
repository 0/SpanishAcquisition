"""
Generic tools.
"""


class Enum(set):
	"""
	An enumerated type.

	>>> e = Enum(['a', 'b', 'c'])
	>>> e.a
	'a'
	>>> e.d
	...
	AttributeError: 'Enum' object has no attribute 'd'
	"""

	def __getattribute__(self, name):
		if name in self:
			return name
		else:
			return set.__getattribute__(self, name)


if __name__ == '__main__':
	import unittest

	from tests import test_box as my_tests

	unittest.main(module=my_tests)
