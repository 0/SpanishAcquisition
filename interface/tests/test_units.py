from nose.tools import eq_
import unittest

from interface import units


class SIValuesTest(unittest.TestCase):
	def testAllUnits(self):
		"""
		Verify that each dimension has exactly one associated unit.
		"""

		eq_(len(units.SIValues.dimensions), len(units.SIValues.units))

		for dim in units.SIValues.dimensions:
			assert dim in units.SIValues.units_


class QuantityTest(unittest.TestCase):
	data = [
		(0, units.SIValues.dimensions.time),
		(1, units.SIValues.dimensions.time),
		(10, units.SIValues.dimensions.time),
		(0.5, units.SIValues.dimensions.frequency),
		(123456789, units.SIValues.dimensions.frequency),
	]

	def testSimple(self):
		"""
		Some simple quantities.
		"""

		for value, dimension in self.data:
			q = units.Quantity(value, dimension)

			eq_(q.value, value)
			eq_(q.dimension, dimension)

	def testFromString(self):
		"""
		Check string parsing.
		"""

		data = [
			('0 s', 0, units.SIValues.dimensions.time),
			('500 ms', 500 * 1e-3, units.SIValues.dimensions.time),
			('10 Hz', 10 * 1e0, units.SIValues.dimensions.frequency),
			('123456789 ns', 123456789 * 1e-9, units.SIValues.dimensions.time),
			('987654321 GHz', 987654321 * 1e9, units.SIValues.dimensions.frequency),
			# Various whitespace.
			('5s', 5 * 1e0, units.SIValues.dimensions.time),
			(' \t 123454321 \t   uHz  \t  ', 123454321 * 1e-6, units.SIValues.dimensions.frequency),
		]

		for string, value, dimension in data:
			q = units.Quantity(value, dimension)

			eq_(units.Quantity.from_string(string), q)

	def testBadFromString(self):
		"""
		Invalid strings pretending to be quantities.
		"""

		data = [
			'', '0', 's', '0seconds', '0 something', '1234 anything', 's 0',
		]

		for string in data:
			try:
				print units.Quantity.from_string(string)
			except ValueError:
				pass
			else:
				assert False, 'Expected ValueError for "{0}".'.format(string)

	def testComparison(self):
		"""
		Check that comparison works.
		"""

		time = units.SIValues.dimensions.time
		frequency = units.SIValues.dimensions.frequency

		assert units.Quantity(1, time) == units.Quantity(1, time)
		assert units.Quantity(1, time) < units.Quantity(2, time)
		assert units.Quantity(5.5, time) >= units.Quantity(5.5, time)
		assert units.Quantity(5.5, time) != units.Quantity(5.4, time)

		try:
			units.Quantity(1, time) == units.Quantity(1, frequency)
		except units.IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'

		try:
			units.Quantity(1, time) <= units.Quantity(1, frequency)
		except units.IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'

	def testRepr(self):
		"""
		Ensure that repr() gives a useful value.
		"""

		# For eval().
		Quantity = units.Quantity
		SIValues = units.SIValues

		for value, dimension in self.data:
			q = units.Quantity(value, dimension)

			eq_(eval(repr(q)), q)

	def testStr(self):
		"""
		Ensure that str() gives a meaningful value.
		"""

		for value, dimension in self.data:
			q = units.Quantity(value, dimension)

			eq_(units.Quantity.from_string(str(q)), q)

		# Zero is a special case.
		zero = units.Quantity(0, units.SIValues.dimensions.time)
		eq_(str(zero), '0 s')

	def testStrKeepPrefix(self):
		"""
		Optionally keep the orignal prefix for str().
		"""

		# No prefix to keep.
		q1 = units.Quantity(1234, units.SIValues.dimensions.time)
		eq_(str(q1), '1.234 ks')

		# Kept prefix.
		q2 = units.Quantity.from_string('1234 ns')
		eq_(str(q2), '1234 ns')

		# Cleared prefix.
		q3 = units.Quantity.from_string('1234 ns')
		q3.original_prefix = None
		eq_(str(q3), '1.234 us')


if __name__ == '__main__':
	unittest.main()
