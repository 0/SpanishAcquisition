from nose.tools import eq_
import unittest

from tool import box


class ImportPathTest(unittest.TestCase):
	def testValid(self):
		"""
		Import valid modules.
		"""

		# With extension.
		m1 = box.import_path('tool/box.py')
		eq_(m1.__doc__, box.__doc__)

		# Without extension.
		m2 = box.import_path('tool/box')
		eq_(m2.__doc__, box.__doc__)

	def testInvalid(self):
		"""
		Try to import invalid modules.
		"""

		# Empty.
		try:
			box.import_path('')
		except ImportError:
			pass
		else:
			assert False, 'Expected ImportError.'

		# Non-empty.
		try:
			box.import_path('not/a/module.py')
		except ImportError:
			pass
		else:
			assert False, 'Expected ImportError.'


class EnumTest(unittest.TestCase):
	def testEmpty(self):
		"""
		A useless object.
		"""

		e = box.Enum()

		try:
			e.anything
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'

		eq_(len(e), 0)

	def testNotEmpty(self):
		"""
		A regular enum.
		"""

		values = ['cow', 'moon', 'dish', 'spoon']

		e = box.Enum(values)

		eq_(len(e), len(values))

		for v in values:
			eq_(getattr(e, v), v)

		e.cow, e.moon, e.dish, e.spoon

		try:
			e.diddle
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'

	def testDuplicates(self):
		"""
		Check uniqueness and equality testing.
		"""

		e = box.Enum(['a'] * 100 + ['b'] * 50)
		f = box.Enum(['b', 'a'])

		eq_(e, f)


class WithoutTest(unittest.TestCase):
	def testWith(self):
		"""
		Use Without in with.
		"""

		with box.Without():
			with box.Without() as w:
				assert w is None

	def testException(self):
		"""
		Ensure that exceptions are passed through.
		"""

		try:
			with box.Without():
				raise IndexError
		except IndexError:
			pass
		else:
			assert False, 'Expected IndexError.'


if __name__ == '__main__':
	unittest.main()