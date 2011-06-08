from nose.tools import eq_
import numpy
import unittest

from tool import box


class EnumTest(unittest.TestCase):
	def testEmpty(self):
		"""
		A useless object.
		"""

		e = box.Enum()

		try:
			e.anything
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'

		eq_(len(e), 0)

	def testNotEmpty(self):
		"""
		A regular enum.
		"""

		values = ['cow', 'moon', 'dish', 'spoon']

		e = box.Enum(values)

		eq_(len(e), len(values))

		for v in values:
			eq_(getattr(e, v), v)

		e.cow, e.moon, e.dish, e.spoon

		try:
			e.diddle
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'

	def testDuplicates(self):
		"""
		Check uniqueness and equality testing.
		"""

		e = box.Enum(['a'] * 100 + ['b'] * 50)
		f = box.Enum(['b', 'a'])

		eq_(e, f)


class IteratorTest(unittest.TestCase):
	@staticmethod
	def fib():
		"""
		Infinite sequence generator.
		"""

		a, b = 0, 1

		while True:
			a, b = b, a + b

			yield a

	def testParallel(self):
		"""
		Iterate in parallel.
		"""

		# Empty.
		try:
			box.ParallelIterator([])
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		# Non-empty.
		p = box.ParallelIterator([xrange(5), self.fib, numpy.linspace(1, 9, 5)])

		expected = [
			(0, 1, 1),
			(1, 1, 3),
			(2, 2, 5),
			(3, 3, 7),
			(4, 5, 9),
		]

		eq_(list(p), expected)
		# Make sure it resets correctly.
		eq_(list(p), expected)

	def testSerial(self):
		"""
		Iterate serially.
		"""

		# Empty.
		try:
			box.SerialIterator([])
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		# Non-empty.
		s = box.SerialIterator([xrange(2), numpy.linspace(1, 5, 3)])

		expected = [
			(0, 1),
			(0, 3),
			(0, 5),
			(1, 1),
			(1, 3),
			(1, 5),
		]

		eq_(list(s), expected)
		# Make sure it resets correctly.
		eq_(list(s), expected)

	def testSingle(self):
		"""
		Wrapping one iterator for whatever reason.
		"""

		s = box.SerialIterator([xrange(5)])
		p = box.ParallelIterator([xrange(5)])

		expected = [(x,) for x in xrange(5)]

		eq_(list(s), expected)
		eq_(list(p), expected)

	def testBoth(self):
		"""
		Iterate every way at the same time.
		"""

		s1 = box.SerialIterator([xrange(2), xrange(3)])
		s2 = box.SerialIterator([xrange(1, -1, -1), xrange(3, -1, -1)])
		p = box.ParallelIterator([s1, s2])

		expected = [
			(0, 0, 1, 3),
			(0, 1, 1, 2),
			(0, 2, 1, 1),
			(1, 0, 1, 0),
			(1, 1, 0, 3),
			(1, 2, 0, 2),
		]

		eq_(list(p), expected)
		# Make sure it resets correctly.
		eq_(list(p), expected)
