import logging

from devices.abstract_device import AbstractDevice
from devices.tools import Synchronized
from interface.resources import Resource

"""
Agilent 34410A Digital Multimeter

Obtain measurements from the multimeter.
"""


log = logging.getLogger(__name__)


class DM34410A(AbstractDevice):
	"""
	Interface for Agilent 34410A DM.
	"""

	def _setup(self):
		self.reset()

		# Exported resources.
		read_only = ['dc_voltage']
		for name in read_only:
			self.resources[name] = Resource(self, name)

	def __init__(self, *args, **kwargs):
		"""
		Connect to the DM and initialize with some values.
		"""

		AbstractDevice.__init__(self, *args, **kwargs)

		self._setup()

	@Synchronized()
	def reset(self):
		"""
		Reset the device to its default state.
		"""

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	@property
	@Synchronized()
	def dc_voltage(self):
		"""
		The DC voltage measured by the device.
		"""

		log.debug('Getting DC voltage.')
		result = float(self.ask('measure:voltage:dc?'))
		log.debug('Got DC voltage: {0}'.format(result))

		return result


if __name__ == '__main__':
	import unittest

	from tests import test_dm34410a as my_tests

	unittest.main(module=my_tests)
