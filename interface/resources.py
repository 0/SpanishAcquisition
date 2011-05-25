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

	def __init__(self, obj=None, getter=None, setter=None):
		if getter is not None and not callable(getter) and obj is None:
			raise ValueError('Cannot call getter with no object.')

		if setter is not None and not callable(setter) and obj is None:
			raise ValueError('Cannot call setter with no object.')

		self._obj = obj
		self._getter = getter
		self._setter = setter

	@property
	def value(self):
		"""
		The value of the resource.
		"""

		if self._getter is None:
			raise NotReadable()

		if callable(self._getter):
			return self._getter()
		elif self._obj is not None:
			return getattr(self._obj, self._getter)
		else:
			raise NotReadable()

	@value.setter
	def value(self, v):
		if self._setter is None:
			raise NotWritable()

		if callable(self._setter):
			self._setter(v)
		elif self._obj is not None:
			setattr(self._obj, self._setter, v)
		else:
			raise NotWritable()


if __name__ == '__main__':
	import unittest

	from tests import test_resources as my_tests

	unittest.main(module=my_tests)
