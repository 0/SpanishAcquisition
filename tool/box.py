import os
import sys

"""
Generic tools.
"""


def import_path(path):
	"""
	Import a Python module given its file path.
	"""

	# Truncate the extension, if given.
	if path[-3:] == '.py':
		path = path[:-3]

	# Prepend the given path to the import path.
	sys.path.insert(0, os.path.dirname(path))

	try:
		return __import__(os.path.basename(path))
	except Exception as e:
		raise ImportError('Could not import "{0}".'.format(path), e)
	finally:
		# Clean up the import path.
		del sys.path[0]


class Enum(set):
	"""
	An enumerated type.

	>>> e = Enum(['a', 'b', 'c'])
	>>> e.a
	'a'
	>>> e.d
	...
	AttributeError: 'Enum' object has no attribute 'd'
	"""

	def __getattribute__(self, name):
		if name in self:
			return name
		else:
			return set.__getattribute__(self, name)


class Without(object):
	"""
	A no-op object for use with "with".
	"""

	def __enter__(self, *args, **kwargs):
		return None

	def __exit__(self, *args, **kwargs):
		return False


if __name__ == '__main__':
	import unittest

	from tests import test_box as my_tests

	unittest.main(module=my_tests)
