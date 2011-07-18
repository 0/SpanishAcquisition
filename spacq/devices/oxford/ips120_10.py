import logging
log = logging.getLogger(__name__)

from collections import namedtuple
from nose.tools import eq_
from time import sleep

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import str_to_bool

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

		# Resources.
		read_write = ['heater_on', 'sweep_rate', 'field']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['heater_on'].converter = str_to_bool
		self.resources['sweep_rate'].converter = float
		self.resources['field'].converter = float

	@Synchronized()
	def _connected(self):
		self.eos_char = '\r'

		AbstractDevice._connected(self)

		self.write('$Q4') # Extended resolution.
		self.write('$C3') # Remote & unlocked.
		self.write('$M9') # Display in Tesla.

		if self.status.activity == 4:
			self.write('$A0') # Unclamp.

		# Ensure some initial sanity.
		assert self.status.activity == 0, 'Not on hold.'
		assert not self.heater_on, 'Heater is on.'
		assert self.persistent_field == 0.0, 'Persistent field is {0}, not zero.'.format(self.persistent_field)
		assert self.output_field == 0.0, 'Output field is {0}, not zero.'.format(self.output_field)

	def write(self, message):
		"""
		Append the "\r" that the device requires.
		"""

		AbstractDevice.write(self, message + '\r')

	@property
	def status(self):
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

		return self.activities[self.status.activity]

	@activity.setter
	def activity(self, value):
		self.write('$A{0}'.format(self.activities.index(value)))

	@property
	def heater_on(self):
		"""
		Whether the heater is enabled.
		"""

		return bool(self.status.heater & 1)

	@heater_on.setter
	def heater_on(self, value):
		self.write('$H{0}'.format(int(value)))

		# Allow the heater to go to the correct setting.
		log.debug('Waiting for heater for {0} s.'.format(self.heater_delay))
		sleep(self.heater_delay)

	@property
	def sweep_rate(self):
		"""
		The rate of the field sweep in T/min.
		"""

		return float(self.ask('R9')[1:])

	@sweep_rate.setter
	def sweep_rate(self, value):
		if value <= 0:
			raise ValueError('Sweep rate must be positive, not {0}.'.format(value))

		self.write('$T{0:f}'.format(value))

	@property
	def persistent_field(self):
		"""
		The output field when the heater was last disabled, in T.
		"""

		return float(self.ask('R18')[1:])

	@property
	def output_field(self):
		"""
		The actual field due to the output current, in T.
		"""

		return float(self.ask('R7')[1:])

	@property
	def set_point(self):
		"""
		The set point in T.
		"""

		return float(self.ask('R8')[1:])

	@set_point.setter
	def set_point(self, value):
		self.write('$J{0}'.format(value))

	@property
	def field(self):
		"""
		The magnetic field in T.
		"""

		return self.output_field

	def set_field(self, value):
		"""
		Go through all the steps for setting the output field.
		"""

		if self.output_field == value:
			return

		set_delay = 60.0 * abs(value - self.output_field) / self.sweep_rate # s

		if value == 0:
			self.activity = 'to_zero'
		else:
			self.set_point = value

			self.activity = 'to_set'

		# If the heater is on, the sweep rate is used, so wait.
		if self.heater_on:
			log.debug('Waiting for sweep for {0} s.'.format(set_delay))
			sleep(set_delay)

		# Ensure that the sweep is actually over.
		while self.status.mode_sweep != 0:
			sleep(0.1)

		self.activity = 'hold'

		eq_(self.output_field, value)

	@field.setter
	@Synchronized()
	def field(self, value):
		status = self.status
		eq_(status.system_status, 0)
		eq_(status.limits, 0)
		eq_(status.mode_sweep, 0)

		eq_(self.activity, 'hold')
		assert not self.heater_on
		eq_(self.field, 0.0)

		# Return to the last field.
		self.set_field(self.persistent_field)

		# Change to the new field.
		self.heater_on = True
		self.set_field(value)
		self.heater_on = False

		# Back to zero.
		self.set_field(0.0)

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
