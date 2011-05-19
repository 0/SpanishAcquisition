import logging
import Gpib
import gpib
import visa

"""
Tools for working with hardware devices.
"""


log = logging.getLogger(__name__)


# Implementation types: PyVISA, Linux GPIB.
PYVISA, LGPIB = xrange(2)


class BlockDataError(Exception):
	"""
	Problem reading block data.
	"""

	pass


class DeviceNotFoundError(Exception):
	"""
	Failure to connect to a device.
	"""

	pass


class IbstaBits(object):
	"""
	Status bits (in ibsta) as reported by Linux GPIB.
	"""

	DCAS = 0x1
	DTAS = 0x2
	LACS = 0x4
	TACS = 0x8
	ATN = 0x10
	CIC = 0x20
	REM = 0x40
	LOK = 0x80
	CMPL = 0x100
	EVENT = 0x200
	SPOLL = 0x400
	RQS = 0x800,
	SRQI = 0x1000
	END = 0x2000
	TIMO = 0x4000
	ERR = 0x8000


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

		log.debug('Converting to block data: {0}'.format(data))

		length = len(data)
		length_length = len(str(length))

		return '#{0}{1}{2}'.format(length_length, length, data)

	@staticmethod
	def from_block_data(block_data):
		"""
		Extracts binary data from 488.2 block data.

		As per section 7.7.6 of IEEE Std 488.2-1992.
		"""

		log.debug('Converting from block data: {0}'.format(block_data))

		# Must have at least "#0\n" or "#XX".
		if len(block_data) < 3:
			raise BlockDataError('Not enough data.')

		if block_data[0] != '#':
			raise BlockDataError('Leading character is "{0}", not #.'.format(block_data[0]))

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
				log.warning('Extra data ignored: {0}'.format(block_data[data_end:]))

			return block_data[data_start:data_end]


class AbstractDevice(object):
	"""
	A class for controlling devices which can be connected to either via Ethernet and PyVISA or GPIB and Linux GPIB.
	"""

	def __init__(self, ip_address=None, board=0, pad=None, sad=0):
		"""
		Connect to a device either over Ethernet or GPIB.

		Ethernet (tcpip::<ip_address>::instr):
			ip_address: The IP address on which the device is listening on port 111.

		GPIB (gpib[board]::<pad>[::<sad>]::instr):
			board: The GPIB board index. Defaults to 0.
			pad: The primary address of the device.
			sad: The secondary address of the device. Defaults to 0.
		"""

		if ip_address is not None:
			log.info('Attempting to use PyVISA with ip_address={0}.'.format(ip_address))

			self.implementation = PYVISA

			try:
				self.device = visa.Instrument('tcpip::{0}::instr'.format(ip_address))
			except visa.VisaIOError as e:
				raise DeviceNotFoundError('Could not open device at ip_address={0}.'.format(ip_address), e)
		elif board is not None and pad is not None:
			log.info('Attempting to use Linux GPIB with board={0}, pad={1}.'.format(board, pad))

			self.implementation = LGPIB

			try:
				self.device = Gpib.Gpib(board, pad, sad)
				# Gpib.Gpib doesn't complain if the device at the PAD doesn't actually exist.
				self.ask('*idn?')
			except gpib.GpibError as e:
				raise DeviceNotFoundError('Could not open device at board={0}, pad={1}.'.format(board, pad), e)
		else:
			raise ValueError('Either an IP or a GPIB address must be specified.')

	def write(self, message):
		"""
		Write to the device.
		"""

		log.debug('Writing to device: {0}'.format(message))

		self.device.write(message)

	def read_raw(self, chunk_size=512):
		"""
		Read everything the device has to say and return it exactly.
		"""

		log.debug('Reading from device.')

		buf = ''

		if self.implementation == PYVISA:
			buf = self.device.read_raw()
		elif self.implementation == LGPIB:
			status = 0
			while not status:
				buf += self.device.read(len=chunk_size)
				status = self.device.ibsta() & IbstaBits.END

		log.debug('Read from device: {0}'.format(buf))

		return buf

	def read(self):
		"""
		Read from the device, but strip terminating whitespace.
		"""

		return self.read_raw().rstrip()

	def ask_raw(self, message):
		"""
		Write, then read_raw.
		"""

		self.write(message)
		return self.read_raw()

	def ask(self, message):
		"""
		Write, then read.
		"""

		self.write(message)
		return self.read()

	@property
	def idn(self):
		"""
		Ask the device for identification.
		"""

		return self.ask('*idn?')


if __name__ == '__main__':
	import unittest

	from tests import test_abstract_device as my_tests

	unittest.main(module=my_tests)
