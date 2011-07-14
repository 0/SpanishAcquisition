from itertools import groupby, islice
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
		number of items in the iterator
		variables sorted by their order in the tuples
	"""

	# Ignore disabled variables entirely!
	variables = [var for var in variables if var.enabled]

	if not variables:
		return ([], 0, [])

	order_attr = operator.attrgetter('order')
	ordered = sorted(variables, key=order_attr, reverse=True)
	grouped = ((order, list(vars)) for order, vars in groupby(ordered, order_attr))

	iterators = []
	num_items = 1
	sorted_variables = []
	# Treat each order to its own parallel iterator.
	for _, vars in grouped:
		# Each variable also gets its own parallel iterator with a change indicator.
		with_indicators = [ParallelIterator([x.iterator, change_indicator()]) for x in vars]

		var_iter = ParallelIterator(with_indicators)
		var_items = sum(1 for _ in var_iter)

		iterators.append(var_iter)
		num_items *= var_items
		sorted_variables.extend(vars)

	iterator = ProductIterator(iterators)

	return (iterator, num_items, sorted_variables)


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

	# Maximum number of initial values to display in string form.
	display_values = 4

	# Maximum number of values to search through for the end.
	search_values = 1000

	def __init__(self, order, config=None, wait='0 s', const=0.0, use_const=False, *args, **kwargs):
		Variable.__init__(self, *args, **kwargs)

		self.order = order

		if config is not None:
			self.config = config
		else:
			self.config = LinSpaceConfig(0.0, 0.0, 1)

		# Iteration parameters.
		self._wait = Quantity(wait)
		self.const = const
		self.use_const = use_const

		# Smooth set.
		self.smooth_steps = 10
		self.smooth_from = False
		self.smooth_to = False

	@property
	def wait(self):
		return str(self._wait)

	@wait.setter
	def wait(self, value):
		wait = Quantity(value)
		wait.assert_dimensions('s')

		self._wait = wait

	@property
	def iterator(self):
		if self.use_const:
			return [self.const]
		else:
			return self.config.to_iterator()

	def __len__(self):
		if self.use_const:
			return 1
		else:
			return len(self.config)

	def __str__(self):
		found_values = list(islice(self.iterator, 0, self.search_values + 1))

		shown_values = ', '.join('{0:g}'.format(x) for x in found_values[:self.display_values])

		if len(found_values) > self.display_values:
			shown_values += ', ...'

			if len(found_values) <= self.search_values:
				shown_values += ', {0:g}'.format(found_values[-1])

		smooth_from = '(' if not self.use_const and self.smooth_from else '['
		smooth_to = ')' if not self.use_const and self.smooth_to else ']'
		return '{0}{1}{2}'.format(smooth_from, shown_values, smooth_to)


class LinSpaceConfig(object):
	"""
	Linear space variable configuration.
	"""

	def __init__(self, initial=0.0, final=0.0, steps=1):
		self.initial = initial
		self.final = final
		self.steps = steps

	@property
	def steps(self):
		return self._steps

	@steps.setter
	def steps(self, value):
		if value <= 0:
			raise ValueError('Number of steps must be positive, not "{0}".'.format(value))

		self._steps = value

	def to_iterator(self):
		return numpy.linspace(self.initial, self.final, self.steps)

	def __len__(self):
		return self.steps
