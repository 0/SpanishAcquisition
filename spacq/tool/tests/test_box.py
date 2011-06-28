from nose.tools import eq_
from pubsub import pub
from threading import RLock
import unittest

from .. import box


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


class PubDictTest(unittest.TestCase):
	def testSimple(self):
		"""
		Run through some valid cases.
		"""

		data = []

		def msg_added(name, value):
			data.append((name, value))

		def msg_removed(name):
			data.append((name,))

		p = pub.Publisher()

		p.subscribe(msg_added, 'test.added')
		p.subscribe(msg_removed, 'test.removed')

		pd = box.PubDict(RLock(), p, 'test')
		pd['a'] = 'abc'
		pd['b'] = 'def'
		pd['c'] = 'ghi'
		del pd['a']
		pd['a'] = 'jkl'
		del pd['c']

		expected = {'a': 'jkl', 'b': 'def'}
		expected_data = [('a', 'abc'), ('b', 'def'), ('c', 'ghi'), ('a',), ('a', 'jkl'), ('c',)]

		eq_(pd, expected)
		eq_(data, expected_data)

	def testLocked(self):
		"""
		Attempt a compound operation.
		"""

		pd = box.PubDict(RLock(), pub.Publisher(), 'test')

		pd['a'] = 'abc'

		with pd.lock:
			del pd['a']
			pd['a'] = 'def'

		expected = {'a': 'def'}

		eq_(pd, expected)

	def testInvalid(self):
		"""
		Try some bad scenarios.
		"""

		pd = box.PubDict(RLock(), pub.Publisher(), 'test')

		# Setting None.
		try:
			pd['a'] = None
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		# Overwriting.
		pd['a'] = 'abc'
		try:
			pd['a'] = 'def'
		except KeyError:
			pass
		else:
			assert False, 'Expected KeyError.'


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
