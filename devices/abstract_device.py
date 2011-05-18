import gpib
import Gpib
import visa


# Implementation types: PyVISA, Linux GPIB.
PYVISA, LGPIB = xrange(2)


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


class DeviceNotFoundError(Exception):
	"""
	Failure to connect to a device.
	"""

	pass


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
			self.implementation = PYVISA

			try:
				self.device = visa.Instrument('tcpip::%s::instr' % (ip_address))
			except visa.VisaIOError as e:
				raise DeviceNotFoundError('Could not open device at ip_address=%s.' % (ip_address), e)
		elif board is not None and pad is not None:
			self.implementation = LGPIB

			try:
				self.device = Gpib.Gpib(board, pad, sad)
				# Gpib.Gpib doesn't complain if the device at the PAD doesn't actually exist.
				self.ask('*idn?')
			except gpib.GpibError as e:
				raise DeviceNotFoundError('Could not open device at board=%d, pad=%d.' % (board, pad), e)
		else:
			raise ValueError('Either an IP or a GPIB address must be specified.')

	def read_raw(self, chunk_size=512):
		"""
		Read everything the device has to say and return it exactly.
		"""

		if self.implementation == PYVISA:
			return self.device.read_raw()
		elif self.implementation == LGPIB:
			buffer = ''

			status = 0
			while not status:
				buffer += self.device.read(len=chunk_size)
				status = self.device.ibsta() & IbstaBits.END

			return buffer

	def read(self):
		"""
		Read from the device, but strip terminating whitespace.
		"""

		return self.read_raw().rstrip()

	def write(self, message):
		"""
		Write to the device.
		"""

		self.device.write(message)

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


if __name__ == '__main__':
	import unittest

	from tests import test_abstract_device


	unittest.main(module=test_abstract_device)
