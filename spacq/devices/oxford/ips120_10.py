import logging
log = logging.getLogger(__name__)

from collections import namedtuple
from time import sleep

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import str_to_bool, quantity_wrapped, quantity_unwrapped

"""
Oxford Instruments IPS120-10 Superconducting Magnet Power Supply
"""


Status = namedtuple('Status', 'system_status, limits, activity, remote_status, heater, mode, mode_sweep')


class IPS120_10(AbstractDevice):
	"""
	Interface for the Oxford Instruments IPS120-10.
	"""

	allowed_settings = ['default value', 'something else']

	activities = ['hold', 'to_set', 'to_zero', 'clamped']

	heater_delay = 10 # s

	def _setup(self):
		AbstractDevice._setup(self)

		self._perma_hot = True

		# Resources.
		read_write = ['perma_hot', 'sweep_rate', 'field']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['perma_hot'].converter = str_to_bool
		self.resources['sweep_rate'].units = 'T.s-1'
		self.resources['field'].units = 'T'

	@Synchronized()
	def _connected(self):
		self.eos_char = '\r'

		AbstractDevice._connected(self)

		self.write('$Q4') # Extended resolution.
		self.write('$C3') # Remote & unlocked.
		self.write('$M9') # Display in Tesla.

		if self.device_status.activity == 4:
			self.write('$A0') # Unclamp.

		# Ensure some initial sanity.
		assert self.device_status.activity == 0, 'Not on hold.'

	def write(self, message):
		"""
		Append the "\r" that the device requires.
		"""

		AbstractDevice.write(self, message + '\r')

	@property
	def device_status(self):
		"""
		All the status information for the device.
		"""

		result = self.ask('X')

		system_status = int(result[1])
		limits = int(result[2])
		activity = int(result[4])
		remote_status = int(result[6])
		heater = int(result[8])
		mode = int(result[10])
		mode_sweep = int(result[11])
		# The polarity status is deprecated.

		return Status(system_status, limits, activity, remote_status, heater, mode, mode_sweep)

	@property
	def activity(self):
		"""
		What the device is currently up to.
		"""

		return self.activities[self.device_status.activity]

	@activity.setter
	def activity(self, value):
		self.write('$A{0}'.format(self.activities.index(value)))

	@property
	def heater_on(self):
		"""
		Whether the heater is enabled.
		"""

		return bool(self.device_status.heater & 1)

	@heater_on.setter
	def heater_on(self, value):
		self.status.append('Turning heater o{0}'.format('n' if value else 'ff'))

		try:
			self.write('$H{0}'.format(int(value)))

			# Allow the heater to go to the correct setting.
			log.debug('Waiting for heater for {0} s.'.format(self.heater_delay))
			sleep(self.heater_delay)
		finally:
			self.status.pop()

	@property
	def perma_hot(self):
		"""
		Whether the heater should always remain on.
		"""

		return self._perma_hot

	@perma_hot.setter
	def perma_hot(self, value):
		self._perma_hot = value

	@property
	# The value used on the device is in T/min.
	@quantity_wrapped('T.s-1', 1./60)
	def sweep_rate(self):
		"""
		The rate of the field sweep, as a quantity in T/s.
		"""

		return float(self.ask('R9')[1:])

	@sweep_rate.setter
	@quantity_unwrapped('T.s-1', 60)
	def sweep_rate(self, value):
		if value <= 0:
			raise ValueError('Sweep rate must be positive, not {0}.'.format(value))

		self.write('$T{0:f}'.format(value))

	@property
	@quantity_wrapped('T')
	def persistent_field(self):
		"""
		The output field when the heater was last disabled, as a quantity in T.
		"""

		return float(self.ask('R18')[1:])

	@property
	@quantity_wrapped('T')
	def output_field(self):
		"""
		The actual field due to the output current in T.
		"""

		return float(self.ask('R7')[1:])

	@property
	@quantity_wrapped('T')
	def set_point(self):
		"""
		The set point, as a quantity in T.
		"""

		return float(self.ask('R8')[1:])

	@set_point.setter
	@quantity_unwrapped('T')
	def set_point(self, value):
		self.write('$J{0}'.format(value))

	@property
	def field(self):
		"""
		The magnetic field, as a quantity in T.
		"""

		return self.output_field

	def set_field(self, value):
		"""
		Go through all the steps for setting the output field.
		"""

		if self.output_field == value:
			return

		self.status.append('Setting field to {0}'.format(value))

		try:
			set_delay = abs(value - self.output_field).value / self.sweep_rate.value # s

			self.set_point = value
			self.activity = 'to_set'

			# If the heater is on, the sweep rate is used, so wait.
			if self.heater_on:
				log.debug('Waiting for sweep for {0} s.'.format(set_delay))
				sleep(set_delay)

			# Ensure that the sweep is actually over.
			while self.device_status.mode_sweep != 0:
				sleep(0.1)

			self.activity = 'hold'
		finally:
			self.status.pop()

	@field.setter
	@Synchronized()
	def field(self, value):
		status = self.device_status
		assert status.system_status == 0, 'System status: {0}'.format(status.system_status)
		assert status.limits == 0, 'Limits: {0}'.format(status.limits)
		assert status.mode_sweep == 0, 'Mode sweep: {0}'.format(status.mode_sweep)
		assert self.activity == 'hold', 'Activity: {0}'.format(self.activity)

		# Return to the last field.
		if not self.heater_on:
			self.set_field(self.persistent_field)
			self.heater_on = True

		# Change to the new field.
		self.set_field(value)

		if not self.perma_hot:
			self.heater_on = False

	@property
	def idn(self):
		"""
		*idn? substitute for this non-SCPI device.
		"""

		return self.ask('V')

	@property
	def opc(self):
		"""
		*opc? substitute for this non-SCPI device.
		"""

		return 1


name = 'IPS120-10'
implementation = IPS120_10
