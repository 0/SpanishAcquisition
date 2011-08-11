from nose.tools import assert_raises, eq_
from unittest import main, TestCase

from spacq.interface.units import IncompatibleDimensions, Quantity

from .. import variables


class SortVariablesTest(TestCase):
	def testEmpty(self):
		"""
		Use no variables.
		"""

		sorted_variables, num_items = variables.sort_variables([])

		eq_(sorted_variables, [])
		eq_(num_items, 0)

	def testSingle(self):
		"""
		Use a single variable.
		"""

		var = variables.OutputVariable(config=variables.LinSpaceConfig(-5.0, 5.0, 11),
				name='Name', order=0, enabled=True, const=60.0)

		sorted_variables, num_items = variables.sort_variables([var])

		eq_(sorted_variables, [(var,)])
		eq_(num_items, 11)

	def testMultiple(self):
		"""
		Use many variables.
		"""

		vars = [
			variables.OutputVariable(config=variables.LinSpaceConfig(1.0, 5.0, 3),
					name='A', order=3, enabled=True),
			variables.OutputVariable(config=variables.LinSpaceConfig(11.0, 12.0, 2),
					name='B', order=2, enabled=True, const=10.0),
			variables.OutputVariable(config=variables.LinSpaceConfig(-99.0, 0.0),
					name='D', order=1, enabled=True, const=9.0, use_const=True),
			variables.OutputVariable(config=variables.LinSpaceConfig(21.0, 25.0, 20),
					name='C', order=2, enabled=True),
			variables.OutputVariable(config=variables.LinSpaceConfig(0.0, 0.0, 1),
					name='E', order=4),
			variables.OutputVariable(
					name='F', order=5, enabled=True, const=5.5, use_const=True),
		]

		sorted_variables, num_items = variables.sort_variables(vars)

		eq_(sorted_variables, [(vars[2], vars[5]), (vars[0],), (vars[1], vars[3])])
		eq_(num_items, 6)


class OutputVariableTest(TestCase):
	def testAdjust(self):
		"""
		Try to adjust the values after initialization.
		"""

		var = variables.OutputVariable(name='Name', order=1)

		var.config = variables.LinSpaceConfig()

		var.config.steps = 1000
		eq_(var.config.steps, 1000)

		try:
			var.config.steps = -1
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		var.wait = '1e2 ms'
		eq_(var.wait, '100 ms')

		try:
			var.wait = '100 Hz'
		except IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'

	def testStr(self):
		"""
		Ensure the variable looks right.
		"""

		var = variables.OutputVariable(name='Name', order=1)

		# Very short.
		var.config = variables.LinSpaceConfig(0.0, 5.0, 3)
		var.type = 'integer'
		eq_(str(var), '[0, 2, 5]')

		# Borderline.
		var.config = variables.LinSpaceConfig(1.0, 5.0, 5)
		var.type = 'float'
		eq_(str(var), '[1, 2, 3, 4, 5]')

		# Short enough.
		var.config = variables.LinSpaceConfig(-200.0, 200.0, 401)
		eq_(str(var), '[-200, -199, -198, -197, ..., 200]')

		# Far too long.
		var.config = variables.LinSpaceConfig(0.0, 100000.0, 100001)
		eq_(str(var), '[0, 1, 2, 3, ...]')

		# Smooth from constant.
		var.smooth_from = True
		eq_(str(var), '(0, 1, 2, 3, ...]')

		# And to.
		var.smooth_to = True
		eq_(str(var), '(0, 1, 2, 3, ...)')

	def testUnits(self):
		"""
		Ensure that values are wrapped with units.
		"""

		var = variables.OutputVariable(name='Name', order=1)
		var.type = 'quantity'
		var.units = 'g.m.s-1'
		var.config = variables.LinSpaceConfig(0.0, -5.0, 3)

		eq_(list(var), [Quantity(x, 'g.m.s-1') for x in [0, -2.5, -5]])
		eq_(str(var), '[0, -2.5, -5] g.m.s-1')

		# Bad combination.
		var.units = None
		assert_raises(ValueError, list, var)


class LinSpaceConfigTest(TestCase):
	def testIterator(self):
		"""
		Create an iterator from a linear space variable.
		"""

		var = variables.OutputVariable(config=variables.LinSpaceConfig(-1.0, -3.0, 5),
				name='Name', order=1, enabled=True, const=10.0)

		# Non-const.
		eq_(len(var), 5)

		it1 = iter(var)
		eq_(list(it1), [-1.0, -1.5, -2.0, -2.5, -3.0])

		# Const.
		var.use_const = True

		eq_(len(var), 1)

		it2 = iter(var)
		eq_(list(it2), [10.0])


class ArbitraryConfigTest(TestCase):
	def testIterator(self):
		"""
		Create an iterator from an arbitrary variable.
		"""

		values = [8, -5, 6.6, 3, 0, 0]

		var = variables.OutputVariable(config=variables.ArbitraryConfig(values),
				name='Name', order=1, enabled=True)

		eq_(len(var), len(values))

		it = iter(var)
		eq_(list(it), values)


if __name__ == '__main__':
	main()
