from numpy import linspace, meshgrid, sort, unique
from scipy.interpolate import griddata

"""
Utilities for working with meshes.
"""


def triples_to_mesh(x, y, z):
	"""
	Convert 3 equal-sized lists of co-ordinates into an interpolated 2D mesh of z-values.

	Returns a tuple of:
		the mesh
		the x bounds
		the y bounds
	"""

	x_values, y_values = sort(unique(x)), sort(unique(y))

	x_space = linspace(x_values[0], x_values[-1], len(x_values))
	y_space = linspace(y_values[0], y_values[-1], len(y_values))

	target_x, target_y = meshgrid(x_space, y_space)

	target_z = griddata((x, y), z, (target_x, target_y), method='cubic')

	return (target_z, (x_values[0], x_values[-1]), (y_values[0], y_values[-1]))
