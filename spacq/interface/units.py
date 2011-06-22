from scipy import constants

from ..tool.box import Enum

"""
Tools for working with quantities and units.
"""


class IncompatibleDimensions(Exception):
	"""
	Operation on quantities with different dimensions.
	"""

	pass


class SIValues(object):
	"""
	Values for SI units.
	"""

	dimensions = Enum([
		'time',
		'frequency',
		'current',
	])

	prefixes = {
		'z': constants.zepto,
		'a': constants.atto,
		'f': constants.femto,
		'p': constants.pico,
		'n': constants.nano,
		'u': constants.micro,
		'm': constants.milli,
		'c': constants.centi,
		'd': constants.deci,
		'': 1,
		'da': constants.deka,
		'h': constants.hecto,
		'k': constants.kilo,
		'M': constants.mega,
		'G': constants.giga,
		'T': constants.tera,
		'P': constants.peta,
		'E': constants.exa,
		'Z': constants.zetta,
		'Y': constants.yotta,
	}
	prefixes_ = dict([(v, k) for (k, v) in prefixes.items()])

	units = {
		's': dimensions.time,
		'Hz': dimensions.frequency,
		'A': dimensions.current,
	}
	units_ = dict([(v, k) for (k, v) in units.items()])


class Quantity(object):
	"""
	A quantity with a value and dimension.
	"""

	@staticmethod
	def _parse_unit(value):
		"""
		Determine the multiplier and dimension of a unit symbol.
		"""

		for unit in SIValues.units:
			if not value.endswith(unit):
				continue

			idx = len(value) - len(unit)

			if idx >= 0 and value[:idx] in SIValues.prefixes:
				prefix = value[:idx]
				# Matches a prefix and the unit.
				multiplier = SIValues.prefixes[prefix]
			else:
				# Cannot make a match with this unit.
				continue

			return (prefix, multiplier, SIValues.units[unit])

		raise ValueError(value)

	@classmethod
	def from_string(cls, value):
		"""
		Create an instance based on a string representation, such as "500 ms".
		"""

		# Expect at least a digit and a letter.
		if len(value) < 2:
			raise ValueError(value)

		spl = value.split()

		if len(spl) == 1:
			# No whitespace, so maybe of the form "500ns".
			idx = -1
			while value[idx+1].isdigit() or value[idx+1] == '.':
				idx += 1

			if idx >= 0:
				unit_str = value[idx+1:]

				try:
					prefix, multiplier, dimension = cls._parse_unit(unit_str)
					return Quantity(float(value[:idx+1]) * multiplier, dimension, original_prefix=prefix)
				except ValueError:
					pass
		elif len(spl) == 2:
			# One section of whitespace, so maybe of the form "500 ns".
			try:
				prefix, multiplier, dimension = cls._parse_unit(spl[1])
				return Quantity(float(spl[0]) * multiplier, dimension, original_prefix=prefix)
			except ValueError:
				pass

		raise ValueError(value)

	def __init__(self, value, dimension, original_prefix=None):
		self.value = value
		self.dimension = dimension
		self.original_prefix = original_prefix

	def assert_dimension(self, other_dimension, exception=True):
		"""
		Whether the dimension matches.

		If exception is True and we would have returned False, raise an exception.
		"""

		if self.dimension == other_dimension:
			return True
		elif exception:
			raise IncompatibleDimensions(self.dimension, other_dimension)
		else:
			return False

	# FIXME: Python 2.7 provides functools.total_ordering()
	def __eq__(self, other):
		self.assert_dimension(other.dimension)

		return self.value == other.value

	def __lt__(self, other):
		self.assert_dimension(other.dimension)

		return self.value < other.value

	def __ne__(self, other):
		return not self == other

	def __le__(self, other):
		return self == other or self < other

	def __ge__(self, other):
		return not self < other

	def __gt__(self, other):
		return not self <= other

	def __repr__(self):
		"""
		eg. 'Quantity(0.005, SIValues.dimensions.time)'
		"""

		return '{0}({1}, SIValues.dimensions.{2})'.format(self.__class__.__name__, repr(self.value), self.dimension)

	def __str__(self):
		"""
		eg. '5 ms'
		"""

		if self.original_prefix is not None:
			multiplier = SIValues.prefixes[self.original_prefix]
			value = self.value / multiplier
			min_prefix = self.original_prefix
		elif self.value == 0:
			# Zero should get no prefix, because '0 s' makes more sense than '0 zs'.
			value = self.value
			min_prefix = ''
		else:
			multipliers = SIValues.prefixes_.items()
			# Make the results reproducible.
			multipliers.sort()

			min_distance, min_multiplier, min_prefix = None, None, None
			for multiplier, prefix in multipliers:
				distance = abs(self.value - multiplier)

				if min_distance is None or distance < min_distance:
					min_distance, min_multiplier, min_prefix = distance, multiplier, prefix

			value = self.value / min_multiplier

		return '{0:.10g} {1}{2}'.format(value, min_prefix, SIValues.units_[self.dimension])


if __name__ == '__main__':
	import unittest

	from .tests import test_units as my_tests

	unittest.main(module=my_tests)
