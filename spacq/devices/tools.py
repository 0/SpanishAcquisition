import logging
log = logging.getLogger(__name__)

from functools import wraps
import string

from spacq.interface.units import Quantity

"""
Tools for working with hardware devices.
"""


def str_to_bool(value):
	"""
	False and 'False' => False
	otherwise => True
	"""

	return bool(value) and value.lower() != 'false'


def quantity_wrapped(units, multiplier=1.0):
	"""
	A decorator for getters to wrap the plain device value into a quantity with a unit.
	"""

	def wrap(f):
		@wraps(f)
		def wrapped(self):
			return Quantity(f(self) * multiplier, units)

		return wrapped

	return wrap

def quantity_unwrapped(units, multiplier=1.0):
	"""
	A decorator for setters to extract the plain device value from the quantity.
	"""

	def wrap(f):
		@wraps(f)
		def wrapped(self, value):
			value.assert_dimensions(units)

			return f(self, value.value * multiplier)

		return wrapped

	return wrap


class BlockDataError(Exception):
	"""
	Problem reading block data.
	"""

	pass


class BlockData(object):
	"""
	Utility methods for conversion between binary and 488.2 block data.
	"""

	@staticmethod
	def to_block_data(data):
		"""
		Packs binary data into 488.2 block data.

		As per section 7.7.6 of IEEE Std 488.2-1992.

		Note: Does not produce indefinitely-formatted block data.
		"""

		log.debug('Converting to block data: {0!r}'.format(data))

		length = len(data)
		length_length = len(str(length))

		return '#{0}{1}{2}'.format(length_length, length, data)

	@staticmethod
	def from_block_data(block_data):
		"""
		Extracts binary data from 488.2 block data.

		As per section 7.7.6 of IEEE Std 488.2-1992.
		"""

		log.debug('Converting from block data: {0!r}'.format(block_data))

		# Must have at least "#0\n" or "#XX".
		if len(block_data) < 3:
			raise BlockDataError('Not enough data.')

		if block_data[0] != '#':
			raise BlockDataError('Leading character is "{0}", not "#".'.format(block_data[0]))

		if block_data[1] == '0':
			log.debug('Indefinite format.')

			if block_data[-1] != '\n':
				raise BlockDataError('Final character is "{0}", not NL.'.format(block_data[-1]))

			return block_data[2:-1]
		else:
			log.debug('Definite format.')

			try:
				length_length = int(block_data[1])
			except ValueError:
				raise BlockDataError('Length length incorrectly specified: {0}'.format(block_data[1]))

			data_start = 2 + length_length

			if data_start > len(block_data):
				raise BlockDataError('Not enough data.')

			try:
				length = int(block_data[2:data_start])
			except ValueError:
				raise BlockDataError('Length incorrectly specified: {0}'.format(block_data[2:data_start]))

			data_end = data_start + length

			if data_end > len(block_data):
				raise BlockDataError('Not enough data.')
			elif data_end < len(block_data):
				if block_data[data_end:] != '\n':
					log.warning('Extra data ignored: {0!r}'.format(block_data[data_end:]))

			return block_data[data_start:data_end]


class BinaryEncoder(object):
	"""
	Utility methods for dealing with encoding and decoding binary data.
	"""

	@staticmethod
	def encode(msg):
		"""
		Convert a string of hexadecimal digits to a byte string.
		"""

		log.debug('Encoding to byte string: {0}'.format(msg))

		# Discard non-hexadecimal characters.
		msg_filtered = [x for x in msg if x in string.hexdigits]
		# Grab pairs.
		idxs = xrange(0, len(msg_filtered), 2)
		msg_paired = [''.join(msg_filtered[i:i+2]) for i in idxs]
		# Convert to bytes.
		msg_encoded = ''.join([chr(int(x, 16)) for x in msg_paired])

		log.debug('Encoded to: {0!r}'.format(msg_encoded))

		return msg_encoded

	@staticmethod
	def decode(msg, pair_size=2, pair_up=True):
		"""
		Convert a byte string to a string of hexadecimal digits.
		"""

		log.debug('Decoding from byte string: {0!r}'.format(msg))

		# Get the hex string for each byte.
		msg_decoded = ['{0:02x}'.format(ord(x)) for x in msg]

		if pair_up:
			idxs = xrange(0, len(msg_decoded), pair_size)
			msg_formatted = [''.join(msg_decoded[i:i+pair_size]) for i in idxs]

			result = ' '.join(msg_formatted)
		else:
			result = ''.join(msg_decoded)

		log.debug('Decoded to: {0}'.format(result))

		return result

	@staticmethod
	def length(msg):
		"""
		Calculate the number of bytes an unencoded message takes up when encoded.
		"""

		log.debug('Finding encoded length: {0}'.format(msg))

		result = len(BinaryEncoder.encode(msg))

		log.debug('Found encoded length: {0}'.format(result))

		return result
