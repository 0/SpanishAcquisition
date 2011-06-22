from nose.tools import eq_
import numpy
import unittest

from .. import group_iterators


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

	@staticmethod
	def tuples():
		"""
		Yield 10 nested tuples.
		"""

		for i in xrange(3):
			yield (i, ((i + 1, i + 2),), ((2 * i,),))

	def testEmpty(self):
		"""
		No iterables provided.
		"""

		p = group_iterators.ProductIterator([])

		eq_(list(p), [])

	def testParallel(self):
		"""
		Iterate in parallel.
		"""

		p = group_iterators.ParallelIterator([xrange(5), self.fib, numpy.linspace(1, 9, 5)])

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

	def testProduct(self):
		"""
		Iterate over the product.
		"""

		p = group_iterators.ProductIterator([xrange(2), numpy.linspace(1, 5, 3)])

		expected = [
			(0, 1),
			(0, 3),
			(0, 5),
			(1, 1),
			(1, 3),
			(1, 5),
		]

		eq_(list(p), expected)
		# Make sure it resets correctly.
		eq_(list(p), expected)

	def testChain(self):
		"""
		Iterate in a chain.
		"""

		c = group_iterators.ChainIterator([xrange(2), numpy.linspace(1, 5, 3)])

		expected = [(0,), (1,), (1,), (3,), (5,),]

		eq_(list(c), expected)
		# Make sure it resets correctly.
		eq_(list(c), expected)

	def testSingle(self):
		"""
		Wrapping one iterator for whatever reason.
		"""

		fs = [group_iterators.ParallelIterator, group_iterators.ProductIterator, group_iterators.ChainIterator]
		results = [f([xrange(5)]) for f in fs]
		expected = [(x,) for x in xrange(5)]

		eq_(list(results[0]), expected)
		eq_(list(results[1]), expected)
		eq_(list(results[2]), expected)

	def testWithTuples(self):
		"""
		The iterables should be able to dole out tuples with no issue.
		"""

		p = group_iterators.ParallelIterator([self.tuples, self.tuples])
		c = group_iterators.ChainIterator([p, p])

		expected = [
			(0, (1, 2), (0,), 0, (1, 2), (0,)),
			(1, (2, 3), (2,), 1, (2, 3), (2,)),
			(2, (3, 4), (4,), 2, (3, 4), (4,)),
		]
		expected += expected

		eq_(list(c), expected)

	def testAll(self):
		"""
		Iterate every way at the same time.
		"""

		p1 = group_iterators.ProductIterator([xrange(2), xrange(3)])
		p2 = group_iterators.ProductIterator([xrange(1, -1, -1), xrange(3, -1, -1)])
		p3 = group_iterators.ParallelIterator([p1, p2])
		c1 = group_iterators.ChainIterator([p3, p3])

		expected = [
			(0, 0, 1, 3),
			(0, 1, 1, 2),
			(0, 2, 1, 1),
			(1, 0, 1, 0),
			(1, 1, 0, 3),
			(1, 2, 0, 2),
		]
		expected += expected

		eq_(list(c1), expected)
		# Make sure it resets correctly.
		eq_(list(c1), expected)


if __name__ == '__main__':
	unittest.main()
