import logging
log = logging.getLogger(__name__)

from threading import RLock
from time import time

from spacq.tool.box import Enum, Synchronized

"""
Hardware device abstraction interface.
"""


# PyVISA, Linux GPIB, PyVISA USB.
drivers = Enum(['pyvisa', 'lgpib', 'pyvisa_usb'])


# Try to import all available drivers.
available_drivers = []

try:
	import Gpib
	import gpib
except ImportError:
	pass
else:
	available_drivers.append(drivers.lgpib)

try:
	import visa
except ImportError:
	pass
else:
	available_drivers.append(drivers.pyvisa)
	available_drivers.append(drivers.pyvisa_usb)


class DeviceNotFoundError(Exception):
	"""
	Failure to connect to a device.
	"""

	pass


class DeviceTimeout(Exception):
	"""
	Timeout on action.
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

		if hasattr(self, 'driver') and self.driver == drivers.lgpib:
			# Some devices don't assert the EOI line, so look for their EOS character instead.
			if hasattr(self, 'eos_char'):
				self.device.config(gpib.IbcEOSchar, ord(self.eos_char))
				self.device.config(gpib.IbcEOSrd, 1)

			# Gpib.Gpib doesn't complain if the device at the PAD doesn't actually exist.
			try:
				log.debug('GPIB device IDN: {0!r}'.format(self.idn))
			except gpib.GpibError as e:
				raise DeviceNotFoundError('Could not open device at "{0}".'.format(self.connection_resource), e)

		# Recursively.
		for name, subdev in self.subdevices.items():
			log.debug('Post-connection for subdevice "{0}".'.format(name))

			subdev._connected()


class AbstractDevice(SuperDevice):
	"""
	A class for controlling devices which can be connected to either via Ethernet and PyVISA or GPIB and Linux GPIB.
	"""

	max_timeout = 15 # s

	def _setup(self):
		self.multi_command = None
		self.responses_expected = 0

		SuperDevice._setup(self)

		self.lock = RLock()

		self.status = []

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
			if drivers.pyvisa in available_drivers:
				log.debug('Using PyVISA with ip_address="{0}".'.format(ip_address))
				self.driver = drivers.pyvisa
				self.connection_resource = {
					'resource_name': 'tcpip::{0}::instr'.format(ip_address),
				}
			else:
				raise NotImplementedError('PyVISA required, but not available.')
		elif gpib_pad is not None:
			if drivers.lgpib in available_drivers:
				log.debug('Using Linux GPIB with gpib_board="{0}", gpib_pad="{1}", '
						'gpib_sad="{2}".'.format(gpib_board, gpib_pad, gpib_sad))
				self.driver = drivers.lgpib
				self.connection_resource = {
					'name': gpib_board,
					'pad': gpib_pad,
					'sad': gpib_sad,
				}
			elif drivers.pyvisa in available_drivers:
				log.debug('Using PyVISA with gpib_board="{0}", gpib_pad="{1}", '
						'gpib_sad="{2}".'.format(gpib_board, gpib_pad, gpib_sad))
				self.driver = drivers.pyvisa
				self.connection_resource = {
					'resource_name': 'gpib{0}::{1}::{2}::instr'.format(gpib_board, gpib_pad, gpib_sad),
				}
			else:
				raise NotImplementedError('Linux GPIB or PyVISA required, but not available.')
		elif usb_resource is not None:
			if drivers.pyvisa_usb in available_drivers:
				log.debug('Using PyVISA with usb_resource="{0}"'.format(usb_resource))
				self.driver = drivers.pyvisa_usb
				self.connection_resource = {
					'resource_name': usb_resource,
				}
			else:
				raise NotImplementedError('PyVISA required, but not available.')
		else:
			raise ValueError('Either an IP, GPIB, or USB address must be specified.')

		if autoconnect:
			self.connect()

	def __repr__(self):
		return '<{0}>'.format(self.__class__.__name__)

	def connect(self):
		"""
		Make a connection to the device.
		"""

		log.info('Connecting to device "{0}" using {1} at "{2}".'.format(self.name, self.driver, self.connection_resource))

		if self.driver == drivers.pyvisa:
			try:
				self.device = visa.Instrument(**self.connection_resource)
			except visa.VisaIOError as e:
				raise DeviceNotFoundError('Could not open device at "{0}".'.format(self.connection_resource), e)
		elif self.driver == drivers.lgpib:
			try:
				self.device = Gpib.Gpib(**self.connection_resource)
			except gpib.GpibError as e:
				raise DeviceNotFoundError('Could not open device at "{0}".'.format(self.connection_resource), e)
		elif self.driver == drivers.pyvisa_usb:
			class USBDevice(visa.Instrument):
				"""
				Using USB devices with PyVISA requires a small hack: the object must be an Instrument, but we can't call Instrument.__init__.
				"""

				def __init__(self, *args, **kwargs):
					# Bypass the initialization in visa.Instrument, due to "send_end" not being valid for USB.
					visa.ResourceTemplate.__init__(self, *args, **kwargs)

			try:
				self.device = USBDevice(**self.connection_resource)
			except visa.VisaIOError as e:
				raise DeviceNotFoundError('Could not open device at "{0}".'.format(self.connection_resource), e)

		try:
			self._connected()
		except Exception as e:
			raise DeviceNotFoundError('Could not finish connection to device at "{0}".'.format(self.connection_resource), e)

	def multi_command_start(self):
		"""
		Redirect further commands to a buffer.
		"""

		log.debug('Starting multi-command message for device "{0}"'.format(self.name))

		if self.driver not in [drivers.pyvisa, drivers.lgpib]:
			raise NotImplementedError('Unsupported driver: "{0}".'.format(self.driver))

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
			return []

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

			return []

	@Synchronized()
	def write(self, message):
		"""
		Write to the device.

		Supports multi-command.
		"""

		if self.multi_command is not None:
			log.debug('Writing to multi-command buffer for device "{0}": {1!r}'.format(self.name, message))

			self.multi_command.append(message)
			return

		log.debug('Writing to device "{0}": {1!r}'.format(self.name, message))

		if self.driver == drivers.pyvisa:
			try:
				self.device.write(message)
			except visa.VisaIOError as e:
				if e.error_code == visa.VI_ERROR_TMO:
					raise DeviceTimeout(e)
				else:
					raise
		elif self.driver == drivers.lgpib:
			try:
				self.device.write(message)
			except gpib.GpibError as e:
				if 'timeout' in e.message:
					raise DeviceTimeout(e)
				else:
					raise
		elif self.driver == drivers.pyvisa_usb:
			# Send the message raw.
			visa.vpp43.write(self.device.vi, message)

	@Synchronized()
	def read_raw(self, chunk_size=512):
		"""
		Read everything the device has to say and return it exactly.
		"""

		log.debug('Reading from device "{0}".'.format(self.name))

		buf = ''

		if self.driver in [drivers.pyvisa, drivers.pyvisa_usb]:
			try:
				buf = self.device.read_raw()
			except visa.VisaIOError as e:
				if e.error_code == visa.VI_ERROR_TMO:
					raise DeviceTimeout(e)
				else:
					raise
		elif self.driver == drivers.lgpib:
			status = 0
			while status == 0:
				try:
					buf += self.device.read(len=chunk_size)
				except gpib.GpibError as e:
					if 'timeout' in e.message:
						raise DeviceTimeout(e)
					else:
						raise

				status = self.device.ibsta() & IbstaBits.END

		log.debug('Read from device "{0}": {1!r}'.format(self.name, buf))

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

	def close(self):
		"""
		Close the connection, if possible.
		"""

		log.debug('Closing device: {0}'.format(self.name))

		if self.driver in [drivers.pyvisa, drivers.pyvisa_usb]:
			self.device.close()

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

		if self.driver in [drivers.pyvisa, drivers.lgpib]:
			return self.ask('*idn?')

	@property
	def opc(self):
		"""
		Wait until the device is done.
		"""

		end_time = time() + self.max_timeout

		while True:
			if self.driver in [drivers.pyvisa, drivers.lgpib]:
				try:
					self.ask('*opc?')
				except DeviceTimeout:
					if time() > end_time:
						raise
				else:
					break


class AbstractSubdevice(SuperDevice):
	"""
	A subdevice (eg. channel) of a hardware device.
	"""

	def _setup(self):
		SuperDevice._setup(self)

		# Synchronized methods should use the device lock.
		self.lock = self.device.lock if self.device else None

	def __init__(self, device):
		self.device = device

		self._setup()
