from nose.tools import eq_
from numpy import linspace
from threading import Lock
import time
import unittest

from spacq.tests.tools import AssertHandler

from ..units import Quantity

from .. import resources


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
		eq_(res2.convert('5') / 2, 2)
		eq_(res3.convert('5') / 2, 2.5)

	def testAllowedValues(self):
		"""
		Verify that only allowed values are allowed.
		"""

		allowed = set([5, 10, 15])

		dev = WithAttribute()
		res = resources.Resource(dev, 'x', 'x', allowed_values=allowed)

		for value in allowed:
			res.value = value
			eq_(res.value, value)

		try:
			res.value = -5
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError'

		eq_(res.allowed_values, allowed)

	def testWrapping(self):
		"""
		Wrap resources in other resources, and then undo.
		"""

		dev = WithAttribute()
		res1 = resources.Resource(dev, 'x', 'x')

		res1.value = 5
		eq_(res1.value, 5)

		# Wrap once.
		res2 = res1.wrapped('wrapper1', lambda x: 2 * x, lambda x: 3 * x)

		eq_(res2.value, 10)
		res2.value = 5
		eq_(res1.value, 15)
		eq_(res2.value, 30)

		# Wrap again.
		res3 = res2.wrapped('wrapper2', lambda x: 5 * x)

		eq_(res3.value, 150)
		res3.value = 10
		eq_(res1.value, 30)
		eq_(res2.value, 60)
		eq_(res3.value, 300)

		# Unwrap.
		res4 = res3.unwrapped('wrapper1')

		eq_(res4.value, 150)
		res4.value = 7
		eq_(res1.value, 7)
		eq_(res2.value, 14)
		eq_(res3.value, 70)
		eq_(res4.value, 35)

		# Modify the original Resource.
		res1.value = 1
		eq_(res1.value, 1)
		eq_(res2.value, 2)
		eq_(res3.value, 10)
		eq_(res4.value, 5)

		assert not res1.is_wrapped_by('wrapper1')
		assert not res1.is_wrapped_by('wrapper2')
		assert     res2.is_wrapped_by('wrapper1')
		assert not res2.is_wrapped_by('wrapper2')
		assert     res3.is_wrapped_by('wrapper1')
		assert     res3.is_wrapped_by('wrapper2')
		assert not res4.is_wrapped_by('wrapper1')
		assert     res4.is_wrapped_by('wrapper2')

	def testSweep(self):
		"""
		Ramp up and down.
		"""

		buf = None
		def setter(value):
			if abs(value) > 10:
				raise ValueError(value)

			buf.append(value)

		exceptions = None
		def exception_callback(e):
			exceptions.append(tuple(e))

		res = resources.Resource(setter=setter)

		# Check the values.
		buf = []
		res.sweep(1.0, 5.0, 5)
		eq_(buf, list(linspace(1.0, 5.0, 5)))

		# Check the time.
		buf = []
		start_time = time.time()
		res.sweep(-5.0, 5.0, 11, delay=0.05)
		time_diff = time.time() - start_time
		assert time_diff > 0.55
		assert time_diff < 0.75
		eq_(buf, list(linspace(-5.0, 5.0, 11)))

		# Check the exceptions.
		buf = []
		exceptions = []
		res.sweep(9.0, 12.0, 4, delay=0.05, exception_callback=exception_callback)
		res.sweep(-15.0, 0.0, 3, delay=0.05, exception_callback=exception_callback)
		eq_(buf, list(linspace(9.0, 10.0, 2)))
		eq_(exceptions, [(11.0,), (-15.0,)])


class AcquisitionThreadTest(unittest.TestCase):
	def testWithoutResource(self):
		"""
		Let the thread run without a resource.
		"""

		buf = []
		delay = Quantity(30, 'ms')
		
		thr = resources.AcquisitionThread(delay, buf.append)

		thr.start()
		time.sleep(delay.value * 5)
		thr.done = True

		eq_(buf, [])

	def testWithResource(self):
		"""
		Let the thread run with a resource.
		"""

		dev = WithMethods()
		res = resources.Resource(dev, dev.get_x)

		expected = [res.value] * 5

		buf = []
		delay = Quantity(30, 'ms')

		thr = resources.AcquisitionThread(delay, buf.append, res)

		thr.start()
		time.sleep(delay.value * 5)
		thr.done = True

		eq_(buf, expected)

	def testWithLock(self):
		"""
		Pause the thread with a lock.
		"""

		dev = WithMethods()
		res = resources.Resource(dev, dev.get_x)
		lock = Lock()

		expected = [res.value] * 4

		buf = []
		delay = Quantity(30, 'ms')

		thr = resources.AcquisitionThread(delay, buf.append, res, running_lock=lock)

		thr.start()
		time.sleep(delay.value * 2)
		lock.acquire()
		time.sleep(delay.value * 2)
		lock.release()
		time.sleep(delay.value * 2)
		thr.done = True

		eq_(buf, expected)

	def testWithUnreadableResource(self):
		"""
		Watch the errors come rolling in.
		"""

		res = resources.Resource()

		buf = []
		delay = Quantity(30, 'ms')

		thr = resources.AcquisitionThread(delay, buf.append, res)

		log = AssertHandler()

		thr.start()
		time.sleep(delay.value * 5)
		thr.done = True

		log.assert_logged('error', 'not readable')

		eq_(buf, [])


if __name__ == '__main__':
	unittest.main()
