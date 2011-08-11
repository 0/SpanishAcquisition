import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_wrapped

"""
Sample ABC1234 Device
"""


class ABC1234(AbstractDevice):
	"""
	Interface for the Sample ABC1234.
	"""

	allowed_settings = ['default value', 'something else', '...']

	def _setup(self):
		AbstractDevice._setup(self)

		# Resources.
		read_only = ['reading']
		for name in read_only:
			self.resources[name] = Resource(self, name)

		read_write = ['setting']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['reading'].units = 'A'
		self.resources['setting'].allowed_values = self.allowed_settings

	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)

		# Override the default.
		self.setting = '...'

	@Synchronized()
	def reset(self):
		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	@property
	def setting(self):
		"""
		This is a generic setting.
		"""

		return self.ask('some:setting?')

	@setting.setter
	def setting(self, value):
		if value not in self.allowed_settings:
			raise ValueError('Invalid setting: {0}'.format(value))

		self.write('some:setting {0}'.format(value))

	@property
	@quantity_wrapped('A')
	@Synchronized()
	def reading(self):
		"""
		The value measured by the device.
		"""

		log.debug('Getting reading.')
		result = float(self.ask('read?'))
		log.debug('Got reading: {0}'.format(result))

		return result


name = 'ABC1234'
implementation = ABC1234
