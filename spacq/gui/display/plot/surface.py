from matplotlib import pyplot
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from mpl_toolkits.mplot3d import axes3d
import numpy
import wx

"""
An embeddable three-dimensional surface plot.
"""


class SurfacePlot(object):
	"""
	A surface plot.
	"""

	def __init__(self, parent, surface_data, x_bounds, y_bounds):
		# Number of values along each axis.
		y_num, x_num = surface_data.shape
		# The equally-spaced values along each axis.
		x_values = numpy.linspace(*x_bounds, num=x_num)
		y_values = numpy.linspace(*y_bounds, num=y_num)
		# The meshgrid of values.
		x, y = numpy.meshgrid(x_values, y_values)

		self.figure = pyplot.figure()
		self.canvas = FigureCanvas(parent, wx.ID_ANY, self.figure)

		self.axes = axes3d.Axes3D(self.figure)
		self.axes.plot_surface(x, y, surface_data, alpha=0.8)

	@property
	def control(self):
		"""
		A drawable control.
		"""

		return self.canvas

	def close(self):
		"""
		Inform pyplot that this figure is no longer required.
		"""

		pyplot.close(self.figure.number)

	def set_x_label(self, value):
		"""
		Set the x axis label.
		"""

		self.axes.set_xlabel(value)

	x_label = property(fset=set_x_label)

	def set_y_label(self, value):
		"""
		Set the y axis label.
		"""

		self.axes.set_ylabel(value)

	y_label = property(fset=set_y_label)

	def set_z_label(self, value):
		"""
		Set the z axis label.
		"""

		self.axes.set_zlabel(value)

	z_label = property(fset=set_z_label)
