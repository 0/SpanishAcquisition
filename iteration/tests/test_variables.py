from nose.tools import eq_
import unittest

from iteration import variables


class testGroup(unittest.TestCase):
	def testEmpty(self):
		"""
		Use no variables.
		"""

		iterator, last, num_items, sorted_variables = variables.combine_variables([])
		eq_(list(iterator), [])
		eq_(last, ())
		eq_(num_items, 0)
		eq_(sorted_variables, [])

	def testSingle(self):
		"""
		Use a single variable.
		"""

		var = variables.Variable('Name', 0, -5.0, 5.0, 11, const=6.0)

		expected = [(x,) for x in range(-5, 6)]

		iterator, last, num_items, sorted_variables = variables.combine_variables([var])
		eq_(list(iterator), expected)
		eq_(last, (6.0,))
		eq_(num_items, len(expected))
		eq_([x.name for x in sorted_variables], ['Name'])

	def testMultiple(self):
		"""
		Use many variables.
		"""

		vars = [
			variables.Variable('A', 1, 1.0, 5.0, 3),
			variables.Variable('B', 2, 11.0, 12.0, 2, const=10.0),
			variables.Variable('D', 3, -99.0, 0.0, const=9.0, enabled=False),
			variables.Variable('C', 2, 21.0, 25.0, 2),
		]

		expected = [
			(1.0, 11.0, 21.0, 9.0),
			(1.0, 12.0, 25.0, 9.0),
			(3.0, 11.0, 21.0, 9.0),
			(3.0, 12.0, 25.0, 9.0),
			(5.0, 11.0, 21.0, 9.0),
			(5.0, 12.0, 25.0, 9.0),
		]

		iterator, last, num_items, sorted_variables = variables.combine_variables(vars)
		eq_(list(iterator), expected)
		eq_(last, (1.0, 10.0, 21.0, 9.0))
		eq_(num_items, len(expected))

		for var, name in zip(sorted_variables, 'ABCD'):
			eq_(var.name, name)


class testVariable(unittest.TestCase):
	def testIterator(self):
		"""
		Create an iterator from a variable.
		"""

		var = variables.Variable('Name', 1, -1.0, -3.0, 5, const=10.0)

		# Enabled.
		it1 = var.to_iterator()
		eq_(list(it1), [-1.0, -1.5, -2.0, -2.5, -3.0])

		# Disabled.
		var.enabled = False

		it2 = var.to_iterator()
		eq_(list(it2), [10.0])


if __name__ == '__main__':
	unittest.main()
