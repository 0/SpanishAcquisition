import logging
from threading import Thread
import time

from interface.units import SIValues
from tool.box import Without

"""
Tools for working with generic resources.
"""


log = logging.getLogger(__name__)


class NotReadable(Exception):
	"""
	Resource cannot be read from.
	"""

	pass


class NotWritable(Exception):
	"""
	Resource cannot be written to.
	"""

	pass


class Resource(object):
	"""
	A generic resource which can potentially be read from or written to.
	"""

	def __init__(self, obj=None, getter=None, setter=None, converter=None, allowed_values=None):
		"""
		obj: The device to which the resource belongs.
		getter: The method used to get the value.
		setter: The method used to set the value.
		converter: A function which returns a valid value for the resource, given a string.
		allowed_values: A set of all values which are valid for the resource.

		The getter and setter can be actual methods, or just attribute/property name strings.
		"""

		if getter is not None and not callable(getter) and obj is None:
			raise ValueError('Cannot call getter with no object.')

		if setter is not None and not callable(setter) and obj is None:
			raise ValueError('Cannot call setter with no object.')

		self.obj = obj
		self.getter = getter
		self.setter = setter
		self.converter = converter
		if allowed_values is not None:
			self.allowed_values = set(allowed_values)
		else:
			self.allowed_values = None

	@property
	def value(self):
		"""
		The value of the resource.
		"""

		if self.getter is None:
			raise NotReadable('Resource not readable.')

		if callable(self.getter):
			return self.getter()
		elif self.obj is not None:
			return getattr(self.obj, self.getter)
		else:
			raise NotReadable('Cannot read from resource.')

	@value.setter
	def value(self, v):
		if self.setter is None:
			raise NotWritable('Resource not writable.')

		if callable(self.setter):
			self.setter(v)
		elif self.obj is not None:
			setattr(self.obj, self.setter, v)
		else:
			raise NotWritable('Cannot write to resource.')

	def convert(self, value):
		if self.converter is not None:
			return self.converter(value)
		else:
			return value

	@property
	def readable(self):
		return self.getter is not None

	@property
	def writable(self):
		return self.setter is not None


class AcquisitionThread(Thread):
	"""
	Once every delay, call the callback with a fresh value from the resource.

	An optional running lock can block execution until it is released elsewhere.
	"""

	def __init__(self, delay, callback, resource=None, running_lock=None):
		Thread.__init__(self)

		delay.assert_dimension(SIValues.dimensions.time)

		self.resource = resource
		self.delay = delay
		self.callback = callback
		if running_lock is None:
			self.running_lock = Without()
		else:
			self.running_lock = running_lock

		# Allow the thread to be stopped prematurely.
		self.done = False

	def run(self):
		while not self.done:
			# If something goes wrong, sleep the maximum.
			delay = self.delay.value

			with self.running_lock:
				if time:
					next_run = time.time() + self.delay.value
				else:
					# Weird things happen at shutdown.
					return

				if self.resource is not None:
					try:
						value = self.resource.value
					except Exception as e:
						log.error('Could not obtain resource value: {0}'.format(repr(e)))
					else:
						self.callback(value)

				if time:
					delay = next_run - time.time()
				else:
					return

			if delay > 0:
				time.sleep(delay)


if __name__ == '__main__':
	import unittest

	from tests import test_resources as my_tests

	unittest.main(module=my_tests)
