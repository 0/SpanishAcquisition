from .abstract_device import DeviceNotFoundError
from ..tool.box import Enum, import_path

"""
Device configuration.
"""


class ConnectionError(Exception):
	"""
	Unable to connect.
	"""

	pass


class DeviceConfig(object):
	"""
	Description for a device.
	"""

	address_modes = Enum([
		'ethernet',
		'gpib',
		'usb',
	])

	def __init__(self):
		# Connection configuration.
		self.address_mode = None
		self.ip_address = None
		self.gpib_board = 0
		self.gpib_pad = 0
		self.gpib_sad = 0
		self.usb_resource = None

		# Path to module that implements this device.
		self.implementation_path = None

		# Resource path to label mappings.
		self.resource_labels = {}

		# The connected device object.
		self.device = None

		# Label to resource object mappings.
		self.resources = {}

	def __getstate__(self):
		"""
		Return a modified dictionary for pickling.
		"""

		result = self.__dict__.copy()

		# Do not pickle references to mutable objects.
		del result['device']
		del result['resources']

		return result

	def __setstate__(self, dict):
		"""
		Revert the changes done by __getstate__.
		"""

		self.__dict__ = dict

		# Set missing values to defaults.
		self.device = None
		self.resources = {}

	def diff_resources(self, new):
		"""
		Compare the resources belonging to 2 DeviceConfig objects.

		The result is a tuple of:
			resources which appear
			resources which change
			resources which disappear
		where all "resources" are label to resource object mappings.
		"""

		old_labels, new_labels = set(self.resources), set(new.resources)

		appeared = new_labels - old_labels
		disappeared = old_labels - new_labels

		changed = set()
		possibly_changed = old_labels.intersection(new_labels)
		for p in possibly_changed:
			if self.resources[p] is not new.resources[p]:
				changed.add(p)

		return (appeared, changed, disappeared)

	def connect(self):
		"""
		Create an instance of the implementation and connect to it.
		"""

		if self.address_mode not in self.address_modes:
			raise ConnectionError('Invalid address mode specified.')

		if self.implementation_path is None:
			raise ConnectionError('No implementation path specified.')

		address = {}

		if self.address_mode == self.address_modes.ethernet:
			if self.ip_address is None:
				raise ConnectionError('No IP address specified.')

			address['ip_address'] = self.ip_address
		elif self.address_mode == self.address_modes.gpib:
			address['gpib_board'] = self.gpib_board
			address['gpib_pad'] = self.gpib_pad
			address['gpib_sad'] = self.gpib_sad
		elif self.address_mode == self.address_modes.usb:
			if self.usb_resource is None:
				raise ConnectionError('No USB resource specified.')

			address['usb_resource'] = self.usb_resource

		if self.implementation_path[-3:] != '.py':
			raise ConnectionError('Must use a Python implementation.')

		try:
			implementation_module = import_path(self.implementation_path)
		except ImportError as e:
			raise ConnectionError('Unable to import implementation.', e)

		try:
			implementation = implementation_module.implementation
		except AttributeError:
			raise ConnectionError('Implementation does not supply "implementation" global.')

		try:
			device = implementation(autoconnect=False, **address)
		except (ValueError, NotImplementedError) as e:
			raise ConnectionError('Unable to create device.', e)

		try:
			device.connect()
		except DeviceNotFoundError as e:
			raise ConnectionError('Unable to make connection to device.', e)

		self.device = device


if __name__ == '__main__':
	import unittest

	# Does not run server tests.
	from .tests import test_config as my_tests

	unittest.main(module=my_tests)