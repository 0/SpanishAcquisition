from nose.tools import eq_
from numpy import arange, linspace, repeat
from numpy.testing import assert_array_equal, assert_array_almost_equal
from pubsub import pub
from threading import RLock, Thread
import time
from unittest import main, TestCase

from .. import box


class FlattenTest(TestCase):
	def testEmpty(self):
		"""
		Flatten nothing.
		"""

		eq_(list(box.flatten([])), [])

	def testSingle(self):
		"""
		Flatten one thing.
		"""

		eq_(list(box.flatten([(1, 2, 3, 4, 5, 6, 7)])), [1, 2, 3, 4, 5, 6, 7])

	def testMany(self):
		"""
		Flatten all the things.
		"""

		eq_(list(box.flatten([(1, 2, 3), [4, 5, 6], {7: 8}])), [1, 2, 3, 4, 5, 6, 7])


class SiftTest(TestCase):
	def testEmpty(self):
		"""
		Sift nothing.
		"""

		eq_(box.sift([], object), [])

	def testAllSame(self):
		"""
		Either keep all or remove all.
		"""

		items = [object() for _ in xrange(5)]

		eq_(box.sift(items, object), items)
		eq_(box.sift(items, Exception), [])

	def testVaried(self):
		"""
		All sorts of objects.
		"""

		items = [ValueError(), TypeError(), KeyError(), 5]

		eq_(box.sift(items, object), items)
		eq_(box.sift(items, int), [items[3]])
		eq_(box.sift(items, Exception), items[0:3])
		eq_(box.sift(items, ValueError), [items[0]])


class TriplesToMeshTest(TestCase):
	def testSimple(self):
		"""
		No interpolation required.
		"""

		x = [1, 2, 3, 4] * 3 # [1, 2, 3, 4, 1, ...]
		y = repeat([5, 6, 7], 4) # [5, 5, 5, 5, 6, ...]
		z = linspace(0, -11, 12) # [0, -1, -2, -3, ...]

		result, x_bounds, y_bounds, z_bounds = box.triples_to_mesh(x, y, z)

		assert_array_equal(result, z.reshape(3, 4))
		eq_(x_bounds, (1, 4))
		eq_(y_bounds, (5, 7))
		eq_(z_bounds, (-11, 0))

	def testInterpolated(self):
		"""
		Some interpolation required.
		"""

		x = [0, 0, 0.25, 1, 1]
		y = [0, 1,    0, 0, 1]
		z = [1, 2,  1.5, 3, 4]

		result, x_bounds, y_bounds, z_bounds = box.triples_to_mesh(x, y, z)

		expected = [
			[1, 2, 3],
			[2, 3, 4],
		]

		assert_array_almost_equal(result, expected)
		eq_(x_bounds, (0, 1))
		eq_(y_bounds, (0, 1))
		eq_(z_bounds, (1, 4))

	def testBigDataSet(self):
		"""
		One hundred thousand evenly-spaced data points.
		"""

		x = range(1000) * 100
		y = repeat(range(100), 1000)
		z = arange(0, 100000)

		result, x_bounds, y_bounds, z_bounds = box.triples_to_mesh(x, y, z)

		assert_array_equal(result, z.reshape(100, 1000))
		eq_(x_bounds, (0, 999))
		eq_(y_bounds, (0, 99))
		eq_(z_bounds, (0, 99999))


class EnumTest(TestCase):
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


class PubDictTest(TestCase):
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

		pd = box.PubDict(RLock(), p.sendMessage, 'test')
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

		pd = box.PubDict(RLock(), pub.Publisher().sendMessage, 'test')

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

		pd = box.PubDict(RLock(), pub.Publisher().sendMessage, 'test')

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


class SynchronizedTest(TestCase):
	class SynchronizedObject(object):
		def __init__(self):
			self.buf = []

			self.lock = RLock()

		@box.Synchronized()
		def do(self, values):
			for i in xrange(values):
				self.buf.append(i)
				time.sleep(0.001)


	class SynchronizedThread(Thread):
		def __init__(self, obj, times, values):
			Thread.__init__(self)

			self.obj = obj
			self.times = times
			self.values = values

		def run(self):
			for i in xrange(self.times):
				self.obj.do(self.values)


	def testSynchronization(self):
		"""
		Ensure that synchronized methods are called in the correct order.
		"""

		num_threads = 4

		times = 4
		values = 5

		obj = SynchronizedTest.SynchronizedObject()

		thrs = []
		for _ in xrange(num_threads):
			thrs.append(SynchronizedTest.SynchronizedThread(obj, times, values))

		for thr in thrs:
			thr.start()

		for thr in thrs:
			thr.join()

		eq_(obj.buf, range(values) * times * num_threads)


class WithoutTest(TestCase):
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
	main()
