import logging
import re


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

	def assert_logged(self, level, msg, ignore_case=True):
		"""
		Assert that a message matching the level and regular expression has been logged.
		"""

		level = level.lower()

		re_flags = 0
		if ignore_case:
			re_flags |= re.IGNORECASE

		for record in self.buffer:
			if record.levelname.lower() == level and re.search(msg, record.msg, re_flags):
				return

		assert False, 'Log message not found at level "{0}": {1}'.format(level, msg)
