import itertools
from nose.tools import eq_
import unittest

from spacq.interface.units import IncompatibleDimensions

from .. import variables


class ChangeIndicatorTest(unittest.TestCase):
	def testSample(self):
		"""
		Ensure that the first few values differ from their neighbours.
		"""

		indicator = variables.change_indicator()
		last = None

		for i in itertools.izip(indicator, xrange(1000)):
			if last is not None:
				assert i != last, 'Values are equal: {0}, {1}'.format(i, last)

			last = i


class CombineVariablesTest(unittest.TestCase):
	@classmethod
	def extract(cls, values):
		"""
		Given a tuple of (value, change indicator, ...) pairs, extract the values.
		"""

		return tuple(values[::2])

	@classmethod
	def list_extract(cls, values):
		"""
		Run extract over the list.
		"""

		return [cls.extract(x) for x in values]

	def testEmpty(self):
		"""
		Use no variables.
		"""

		iterator, last, num_items, sorted_variables = variables.combine_variables([])
		eq_(self.list_extract(list(iterator)), [])
		eq_(self.extract(last), ())
		eq_(num_items, 0)
		eq_(sorted_variables, [])

	def testSingle(self):
		"""
		Use a single variable.
		"""

		var = variables.LinSpaceVariable(-5.0, 5.0, 11,
				name='Name', order=0, enabled=True, const=60.0)

		expected = [(x,) for x in range(-5, 6)]

		iterator, last, num_items, sorted_variables = variables.combine_variables([var])
		eq_(self.list_extract(list(iterator)), expected)
		eq_(self.extract(last), (60.0,))
		eq_(num_items, len(expected))
		eq_([x.name for x in sorted_variables], ['Name'])

	def testMultiple(self):
		"""
		Use many variables.
		"""

		vars = [
			variables.LinSpaceVariable(1.0, 5.0, 3,
					name='A', order=3, enabled=True),
			variables.LinSpaceVariable(11.0, 12.0, 2,
					name='B', order=2, enabled=True, const=10.0),
			variables.LinSpaceVariable(-99.0, 0.0,
					name='D', order=1, enabled=True, const=9.0, use_const=True),
			variables.LinSpaceVariable(21.0, 25.0, 2,
					name='C', order=2, enabled=True),
			variables.LinSpaceVariable(0.0, 0.0, 1,
					name='E', order=4),
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
		eq_(self.list_extract(list(iterator)), expected)
		eq_(self.extract(last), (0.0, 10.0, 0.0, 9.0))
		eq_(num_items, len(expected))

		for var, name in zip(sorted_variables, 'ABCD'):
			eq_(var.name, name)


class LinSpaceVariableTest(unittest.TestCase):
	def testIterator(self):
		"""
		Create an iterator from a variable.
		"""

		var = variables.LinSpaceVariable(-1.0, -3.0, 5,
				name='Name', order=1, enabled=True, const=10.0)

		# Non-const.
		it1 = var.to_iterator()
		eq_(list(it1), [-1.0, -1.5, -2.0, -2.5, -3.0])

		# Const.
		var.use_const = True

		it2 = var.to_iterator()
		eq_(list(it2), [10.0])

	def testAdjust(self):
		"""
		Try to adjust the values after initialization.
		"""

		var = variables.LinSpaceVariable(name='Name', order=1)

		var.steps = 1000
		eq_(var.steps, 1000)

		try:
			var.steps = -1
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		var.wait = '100 ms'
		eq_(var.wait, '100 ms')

		try:
			var.wait = '100 Hz'
		except IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'


if __name__ == '__main__':
	unittest.main()
