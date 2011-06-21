from nose.tools import eq_
from threading import Lock
import time
import unittest

from interface.units import Quantity, SIValues

from interface import resources


class WithAttribute(object):
	x = 5


class WithMethods(object):
	_x = 5

	def get_x(self):
		return self._x

	def set_x(self, value):
		self._x = value


class WithProperty(object):
	_x = 5

	@property
	def x(self):
		return self._x

	@x.setter
	def x(self, value):
		self._x = value


class ResourceTest(unittest.TestCase):
	def testUseless(self):
		"""
		A resource with neither a getter nor a setter.
		"""

		res = resources.Resource()

		try:
			res.value
		except resources.NotReadable:
			pass
		else:
			assert False, 'Expected NotReadable.'

		assert not res.readable

		try:
			res.value = 5
		except resources.NotWritable:
			pass
		else:
			assert False, 'Expected NotWritable.'

		assert not res.writable

	def testMoreThanUseless(self):
		"""
		A resource with a lookup getter or setter, but no object.
		"""

		# Broken from the start.
		try:
			res = resources.Resource(getter='x')
		except:
			pass
		else:
			assert False, 'Expected ValueError.'

		try:
			res = resources.Resource(setter='x')
		except:
			pass
		else:
			assert False, 'Expected ValueError.'

		# Broken later on.
		res = resources.Resource()
		res.getter = 'x'
		res.setter = 'x'

		try:
			res.value
		except resources.NotReadable:
			pass
		else:
			assert False, 'Expected NotReadable.'

		try:
			res.value = 5
		except resources.NotWritable:
			pass
		else:
			assert False, 'Expected NotWritable.'


	def testReadonly(self):
		"""
		A read-only resource using an attribute.
		"""

		dev = WithAttribute()
		res = resources.Resource(dev, 'x')

		eq_(res.value, 5)

		try:
			res.value = 55
		except resources.NotWritable:
			pass
		else:
			assert False, 'Expected NotWritable.'

		eq_(res.value, 5)

	def testWriteonly(self):
		"""
		A write-only resource using an attribute.
		"""

		dev = WithAttribute()
		res = resources.Resource(dev, None, 'x')

		eq_(dev.x, 5)

		try:
			res.value
		except resources.NotReadable:
			pass
		else:
			assert False, 'Expected NotReadable.'

		res.value = 55

		eq_(dev.x, 55)

	def testWithMethods(self):
		"""
		A read-write resource using methods.
		"""

		dev = WithMethods()
		res = resources.Resource(None, dev.get_x, dev.set_x)

		eq_(res.value, 5)

		res.value = 1234

		eq_(res.value, 1234)

	def testWithProperty(self):
		"""
		A read-write resource using a property.
		"""

		dev = WithProperty()
		res = resources.Resource(dev, 'x', 'x')

		eq_(res.value, 5)

		res.value = 5678

		eq_(res.value, 5678)

	def testConverter(self):
		"""
		Conversion with and without a converter.
		"""

		dev = WithAttribute()
		res1 = resources.Resource(dev)
		res2 = resources.Resource(dev, converter=int)
		res3 = resources.Resource(dev, converter=float)

		eq_(res1.convert('5'), '5')
		eq_(res2.convert('5'), 5)
		eq_(res2.convert('5'), 5.0)

	def testWrapping(self):
		"""
		Wrap resources in other resources.
		"""

		dev = WithAttribute()
		res1 = resources.Resource(dev, 'x', 'x')

		res1.value = 5
		eq_(res1.value, 5)

		res2 = resources.Resource.wrap(res1, 'wrapper1', lambda x: 2 * x, lambda x: 3 * x)

		eq_(res2.value, 10)
		res2.value = 5
		eq_(res1.value, 15)
		eq_(res2.value, 30)

		res3 = resources.Resource.wrap(res2, 'wrapper2', lambda x: 5 * x)

		eq_(res3.value, 150)
		res3.value = 10
		eq_(res1.value, 30)
		eq_(res2.value, 60)
		eq_(res3.value, 300)

		res1.value = 1
		eq_(res1.value, 1)
		eq_(res2.value, 2)
		eq_(res3.value, 10)

		eq_(res3.wrappers, ['wrapper1', 'wrapper2'])


class AcquisitionThreadTest(unittest.TestCase):
	def testWithoutResource(self):
		"""
		Let the thread run without a resource.
		"""

		buf = []
		delay = Quantity(0.1, SIValues.dimensions.time)
		
		thr = resources.AcquisitionThread(delay, buf.append)

		thr.start()
		time.sleep(delay.value * 10)
		thr.done = True

		eq_(buf, [])

	def testWithResource(self):
		"""
		Let the thread run with a resource.
		"""

		dev = WithMethods()
		res = resources.Resource(dev, dev.get_x)

		expected = [res.value] * 10

		buf = []
		delay = Quantity(0.1, SIValues.dimensions.time)

		thr = resources.AcquisitionThread(delay, buf.append, res)

		thr.start()
		time.sleep(delay.value * 10)
		thr.done = True

		eq_(buf, expected)

	def testWithLock(self):
		"""
		Pause the thread with a lock.
		"""

		dev = WithMethods()
		res = resources.Resource(dev, dev.get_x)
		lock = Lock()

		expected = [res.value] * 8

		buf = []
		delay = Quantity(0.1, SIValues.dimensions.time)

		thr = resources.AcquisitionThread(delay, buf.append, res, running_lock=lock)

		thr.start()
		time.sleep(delay.value * 4)
		lock.acquire()
		time.sleep(delay.value * 4)
		lock.release()
		time.sleep(delay.value * 4)
		thr.done = True

		eq_(buf, expected)


if __name__ == '__main__':
	unittest.main()
