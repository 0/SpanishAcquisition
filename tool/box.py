import itertools

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

		result = []

		for x in value:
			if isinstance(x, tuple):
				result.extend(x)
			else:
				result.append(x)

		return tuple(result)

	def __init__(self, iterables, *args, **kwargs):
		if not iterables:
			raise ValueError('No iterables provided.')

		self.iterables = iterables

	def _make_iterator(self, obj):
		if callable(obj):
			# Assume it's a generator.
			return obj()
		else:
			# Assume it's an iterable.
			return iter(obj)

	def _make_iterators(self):
		return [self._make_iterator(i) for i in self.iterables]

	def iterate_with(self, f):
		"""
		Combine all the iterables into a single iterator using the function.
		"""

		return (self.flatten(x) for x in f(*self._make_iterators()))


class ParallelIterator(GroupIterator):
	"""
	Step over the iterators at the same time.

	Iteration stops when any single one runs out.
	"""

	def __iter__(self):
		return self.iterate_with(itertools.izip)


class SerialIterator(GroupIterator):
	"""
	Step over the iterators sequentially, a la Cartesian product.

	Iteration never stops if any single one is infinite.
	"""

	def __iter__(self):
		return self.iterate_with(itertools.product)


if __name__ == '__main__':
	import unittest

	from tests import test_box as my_tests

	unittest.main(module=my_tests)
