import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import str_to_bool, quantity_wrapped, quantity_unwrapped

"""
Interface for R&S SMF100A signal generator.
"""


class SMF100A(AbstractDevice):
	"""
	Interface for the SMF100A.
	"""

	min_power = 0.007 # V
	max_power = 7.071 # V

	min_freq = 1e9 # Hz
	max_freq = 22e9 # Hz

	def _setup(self):
		AbstractDevice._setup(self)

		# Resources.
		read_write = ['enabled', 'power', 'frequency']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['enabled'].converter = str_to_bool
		self.resources['power'].units = 'V'
		self.resources['frequency'].units = 'Hz'

	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)

		# Set the units for communication.
		self.write('unit:power v')

	@Synchronized()
	def reset(self):
		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	@property
	def enabled(self):
		"""
		Whether the RF output is enabled.
		"""

		return bool(int(self.ask('output:state?')))

	@enabled.setter
	def enabled(self, value):
		self.write('output:state {0}'.format(int(value)))

	@property
	@quantity_wrapped('V')
	def power(self):
		"""
		The RF output power, as a quantity in V.
		"""

		return float(self.ask('source:power:power?'))

	@power.setter
	@quantity_unwrapped('V')
	def power(self, value):
		if value < self.min_power or value > self.max_power:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value,
				self.min_power, self.max_power))

		self.write('source:power:power {0}'.format(value))

	@property
	@quantity_wrapped('Hz')
	def frequency(self):
		"""
		The RF output frequency, as a quantity in Hz.
		"""

		return float(self.ask('source:frequency:cw?'))

	@frequency.setter
	@quantity_unwrapped('Hz')
	def frequency(self, value):
		if value < self.min_freq or value > self.max_freq:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value,
				self.min_freq, self.max_freq))

		self.write('source:frequency:cw {0}'.format(value))


name = 'SMF100A'
implementation = SMF100A
