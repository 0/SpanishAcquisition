from chaco.api import ArrayPlotData, ColorBar, HPlotContainer, jet, LinearMapper
from chaco.tools.api import RangeSelection, RangeSelectionOverlay
from enable.api import Window

from .common.chaco_plot import ChacoPlot

"""
An embeddable colormapped plot.
"""


class ColormappedPlot(ChacoPlot):
	"""
	A colormapped plot.
	"""

	def __init__(self, parent, x_bounds, y_bounds, *args, **kwargs):
		self.parent = parent

		self.data = ArrayPlotData()
		self.data.set_data('color', [[0]])

		ChacoPlot.__init__(self, self.data, *args, **kwargs)

		self.img_plot('color', colormap=jet, xbounds=x_bounds, ybounds=y_bounds)

		self.configure()

	@property
	def plot_obj(self):
		"""
		The actual plot object.
		"""

		return self.plots.values()[0][0]

	@property
	def control(self):
		"""
		A drawable control with a color bar.
		"""

		color_map = self.plot_obj.color_mapper
		linear_mapper = LinearMapper(range=color_map.range)
		color_bar = ColorBar(index_mapper=linear_mapper, color_mapper=color_map, plot=self.plot_obj,
				orientation='v', resizable='v', width=30)
		color_bar._axis.tick_label_formatter = self.sci_formatter
		color_bar.padding_top = self.padding_top
		color_bar.padding_bottom = self.padding_bottom
		color_bar.padding_left = 50 # Room for labels.
		color_bar.padding_right = 10

		range_selection = RangeSelection(component=color_bar)
		range_selection.listeners.append(self.plot_obj)
		color_bar.tools.append(range_selection)

		range_selection_overlay = RangeSelectionOverlay(component=color_bar)
		color_bar.overlays.append(range_selection_overlay)

		container = HPlotContainer(use_backbuffer=True)
		container.add(self)
		container.add(color_bar)

		return Window(self.parent, component=container).control

	@property
	def color_data(self):
		"""
		Plotted values.
		"""

		return self.data.get_data('color')

	@color_data.setter
	def color_data(self, values):
		self.data.set_data('color', values)

	@property
	def low_setting(self):
		"""
		Lowest color value.
		"""

		return self.plot_obj.color_mapper.range.low

	@low_setting.setter
	def low_setting(self, value):
		self.plot_obj.color_mapper.range.low_setting = value

	@property
	def high_setting(self):
		"""
		Highest color value.
		"""

		return self.plot_obj.color_mapper.range.high

	@high_setting.setter
	def high_setting(self, value):
		self.plot_obj.color_mapper.range.high_setting = value
