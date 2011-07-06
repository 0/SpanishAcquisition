import itertools
import numpy
import operator

from spacq.interface.units import Quantity

from .group_iterators import ParallelIterator, ProductIterator


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
	Create a GroupIterator out of some OutputVariable instances.

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

	iterator = ProductIterator(iterators)

	last_values = []
	for var in sorted_variables:
		# Using 2 as a value different from change_indicator values.
		last_values.extend([var.const, 2])

	return (iterator, tuple(last_values), num_items, sorted_variables)


class Variable(object):
	"""
	An abstract superclass for all variables.
	"""

	def __init__(self, name, enabled=False, resource_name=''):
		self.name = name
		self.enabled = enabled
		self.resource_name = resource_name


class InputVariable(Variable):
	"""
	An input (measurement) variable.
	"""

	def __init__(self, *args, **kwargs):
		Variable.__init__(self, *args, **kwargs)


class OutputVariable(Variable):
	"""
	An abstract superclass for output variables.
	"""

	def __init__(self, order, wait='0 s', const=0.0, use_const=False, *args, **kwargs):
		Variable.__init__(self, *args, **kwargs)

		self.order = order

		# Iteration parameters.
		self._wait = Quantity(wait)
		self.const = const
		self.use_const = use_const

	@property
	def wait(self):
		return str(self._wait)

	@wait.setter
	def wait(self, value):
		wait = Quantity(value)
		wait.assert_dimensions('s')

		self._wait = wait


class LinSpaceVariable(OutputVariable):

	"""
	A linear space variable.
	"""

	def __init__(self, initial=0.0, final=0.0, steps=1, *args, **kwargs):
		OutputVariable.__init__(self, *args, **kwargs)

		# Linear space parameters.
		self.initial = initial
		self.final = final
		self._steps = steps

	@property
	def steps(self):
		return self._steps

	@steps.setter
	def steps(self, value):
		if value <= 0:
			raise ValueError('Number of steps must be positive, not "{0}".'.format(value))

		self._steps = value

	def to_iterator(self):
		if self.use_const:
			return [self.const]
		else:
			return numpy.linspace(self.initial, self.final, self.steps)
