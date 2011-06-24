from nose.tools import eq_
from numpy import append, linspace, repeat
from numpy.testing import assert_array_equal, assert_array_almost_equal
import unittest

from .. import mesh


class TriplesToMeshTest(unittest.TestCase):
	def testSimple(self):
		"""
		No interpolation required.
		"""

		x = [1, 2, 3, 4] * 3 # [1, 2, 3, 4, 1, ...]
		y = repeat([5, 6, 7], 4) # [5, 5, 5, 5, 6, ...]
		z = linspace(0, -11, 12) # [0, -1, -2, -3, ...]

		result, x_bounds, y_bounds = mesh.triples_to_mesh(x, y, z)

		assert_array_equal(result, z.reshape(3, 4))
		eq_(x_bounds, (1, 4))
		eq_(y_bounds, (5, 7))

	def testInterpolated(self):
		"""
		Some interpolation required.
		"""

		x = [0, 0, 0.25, 1, 1]
		y = [0, 1,    0, 0, 1]
		z = [1, 2,  1.5, 3, 4]

		result, x_bounds, y_bounds = mesh.triples_to_mesh(x, y, z)

		expected = [
			[1, 2, 3],
			[2, 3, 4],
		]

		assert_array_almost_equal(result, expected)
		eq_(x_bounds, (0, 1))
		eq_(y_bounds, (0, 1))
