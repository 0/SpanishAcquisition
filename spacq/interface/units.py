import logging
log = logging.getLogger(__name__)

from copy import deepcopy
from math import log10
from numpy import allclose, array
import quantities as pq

"""
Tools for working with quantities and units.
"""


class IncompatibleDimensions(TypeError):
	"""
	Operation on quantities with different dimensions.
	"""

	pass


class SIValues(object):
	"""
	Values for SI units.
	"""

	prefixes = {
		'y': -24,
		'z': -21,
		'a': -18,
		'f': -15,
		'p': -12,
		'n': -9,
		'u': -6,
		'm': -3,
		'c': -2,
		'd': -1,
		'': 0,
		'da': 1,
		'h': 2,
		'k': 3,
		'M': 6,
		'G': 9,
		'T': 12,
		'P': 15,
		'E': 18,
		'Z': 21,
		'Y': 24,
	}
	prefixes_ = dict([(v, k) for (k, v) in prefixes.items()])

	# SI base and derived units.
	units = set(['A', 'cd', 'g', 'Hz', 'J', 'K', 'm', 'mol', 'N', 's', 'V'])


class Quantity(object):
	"""
	A quantity with a value and dimensions.
	"""

	@staticmethod
	def parse_units(string):
		"""
		Convert group of unit symbols to pq-acceptable notation:
			Determine the multipliers and strip the prefixes.
			Use "*" and "**" to combine units.

		eg. ' mN.m.ks-2' -> 'N*m*s**-2', 3
		"""

		symbols = [x.strip() for x in string.split('.')]

		result_units = []
		result_multiplier = 0

		for symbol in symbols:
			symbol_unit, symbol_multiplier = None, None
			for prefix, multiplier in SIValues.prefixes.items():
				if not symbol.startswith(prefix):
					continue

				unit = symbol[len(prefix):]

				exponent = None
				for i in xrange(len(unit)):
					try:
						exponent = float(unit[i:])
						break
					except ValueError:
						pass

				if exponent is not None:
					unit = unit[:i]

				if unit not in SIValues.units:
					continue

				if symbol_unit is None:
					if exponent is not None:
						unit += '**{0}'.format(exponent)
					symbol_unit, symbol_multiplier = unit, multiplier
				else:
					# Already found a match.
					raise ValueError('Ambiguous unit symbol: "{0}"'.format(symbol))

			if symbol_unit is not None:
				result_units.append(symbol_unit)
				result_multiplier += symbol_multiplier
			else:
				# Did not find anything.
				raise ValueError('Unrecognized unit symbol: "{0}"'.format(symbol))

		return ('*'.join(result_units), result_multiplier)

	@staticmethod
	def from_string(string):
		"""
		Separate the value from the units.
		"""

		value = None
		for i in xrange(len(string), 0, -1):
			try:
				value = float(string[:i])
			except ValueError:
				continue

			return value, string[i:]

		raise ValueError(value)

	def __init__(self, value, units=None):
		"""
		Both ('100 ms') and (100, 'ms') are acceptable.
		"""

		if isinstance(value, basestring):
			value, units = self.from_string(value)

		# Even if passed a lone integer, work with an array of floats.
		value = array(value, dtype=float)

		log.debug('Creating Quantity: {0}, {1}'.format(value, units))

		# Remove unit prefixes.
		new_units, multiplier = self.parse_units(units)
		new_value = value * (10 ** multiplier)

		# Normalize to SI base units.
		original_quantity = pq.Quantity(new_value, new_units)
		self._q = original_quantity.simplified

		# Information to restore original representation.
		self.original_units = units
		self.original_multiplier = multiplier

		# Find the normalization factor.
		if self._q.magnitude.size > 1:
			for q, orig in zip(self._q.magnitude.flatten(), original_quantity.magnitude.flatten()):
				if q != orig:
					self.original_multiplier += log10(abs(q)) - log10(abs(orig))
					break
		else:
			q, orig = self._q.magnitude, original_quantity.magnitude
			if q != orig:
				self.original_multiplier += log10(abs(q)) - log10(abs(orig))

	@property
	def dimensions(self):
		"""
		The set of simplified units and their exponents.
		"""

		return set(self._q.dimensionality.items())

	@property
	def value(self):
		"""
		The magnitude of the quantity, normalized to the base units.
		"""

		result = self._q.magnitude

		if result.shape:
			return result
		else:
			return result.tolist()

	@property
	def original_value(self):
		"""
		The magnitude of the quantity that matches the units.
		"""

		return self._q.magnitude / (10 ** self.original_multiplier)

	def assert_dimensions(self, other, exception=True):
		"""
		Whether the dimensions match.

		If exception is True and we would have returned False, raise an exception.
		"""

		if isinstance(other, basestring):
			# Given a units string.
			other = Quantity(1, other).dimensions

		if self.dimensions == other:
			return True
		elif exception:
			raise IncompatibleDimensions(self.dimensions, other)
		else:
			return False

	# FIXME: Python 2.7 provides functools.total_ordering()
	def __eq__(self, other):
		self.assert_dimensions(other.dimensions)

		return allclose(self.value, other.value)

	def __lt__(self, other):
		self.assert_dimensions(other.dimensions)

		return self.value < other.value

	def __ne__(self, other):
		return not self == other

	def __le__(self, other):
		return self == other or self < other

	def __ge__(self, other):
		return not self < other

	def __gt__(self, other):
		return not self <= other

	def __mul__(self, other):
		"""
		Multiplication by reals.
		"""

		result = deepcopy(self)
		result._q *= other

		return result

	def __rmul__(self, other):
		return self * other

	def __repr__(self):
		return '{0}(\'{1}\')'.format(self.__class__.__name__, str(self))

	def __str__(self):
		value = self.original_value
		symbol = self.original_units

		if isinstance(value, float):
			return '{0:.10g} {1}'.format(value, symbol)
		else:
			raise NotImplementedError()

	# FIXME: http://projects.scipy.org/numpy/ticket/1176
	def __deepcopy__(self, memo):
		"""
		Rather than copying anything, simply create a new instance.
		"""

		return Quantity(str(self))
