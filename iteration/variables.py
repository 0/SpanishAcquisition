import itertools
import numpy
import operator

from interface.units import IncompatibleDimensions, SIValues, Quantity
from iteration.group_iterators import ChainIterator, ParallelIterator, ProductIterator


def combine_variables(variables):
	"""
	Create a GroupIterator out of some Variables.

	The returned values are:
		iterator
		tuple of constant values
		number of items in the iterator
		variables sorted by their order in the tuples
	"""

	if not variables:
		return ([], (), 0, [])

	order_attr = operator.attrgetter('order')
	ordered = sorted(variables, key=order_attr)
	grouped = ((order, list(vars)) for order, vars in itertools.groupby(ordered, order_attr))

	iterators = []
	num_items = 1
	sorted_variables = []
	# Treat each order to its own parallel iterator.
	for _, vars in grouped:
		var_iter = ParallelIterator([x.to_iterator() for x in vars])
		var_items = sum(1 for _ in var_iter)

		iterators.append(var_iter)
		num_items *= var_items
		sorted_variables.extend(vars)

	# This shouldn't be possible, but just in case.
	if num_items <= 0:
		return None

	iterator = ProductIterator(iterators)
	last_values = tuple(x.const for x in sorted_variables)

	return (iterator, last_values, num_items, sorted_variables)


class Variable(object):
	"""
	A simple linear space variable.
	"""

	def __init__(self, name, order, initial=0.0, final=0.0, steps=1, enabled=True,
			wait=0, const=None, resource_name=''):
		"""
		name: A string labelling the variable.
		order: The integer nesting order.
		"""

		self.name = name
		self.order = order

		# Linear space parameters.
		self.initial = initial
		self.final = final
		self._steps = steps

		# Iteration parameters.
		self.enabled = enabled
		self._wait = Quantity(wait, SIValues.dimensions.time)
		if const is not None:
			self.const = const
		else:
			self.const = initial

		self.resource_name = resource_name

	@property
	def steps(self):
		return self._steps

	@steps.setter
	def steps(self, value):
		if value <= 0:
			raise ValueError('Number of steps must be positive, not "{0}".'.format(value))

		self._steps = value

	@property
	def wait(self):
		return str(self._wait)

	@wait.setter
	def wait(self, value):
		wait = Quantity.from_string(value)

		if wait.dimension != SIValues.dimensions.time:
			raise IncompatibleDimensions(wait.dimensions, SIValues.dimensions.time)

		self._wait = wait

	def to_iterator(self):
		"""
		Create an iterator for the variable.
		"""

		if self.enabled:
			return numpy.linspace(self.initial, self.final, self.steps)
		else:
			return [self.const]


if __name__ == '__main__':
	import unittest

	from tests import test_variables as my_tests

	unittest.main(module=my_tests)
