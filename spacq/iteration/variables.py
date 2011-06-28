import itertools
import numpy
import operator

from spacq.interface.units import SIValues, Quantity

from .group_iterators import ChainIterator, ParallelIterator, ProductIterator


def change_indicator():
	"""
	A generator that flip-flops between 0 and 1.
	"""

	state = 0

	while True:
		state = 0 if state else 1

		yield state


def combine_variables(variables):
	"""
	Create a GroupIterator out of some Variables.

	The returned values are:
		iterator
		tuple of constant values
		number of items in the iterator
		variables sorted by their order in the tuples
	"""

	# Ignore disabled variables entirely!
	variables = [var for var in variables if var.enabled]

	if not variables:
		return ([], (), 0, [])

	order_attr = operator.attrgetter('order')
	ordered = sorted(variables, key=order_attr, reverse=True)
	grouped = ((order, list(vars)) for order, vars in itertools.groupby(ordered, order_attr))

	iterators = []
	num_items = 1
	sorted_variables = []
	# Treat each order to its own parallel iterator.
	for _, vars in grouped:
		# Each variable also gets its own tupled parallel iterator with a change indicator.
		with_indicators = [ParallelIterator([x.to_iterator(), change_indicator()]) for x in vars]

		var_iter = ParallelIterator(with_indicators)
		var_items = sum(1 for _ in var_iter)

		iterators.append(var_iter)
		num_items *= var_items
		sorted_variables.extend(vars)

	# This shouldn't be possible, but just in case.
	if num_items <= 0:
		return None

	iterator = ProductIterator(iterators)

	last_values = []
	for var in sorted_variables:
		# Using 2 as a value different from change_indicator values.
		last_values.extend([var.const, 2])

	return (iterator, tuple(last_values), num_items, sorted_variables)


class Variable(object):
	"""
	A simple linear space variable.
	"""

	def __init__(self, name, order, initial=0.0, final=0.0, steps=1, enabled=False,
			wait=0, const=None, use_const=False, resource_name=''):
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
		self.use_const = use_const

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

		wait.assert_dimension(SIValues.dimensions.time)

		self._wait = wait

	def to_iterator(self):
		"""
		Create an iterator for the variable.
		"""

		if self.use_const:
			return [self.const]
		else:
			return numpy.linspace(self.initial, self.final, self.steps)


if __name__ == '__main__':
	import unittest

	from .tests import test_variables as my_tests

	unittest.main(module=my_tests)
