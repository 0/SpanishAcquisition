import logging
import Gpib
import gpib
import threading
import visa

from devices.tools import Synchronized

"""
Hardware device abstraction interface.
"""


log = logging.getLogger(__name__)


# Implementation types: PyVISA, Linux GPIB, PyVISA USB.
PYVISA, LGPIB, PYVISA_USB = xrange(3)


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


class USBDevice(visa.Instrument):
	"""
	Using USB devices with PyVISA requires a small hack: the object must be an Instrument, but we can't call Instrument.__init__.
	"""

	def __init__(self, *args, **kwargs):
		# Bypass the initialization in visa.Instrument, due to "send_end" not being valid for USB.
		visa.ResourceTemplate.__init__(self, *args, **kwargs)


class SuperDevice(object):
	def _setup(self):
		"""
		Pre-connection setup.
		"""

		self.name = self.__class__.__name__

		self.resources = {}
		self.subdevices = {}

	def _connected(self):
		"""
		Post-connection setup.
		"""

		# Recursively.
		for name, subdev in self.subdevices.items():
			log.debug('Post-connection for subdevice "{0}".'.format(name))

			subdev._connected()


class AbstractDevice(SuperDevice):
	"""
	A class for controlling devices which can be connected to either via Ethernet and PyVISA or GPIB and Linux GPIB.
	"""

	def _setup(self):
		SuperDevice._setup(self)

		self.lock = threading.RLock()

	def __init__(self, ip_address=None, board=0, pad=None, sad=0, usb_resource=None, autoconnect=True):
		"""
		Ethernet (tcpip::<ip_address>::instr):
			ip_address: IP address on which the device is listening on port 111.

		GPIB (gpib[board]::<pad>[::<sad>]::instr):
			board: GPIB board index. Defaults to 0.
			pad: Primary address of the device.
			sad: Secondary address of the device. Defaults to 0.

		USB (usb_resource):
			usb_resource: VISA resource of the form: USB[board]::<vendor>::<product>::<serial>[::<interface>]::RAW

		autoconnect: Connect to the device upon instantiation.
		"""

		self._setup()

		log.info('Creating device "{0}".'.format(self.name))

		if ip_address is not None:
			log.debug('Using PyVISA with ip_address="{0}".'.format(ip_address))

			self._implementation = PYVISA

			self.ip_address = ip_address
		elif board is not None and pad is not None:
			log.debug('Using Linux GPIB with board="{0}", pad="{1}".'.format(board, pad))

			self._implementation = LGPIB

			self.board = board
			self.pad = pad
			self.sad = sad
		elif usb_resource is not None:
			log.debug('Using PyVISA with usb_resource="{0}"'.format(usb_resource))

			self._implementation = PYVISA_USB

			self.usb_resource = usb_resource
		else:
			raise ValueError('Either an IP, GPIB, or USB address must be specified.')

		if autoconnect:
			self.connect()

	def connect(self):
		"""
		Make a connection to the device.
		"""

		log.info('Connecting to device "{0}".'.format(self.name))

		if self._implementation == PYVISA:
			try:
				self.device = visa.Instrument('tcpip::{0}::instr'.format(self.ip_address))
			except visa.VisaIOError as e:
				raise DeviceNotFoundError('Could not open device at ip_address="{0}".'.format(self.ip_address), e)
		elif self._implementation == LGPIB:
			try:
				self.device = Gpib.Gpib(self.board, self.pad, self.sad)
				# Gpib.Gpib doesn't complain if the device at the PAD doesn't actually exist.
				log.debug('GPIB device IDN: {0}'.format(self.idn))
			except gpib.GpibError as e:
				raise DeviceNotFoundError('Could not open device at board={0}, pad={1}, sad={2}.'.format(self.board, self.pad, self.sad), e)
		elif self._implementation == PYVISA_USB:
			try:
				self.device = USBDevice(self.usb_resource)
			except visa.VisaIOError as e:
				raise DeviceNotFoundError('Could not open device at usb_resource="{0}".'.format(self.usb_resource), e)

		self._connected()

	@Synchronized()
	def write(self, message):
		"""
		Write to the device.
		"""

		log.debug('Writing to device "{0}": {1}'.format(self.name, message))

		if self._implementation == PYVISA or self._implementation == LGPIB:
			self.device.write(message)
		elif self._implementation == PYVISA_USB:
			# Send the message raw.
			visa.vpp43.write(self.device.vi, message)

	@Synchronized()
	def read_raw(self, chunk_size=512):
		"""
		Read everything the device has to say and return it exactly.
		"""

		log.debug('Reading from device "{0}".'.format(self.name))

		buf = ''

		if self._implementation == PYVISA or self._implementation == PYVISA_USB:
			buf = self.device.read_raw()
		elif self._implementation == LGPIB:
			status = 0
			while not status:
				buf += self.device.read(len=chunk_size)
				status = self.device.ibsta() & IbstaBits.END

		log.debug('Read from device "{0}": {1}'.format(self.name, buf))

		return buf

	def read(self):
		"""
		Read from the device, but strip terminating whitespace.
		"""

		return self.read_raw().rstrip()

	@Synchronized()
	def ask_raw(self, message):
		"""
		Write, then read_raw.
		"""

		self.write(message)
		return self.read_raw()

	@Synchronized()
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


class AbstractSubdevice(SuperDevice):
	def _setup(self):
		SuperDevice._setup(self)

		# Synchronized methods should use the device lock.
		self.lock = self.device.lock if self.device else None

	def __init__(self, device):
		self.device = device

		self._setup()


if __name__ == '__main__':
	import unittest

	from tests import test_abstract_device as my_tests

	unittest.main(module=my_tests)
