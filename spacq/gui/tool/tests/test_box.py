from nose.tools import eq_
from unittest import main, TestCase

from .. import box


class DetermineWildcardTest(TestCase):
	def testDefault(self):
		"""
		Simply all files.
		"""

		w = box.determine_wildcard()
		eq_(w, 'All files|*')

	def testExtension(self):
		"""
		With a nameless extension.
		"""

		w = box.determine_wildcard('test')
		eq_(w, '(*.test)|*.test|All files|*')

	def testFileType(self):
		"""
		With a named extension.
		"""

		w = box.determine_wildcard('test', 'Test')
		eq_(w, 'Test (*.test)|*.test|All files|*')

	def testInvalid(self):
		"""
		Try some invalid combinations.
		"""

		# Unused argument.
		w = box.determine_wildcard(file_type='Test')
		eq_(w, 'All files|*')

		# Invalid characters.
		try:
			box.determine_wildcard('test|test', 'Test')
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		try:
			box.determine_wildcard('test', 'Test|Test')
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'


if __name__ == '__main__':
	main()
