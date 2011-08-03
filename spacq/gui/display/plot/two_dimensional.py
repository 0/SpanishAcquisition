from chaco.api import ArrayPlotData
from enable.api import Window
from functools import partial

from .common.chaco_plot import ChacoPlot

"""
An embeddable two-dimensional plot.
"""


class TwoDimensionalPlot(ChacoPlot):
	"""
	A 2D plot.
	"""

	auto_color_idx = 0
	auto_color_list = ['green', 'brown', 'blue', 'red', 'black']

	@classmethod
	def auto_color(cls):
		"""
		Choose the next color.
		"""

		color = cls.auto_color_list[cls.auto_color_idx]
		cls.auto_color_idx = (cls.auto_color_idx + 1) % len(cls.auto_color_list)

		return color

	def __init__(self, parent, color=None, *args, **kwargs):
		self.parent = parent

		if color is None:
			color = self.auto_color()

		self.data = ArrayPlotData()
		self.data.set_data('x', [0])
		self.data.set_data('y', [0])

		ChacoPlot.__init__(self, self.data, *args, **kwargs)

		self.plot(('x', 'y'), color=color)

		self.configure()

	@property
	def control(self):
		"""
		A drawable control.
		"""

		return Window(self.parent, component=self).control

	def get_data(self, axis):
		"""
		Values for an axis.
		"""

		return self.data.get_data(axis)

	def set_data(self, values, axis):
		self.data.set_data(axis, values)

	x_data = property(partial(get_data, axis='x'), partial(set_data, axis='x'))
	y_data = property(partial(get_data, axis='y'), partial(set_data, axis='y'))

	def x_autoscale(self):
		"""
		Enable autoscaling for the x axis.
		"""

		x_range = self.plots.values()[0][0].index_mapper.range
		x_range.low = x_range.high = 'auto'

	def y_autoscale(self):
		"""
		Enable autoscaling for the y axis.
		"""

		y_range = self.plots.values()[0][0].value_mapper.range
		y_range.low = y_range.high = 'auto'
