import itertools

"""
Ways of grouping iterators.
"""


class GroupIterator(object):
	"""
	Step over iterators in groups.
	"""

	@staticmethod
	def flatten(value):
		"""
		Remove one layer of nesting from each item.

		This allows for auto-flattened nested GroupIterators.
		"""

		if not isinstance(value, tuple):
			return (value,)

		result = []

		for x in value:
			if isinstance(x, tuple):
				result.extend(x)
			else:
				result.append(x)

		return tuple(result)

	def __init__(self, iterables):
		if iterables:
			self.iterables = iterables
		else:
			# We'll just raise StopIteration on the first next().
			self.iterables = [[]]

	def make_iterator(self, obj):
		if callable(obj):
			# Assume it's a generator.
			return obj()
		else:
			# Assume it's an iterable.
			return iter(obj)

	def make_iterators(self):
		return [self.make_iterator(i) for i in self.iterables]

	def iterate_with(self, f):
		"""
		Combine all the iterables into a single iterator using the function.
		"""

		return (self.flatten(x) for x in f(*self.make_iterators()))


class ParallelIterator(GroupIterator):
	"""
	Step over the iterables at the same time.

	>>> list(ParallelIterator([xrange(3), xrange(0, 6, 2)]))
	[(0, 0), (1, 2), (2, 4)]

	Iteration stops when any single iterable runs out.
	"""

	def __iter__(self):
		return self.iterate_with(itertools.izip)


class ProductIterator(GroupIterator):
	"""
	Step over the Cartesian product of the iterables.

	>>> list(ProductIterator([xrange(2), xrange(0, 4, 2)]))
	[(0, 0), (0, 2), (1, 0), (1, 2)]

	Iteration never stops if any single iterable is infinite.
	"""

	def __iter__(self):
		return self.iterate_with(itertools.product)


class ChainIterator(GroupIterator):
	"""
	Step over the iterables sequentially.

	>>> list(box.ChainIterator([xrange(3), xrange(3, 6)]))
	[(0,), (1,), (2,), (3,), (4,), (5,)]

	Iteration never stops if any single iterable is infinite.
	"""

	def __iter__(self):
		return self.iterate_with(itertools.chain)


if __name__ == '__main__':
	import unittest

	from tests import test_group_iterators as my_tests

	unittest.main(module=my_tests)
