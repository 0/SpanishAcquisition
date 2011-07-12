import logging
log = logging.getLogger(__name__)

from nose.plugins.skip import SkipTest
import re
from unittest import TestCase

from testconfig import config as tc


class AssertHandler(logging.handlers.BufferingHandler):
	"""
	A logging handler that allows making assertions based on its contents.
	"""

	def __init__(self, capacity=100, *args, **kwargs):
		"""
		Add ourselves to the main logger.
		"""

		logging.handlers.BufferingHandler.__init__(self, capacity, *args, **kwargs)

		logging.getLogger().addHandler(self)

	def assert_logged(self, level, msg, ignore_case=True, literal=False):
		"""
		Assert that a message matching the level and regular expression has been logged.
		"""

		level = level.lower()

		re_flags = 0
		if ignore_case:
			re_flags |= re.IGNORECASE

		for record in self.buffer:
			if record.levelname.lower() == level:
				if (literal and msg == record.msg or
						not literal and re.search(msg, record.msg, re_flags)):
					return

		assert False, 'Log message not found at level "{0}": {1}'.format(level, msg)


class DeviceServerTestCase(TestCase):
	"""
	Class for a device server test.
	"""

	def obtain_device(self, impl=None, model_name=None, required_keys=None):
		"""
		Try to get a handle for a physical device.
		"""

		all_devices = tc['devices'].items()

		if model_name is not None:
			potential_devices = (a for (n, a) in all_devices if n.startswith('{0}.'.format(model_name)))
		else:
			potential_devices = (a for (n, a) in all_devices)

		for device in potential_devices:
			valid = True

			if required_keys is not None:
				for required_key in required_keys:
					if required_key not in device:
						valid = False
						break

			if not valid:
				continue

			try:
				if impl is not None:
					return impl(**device['address'])
				else:
					return device
			except Exception as e:
				log.info('Could not connect to device at "{0}": {1}'.format(device['address'], e))

		raise SkipTest('Could not connect to device.')
