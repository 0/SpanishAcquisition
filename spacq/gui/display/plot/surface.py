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

	alpha = 0.8

	def __init__(self, parent, style='surface'):
		self.style = style

		self.figure = pyplot.figure()
		self.canvas = FigureCanvas(parent, wx.ID_ANY, self.figure)

		self.axes = axes3d.Axes3D(self.figure)
		self.surface = None

	def __del__(self):
		try:
			self.close()
		except Exception:
			pass

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

	def set_surface_data(self, data):
		"""
		Set the surface data based on the data tuple.
		"""

		if self.surface is not None:
			self.axes.collections.remove(self.surface)
			self.surface = None

		if data is None:
			return

		surface_data, x_bounds, y_bounds = data

		# Number of values along each axis.
		y_num, x_num = surface_data.shape
		# The equally-spaced values along each axis.
		x_values = numpy.linspace(*x_bounds, num=x_num)
		y_values = numpy.linspace(*y_bounds, num=y_num)
		# The meshgrid of values.
		x, y = numpy.meshgrid(x_values, y_values)

		if self.style == 'surface':
			# Just a regular surface.
			self.surface = self.axes.plot_surface(x, y, surface_data, alpha=self.alpha)
		elif self.style == 'waveform':
			# Waveform style shows individual waveforms nicely.
			self.surface = self.axes.plot_wireframe(x, y, surface_data, cstride=100000)

	surface_data = property(fset=set_surface_data)

	@property
	def x_label(self):
		"""
		The x axis label.
		"""
		return self.axes.get_xlabel()

	@x_label.setter
	def x_label(self, value):
		self.axes.set_xlabel(value)

	@property
	def y_label(self):
		"""
		The y axis label.
		"""
		return self.axes.get_ylabel()

	@y_label.setter
	def y_label(self, value):
		self.axes.set_ylabel(value)

	@property
	def z_label(self):
		"""
		The z axis label.
		"""
		return self.axes.get_zlabel()

	@z_label.setter
	def z_label(self, value):
		self.axes.set_zlabel(value)

	def redraw(self):
		self.canvas.draw()
