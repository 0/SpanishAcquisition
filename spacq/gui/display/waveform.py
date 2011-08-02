from chaco.api import VPlotContainer
from enable.api import Window
from math import floor, log10
from numpy import linspace
import wx

from spacq.interface.units import SIValues

from .plot.two_dimensional import TwoDimensionalPlot


class WaveformDisplay(TwoDimensionalPlot):
	marker_height = 50

	def __init__(self, parent, *args, **kwargs):
		TwoDimensionalPlot.__init__(self, parent, *args, **kwargs)

		self.padding_left = 50

		self.title = 'Waveform'

		self.vplot_container = VPlotContainer(use_backbuffer=True)
		self.vplot_container.stack_order = 'top_to_bottom'
		self.vplot_container.add(self)

	@property
	def control(self):
		return Window(self.parent, component=self.vplot_container).control

	def add_marker(self, num, data):
		marker_plot = TwoDimensionalPlot(self, height=self.marker_height, resizable='h')
		marker_plot.padding_left = self.padding_left

		marker_plot.x_data = self.x_data
		marker_plot.y_data = data
		marker_plot.title = 'Marker {0}'.format(num)

		# Synchronize with waveform plot.
		marker_plot.index_range = self.index_range

		self.vplot_container.add(marker_plot)


class WaveformPanel(wx.Panel):
	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Waveform plot.
		self.waveform_plot = WaveformDisplay(self)
		panel_box.Add(self.waveform_plot.control, proportion=1, flag=wx.EXPAND)

		self.SetSizer(panel_box)

	def SetValue(self, waveform, marker_data, frequency):
		max_time = len(waveform) / frequency.value
		# Find the order of magnitude (to within 3 orders, to keep it at n, u, m, etc).
		magnitude = 3 * floor(floor(log10(max_time)) / 3)

		self.waveform_plot.x_data = linspace(0, max_time / (10 ** magnitude), len(waveform))
		self.waveform_plot.y_data = waveform

		self.waveform_plot.x_label = '{0}s'.format(SIValues.prefixes_[magnitude])

		for num, data in marker_data.items():
			self.waveform_plot.add_marker(num, data)

		self.waveform_plot.x_autoscale()
		self.waveform_plot.y_autoscale()


class WaveformFrame(wx.Frame):
	def __init__(self, parent, output_name, *args, **kwargs):
		wx.Frame.__init__(self, parent, title=output_name, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		self.panel = WaveformPanel(self)
		self.panel.SetMinSize((600, 400))
		frame_box.Add(self.panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

	def SetValue(self, *args):
		self.panel.SetValue(*args)
