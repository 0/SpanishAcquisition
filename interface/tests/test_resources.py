from nose.tools import eq_
import unittest

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

		try:
			res.value = 5
		except resources.NotWritable:
			pass
		else:
			assert False, 'Expected NotWritable.'

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
		res._getter = 'x'
		res._setter = 'x'

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


if __name__ == '__main__':
	unittest.main()
