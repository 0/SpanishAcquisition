import logging
import threading

from devices.tools import Synchronized

"""
Hardware device abstraction interface.
"""


log = logging.getLogger(__name__)


# Implementation types: PyVISA, Linux GPIB, PyVISA USB.
PYVISA, LGPIB, PYVISA_USB = xrange(3)


# Try to import all available implementation types.
available_implementations = []

try:
	import Gpib
	import gpib
except ImportError:
	pass
else:
	available_implementations.append(LGPIB)

try:
	import visa
except ImportError:
	pass
else:
	available_implementations.append(PYVISA)
	available_implementations.append(PYVISA_USB)


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
		self.multi_command = None
		self.responses_expected = 0

		SuperDevice._setup(self)

		self.lock = threading.RLock()

	def __init__(self, ip_address=None, gpib_board=0, gpib_pad=None, gpib_sad=0,
			usb_resource=None, autoconnect=True):
		"""
		Ethernet (tcpip::<ip_address>::instr):
			ip_address: Address on which the device is listening on port 111.

		GPIB (gpib[gpib_board]::<gpib_pad>[::<gpib_sad>]::instr):
			gpib_board: GPIB board index. Defaults to 0.
			gpib_pad: Primary address of the device.
			gpib_sad: Secondary address of the device. Defaults to 0.

		USB (usb_resource):
			usb_resource: VISA resource of the form: USB[board]::<vendor>::<product>::<serial>[::<interface>]::RAW

		autoconnect: Connect to the device upon instantiation.
		"""

		self._setup()

		log.info('Creating device "{0}".'.format(self.name))

		if ip_address is not None:
			if PYVISA in available_implementations:
				log.debug('Using PyVISA with ip_address="{0}".'.format(ip_address))
				self._implementation = PYVISA
				self.connection_resource = {
					'resource_name': 'tcpip::{0}::instr'.format(ip_address),
				}
			else:
				raise NotImplementedError('PyVISA required, but not available.')
		elif gpib_pad is not None:
			if LGPIB in available_implementations:
				log.debug('Using Linux GPIB with gpib_board="{0}", gpib_pad="{1}", '
						'gpib_sad="{2}".'.format(gpib_board, gpib_pad, gpib_sad))
				self._implementation = LGPIB
				self.connection_resource = {
					'name': gpib_board,
					'pad': gpib_pad,
					'sad': gpib_sad,
				}
			elif PYVISA in available_implementations:
				log.debug('Using PyVISA with gpib_board="{0}", gpib_pad="{1}", '
						'gpib_sad="{2}".'.format(gpib_board, gpib_pad, gpib_sad))
				self._implementation = PYVISA
				self.connection_resource = {
					'resource_name': 'gpib{0}::{1}::{2}::instr'.format(gpib_board, gpib_pad, gpib_sad),
				}
			else:
				raise NotImplementedError('Linux GPIB or PyVISA required, but not available.')
		elif usb_resource is not None:
			if PYVISA_USB in available_implementations:
				log.debug('Using PyVISA with usb_resource="{0}"'.format(usb_resource))
				self._implementation = PYVISA_USB
				self.connection_resource = {
					'resource_name': usb_resource,
				}
			else:
				raise NotImplementedError('PyVISA required, but not available.')
		else:
			raise ValueError('Either an IP, GPIB, or USB address must be specified.')

		if autoconnect:
			self.connect()

	def connect(self):
		"""
		Make a connection to the device.
		"""

		log.info('Connecting to device "{0}" using {1} at "{2}".'.format(self.name, self._implementation, self.connection_resource))

		try:
			if self._implementation == PYVISA:
				self.device = visa.Instrument(**self.connection_resource)
			elif self._implementation == LGPIB:
				self.device = Gpib.Gpib(**self.connection_resource)
				# Gpib.Gpib doesn't complain if the device at the PAD doesn't actually exist.
				log.debug('GPIB device IDN: {0}'.format(self.idn))
			elif self._implementation == PYVISA_USB:
				self.device = USBDevice(**self.connection_resource)
		except (visa.VisaIOError, gpib.GpibError) as e:
			raise DeviceNotFoundError('Could not open device at '
					'"{0}".'.format(self.connection_resource), e)

		self._connected()

	def multi_command_start(self):
		"""
		Redirect further commands to a buffer.
		"""

		log.debug('Starting multi-command message for device "{0}"'.format(self.name))

		if self._implementation not in [PYVISA, LGPIB]:
			raise NotImplementedError('Unsupported implementation: "{0}".'.format(self._implementation))

		self.multi_command = []
		self.responses_expected = 0

	@Synchronized()
	def multi_command_stop(self):
		"""
		Stop redirecting to a buffer, and send the buffered commands.

		Returns the results of queries if any were expected.
		"""

		log.debug('Stopping multi-command message for device "{0}"'.format(self.name))

		if self.multi_command is None:
			raise ValueError('Multi-command message not started.')
		elif not self.multi_command:
			# No commands.
			return

		commands = self.multi_command
		# This ensures that write and ask will not buffer the real message.
		self.multi_command = None

		# Only commands not starting with "*" get a ":" prefix.
		commands = [cmd if cmd[0] == '*' else ':' + cmd for cmd in commands]
		message = ';'.join(commands)

		if self.responses_expected:
			result = self.ask(message)

			# FIXME: What if the response contains a meaningful ";" somewhere?
			return result.split(';', self.responses_expected - 1)
		else:
			self.write(message)

	@Synchronized()
	def write(self, message):
		"""
		Write to the device.

		Supports multi-command.
		"""

		if self.multi_command is not None:
			log.debug('Writing to multi-command buffer for device "{0}": {1}'.format(self.name, message))

			self.multi_command.append(message)
			return

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

		Supports multi-command.
		"""

		self.write(message)

		if self.multi_command is None:
			return self.read()
		else:
			self.responses_expected += 1

	def find_resource(self, path):
		"""
		Return a Resource given a resource path spec.

		eg. ('subdevice A', 'subdevice B', 'resource C') -> Resource
		"""

		log.debug('Looking for resource {0}.'.format(path))

		if len(path) < 1:
			raise ValueError('No path provided.')

		# Keep track of the last device in the tree so far.
		dev = self
		# Keep track of the path so far.
		traversed = ()

		while len(path) > 1:
			try:
				dev = dev.subdevices[path[0]]
			except KeyError:
				raise ValueError('No subdevice "{0}" in {1}.'.format(path[0], traversed))

			traversed += path[:1]
			path = path[1:]

		try:
			return dev.resources[path[0]]
		except KeyError:
			raise ValueError('No resource "{0}" in {1}.'.format(path[0], traversed))

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

	# Does not run server tests.
	from tests import test_abstract_device as my_tests

	unittest.main(module=my_tests)
