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
			('500 ms', 500 * 1e-3, units.SIValues.dimensions.time),
			('10 Hz', 10 * 1e0, units.SIValues.dimensions.frequency),
			('123456789 ns', 123456789 * 1e-9, units.SIValues.dimensions.time),
			('987654321 GHz', 987654321 * 1e9, units.SIValues.dimensions.frequency),
		]

		for string, value, dimension in data:
			q = units.Quantity(value, dimension)

			eq_(units.Quantity.from_string(string), q)

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

		# For eval()
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
