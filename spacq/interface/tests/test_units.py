from copy import deepcopy
from nose.tools import assert_raises, eq_
from unittest import main, TestCase

from .. import units


class QuantityTest(TestCase):
	# String value, value, units, multiplier, proper string value.
	data = [
		# Straightforward.
		('-1 s', -1, 's', 0, None),
		('0 s', 0, 's', 0, None),
		('1e0 s', 1, 's', 0, '1 s'),
		# Multiple units.
		('10 A.m', 10, 'A.m', 0, None),
		('0.5 GJ.Hz.cd', 0.5, 'GJ.Hz.cd', 9, None),
		('500 kg.ms-1', 500, 'kg.ms-1', -3, None),
		('-1234567890123 m.s-2', -1234567890123, 'm.s-2', 0, '-1.23456789e+12 m.s-2'),
		# Large & small.
		('3e40 nA', 3e40, 'nA', -9, '3e+40 nA'),
		('-3e40 mA', -3e40, 'mA', -3, '-3e+40 mA'),
		('7e-40 GA', 7e-40, 'GA', 9, None),
		('-7e-40 uA', -7e-40, 'uA', -6, None),
		# Various whitespace.
		('5s', 5, 's', 0, '5 s'),
		('5s . Hz\t2 ', 5, 's.Hz2', 0, '5 s.Hz2'),
		(' \t 123454321 \t   uHz  \t  ', 123454321, 'uHz', -6, '123454321 uHz'),
	]

	def testSimple(self):
		"""
		Some simple quantities.
		"""

		for string, value, orig_units, multiplier, _ in self.data:
			q = units.Quantity(string)

			eq_(q, units.Quantity(value, orig_units))
			eq_(q.value, value * 10 ** multiplier)
			eq_(q.original_value, value)

	def testBadStrings(self):
		"""
		Invalid strings pretending to be quantities.
		"""

		data = [
			'', '0', 's', '0seconds', '0 something', '1234 anything', 's 0',
		]

		for string in data:
			assert_raises(ValueError, units.Quantity, string)

	def testMismatchedUnits(self):
		"""
		Values should be comparable as long as they have the same dimensions.
		"""

		qs = [
			units.Quantity(1, 'GJ.s'),
			units.Quantity(1e9, 'J.Hz-1'),
			units.Quantity(1, 'Tg.m2.s-1'),
			units.Quantity(1, 'kg.Gm.m.Hz'),
			units.Quantity(1000, 'Gg.m2.s.Hz2'),
		]

		for q in qs:
			eq_(q, qs[0])

	def testAmbiguousUnit(self):
		"""
		This shouldn't happen, but let's make sure it works.
		"""

		# Ensure it works normally.
		units.Quantity(5, 'ps')

		# Insert fake unit.
		assert 'ps' not in units.SIValues.units
		units.SIValues.units.add('ps')

		try:
			assert_raises(ValueError, units.Quantity, 5, 'ps')
		finally:
			units.SIValues.units.remove('ps')

	def testAssertDimensions(self):
		"""
		Ensure that dimensions are asserted correctly.
		"""

		q = units.Quantity(5, 's')

		# No exception.
		assert q.assert_dimensions('s', exception=False)
		assert not q.assert_dimensions('N.m', exception=False)
		assert q.assert_dimensions(q, exception=False)

		# Exception.
		assert q.assert_dimensions('s')
		assert_raises(units.IncompatibleDimensions, q.assert_dimensions, 'A')
		assert_raises(units.IncompatibleDimensions, eq_, units.Quantity(1, 's'), units.Quantity(1, 'm'))

	def testComparison(self):
		"""
		Check that comparison works.
		"""

		assert units.Quantity(1, 's.m') == units.Quantity(1, 'm.s')
		assert units.Quantity(1, 'm.s-1') < units.Quantity(2, 's-1.m')
		assert units.Quantity(5.5, 's') >= units.Quantity(5.5, 's')
		assert units.Quantity(5.5, 's') != units.Quantity(5.4, 's')

		try:
			units.Quantity(1, 's') > units.Quantity(1, 's2')
		except units.IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'

		try:
			units.Quantity(1, 's') <= units.Quantity(1, 'Hz')
		except units.IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'

		try:
			1 == units.Quantity(1, 's')
		except TypeError:
			pass
		else:
			assert False, 'Expected TypeError'

		try:
			1 <= units.Quantity(1, 's')
		except TypeError:
			pass
		else:
			assert False, 'Expected TypeError'

	def testArithmetic(self):
		"""
		Perform arithmetic on quantities.
		"""

		# Absolute value.
		q1 = units.Quantity(123, 'T')
		q2 = units.Quantity(0, 'T')
		q3 = units.Quantity(-123, 'T')

		eq_(abs(q1), q1)
		eq_(abs(q2), q2)
		eq_(abs(q3), q1)

		# Addition & subtraction.
		## Matching units.
		q1 = units.Quantity(5, 's')
		q2 = units.Quantity(-4, 'ms')
		q3 = units.Quantity(4.996, 's')
		q4 = units.Quantity(5.004, 's')

		eq_(q1 + q2, q3)
		eq_(q1 - q2, q4)

		## Non-matching units.
		q2 = units.Quantity(-4, 'mHz')

		try:
			q1 + q2
		except units.IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions'

		try:
			q1 - q2
		except units.IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions'

		try:
			units.Quantity(1, 's') + 1
		except TypeError:
			pass
		else:
			assert False, 'Expected TypeError'

		try:
			units.Quantity(1, 's') - 1
		except TypeError:
			pass
		else:
			assert False, 'Expected TypeError'

		# Multiplication by real.
		q = units.Quantity(1.5, 'N.m')

		q_mul = 2 * q
		q_mul = q_mul * 3

		eq_(q, units.Quantity(1.5, 'J'))
		eq_(q_mul, units.Quantity(9, 'J'))

		# Division by real.
		q = units.Quantity(-1.5, 'N.m')

		q_mul = q / -3

		eq_(q, units.Quantity(-1.5, 'J'))
		eq_(q_mul, units.Quantity(0.5, 'J'))

	def testRepr(self):
		"""
		Ensure that repr() gives a useful value.
		"""

		# For eval().
		Quantity = units.Quantity

		for _, value, orig_units, _, _ in self.data:
			q = units.Quantity(value, orig_units)

			eq_(eval(repr(q)), q)

	def testStr(self):
		"""
		Ensure that str() gives a meaningful value.
		"""

		for string, value, orig_units, _, proper_string in self.data:
			if proper_string is None:
				proper_string = string

			q = units.Quantity(value, orig_units)

			eq_(str(q), proper_string)

	def testDeepCopy(self):
		"""
		"""

		q = units.Quantity('100 ns.V2')

		eq_(deepcopy(q), units.Quantity('100 ns.V2'))


if __name__ == '__main__':
	main()
