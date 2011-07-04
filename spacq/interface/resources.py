import logging
log = logging.getLogger(__name__)

from copy import copy
from threading import Thread
import time

from spacq.tool.box import Without

from .units import SIValues

"""
Tools for working with generic resources.
"""


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

		self.wrappers = []

	@property
	def value(self):
		"""
		The value of the resource.
		"""

		if self.getter is None:
			raise NotReadable('Resource not readable.')

		if callable(self.getter):
			result = self.getter()
		elif self.obj is not None:
			result = getattr(self.obj, self.getter)
		else:
			raise NotReadable('Cannot read from resource.')

		# Apply the wrappers.
		for _, getter_filter, _ in self.wrappers:
			if getter_filter is None:
				continue

			result = getter_filter(result)

		return result

	@value.setter
	def value(self, v):
		if self.setter is None:
			raise NotWritable('Resource not writable.')

		# Apply the wrappers.
		for _, _, setter_filter in self.wrappers:
			if setter_filter is None:
				continue

			v = setter_filter(v)

		if self.allowed_values is not None and v not in self.allowed_values:
			raise ValueError('Disallowed value: {0}'.format(v))

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

	def _find_wrapper_by_name(self, name):
		"""
		Return the last index of the given wrapper.
		"""

		for i, (n, _, _) in reversed(list(enumerate(self.wrappers))):
			if n == name:
				return i

		raise ValueError('Wrapper not found: {0}'.format(name))

	def is_wrapped_by(self, name):
		"""
		Determine whether the given wrapper already wraps this Resource.
		"""

		try:
			self._find_wrapper_by_name(name)
		except ValueError:
			return False
		else:
			return True

	def wrapped(self, name, getter_filter=None, setter_filter=None):
		"""
		Produce a Resource which is a wrapper around this Resource.

		name: The name of the wrapper to add.
		getter_filter: Function of one argument through which to pass any obtained values.
		setter_filter: Function of one argument through which to pass values when setting.
		"""

		result = copy(self)

		result.wrappers = self.wrappers + [(name, getter_filter, setter_filter)]

		return result

	def unwrapped(self, name):
		"""
		Produce a Resource with the last instance of the given wrapper removed.

		name: The name of the wrapper to remove.
		"""

		result = copy(self)

		idx = self._find_wrapper_by_name(name)
		result.wrappers = self.wrappers[:idx] + self.wrappers[idx+1:]

		return result


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

			if not self.done and delay > 0:
				time.sleep(delay)
