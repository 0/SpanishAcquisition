from spacq.tool.box import Enum

from .abstract_device import DeviceNotFoundError

"""
Device configuration.
"""


def device_tree():
	"""
	Build a device tree from the existing devices.
	"""

	from .. import devices

	tree = {}

	for manufacturer in devices.manufacturers:
		subtree = {}

		for model, mock_model in zip(manufacturer.models, manufacturer.mock_models):
			if model is None and mock_model is None:
				continue
			elif model is not None and mock_model is None:
				name = model.name
			elif model is None and mock_model is not None:
				name = mock_model.name
			elif model is not None and mock_model is not None:
				if model.name != mock_model.name:
					raise ValueError('Different device names: "{0}" and '
							'"{1}".'.format(model.name, mock_model.name))

				name = model.name

			subtree[name] = {}

			if model is not None:
				subtree[name]['real'] = model.implementation

			if mock_model is not None:
				subtree[name]['mock'] = mock_model.implementation

		tree[manufacturer.name] = subtree

	return tree


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

	def __init__(self, name):
		self.name = name

		# Connection configuration.
		self.address_mode = None
		self.ip_address = None
		self.gpib_board = 0
		self.gpib_pad = 0
		self.gpib_sad = 0
		self.usb_resource = None

		# Information about module that implements this device.
		self.manufacturer = None
		self.model = None
		self.mock = False

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

		if self.manufacturer is None or self.model is None:
			raise ConnectionError('No implementation specified.')

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

		tree = device_tree()

		if self.manufacturer not in tree:
			raise ConnectionError('Unknown manufacturer: {0}'.format(self.manufacturer))
		else:
			subtree = tree[self.manufacturer]

		if self.model not in subtree:
			raise ConnectionError('Unknown model: {0}'.format(self.model))
		else:
			subtree = subtree[self.model]

		kind = 'mock' if self.mock else 'real'

		if kind not in subtree:
			raise ConnectionError('Unknown kind: {0}'.format(kind))
		else:
			implementation = subtree[kind]

		try:
			device = implementation(autoconnect=False, **address)
		except (ValueError, NotImplementedError) as e:
			raise ConnectionError('Unable to create device.', e)

		try:
			device.connect()
		except DeviceNotFoundError as e:
			raise ConnectionError('Unable to make connection to device.', e)

		self.device = device
