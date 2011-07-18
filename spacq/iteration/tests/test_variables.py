from nose.tools import eq_
import unittest

from spacq.interface.units import IncompatibleDimensions

from .. import variables


class SortVariablesTest(unittest.TestCase):
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
		]

		sorted_variables, num_items = variables.sort_variables(vars)

		eq_(sorted_variables, [(vars[0],), (vars[1], vars[3]), (vars[2],)])
		eq_(num_items, 6)


class OutputVariableTest(unittest.TestCase):
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
		eq_(str(var), '[0, 2.5, 5]')

		# Borderline.
		var.config = variables.LinSpaceConfig(1.0, 5.0, 5)
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


class LinSpaceConfigTest(unittest.TestCase):
	def testIterator(self):
		"""
		Create an iterator from a linear space variable.
		"""

		var = variables.OutputVariable(config=variables.LinSpaceConfig(-1.0, -3.0, 5),
				name='Name', order=1, enabled=True, const=10.0)

		# Non-const.
		eq_(len(var), 5)

		it1 = var.iterator
		eq_(list(it1), [-1.0, -1.5, -2.0, -2.5, -3.0])

		# Const.
		var.use_const = True

		eq_(len(var), 1)

		it2 = var.iterator
		eq_(list(it2), [10.0])


if __name__ == '__main__':
	unittest.main()
