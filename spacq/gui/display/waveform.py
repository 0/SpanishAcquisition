from numpy import linspace
import wx

from .plot.two_dimensional import TwoDimensionalPlot


class WaveformDisplay(TwoDimensionalPlot):
	def __init__(self, parent, *args, **kwargs):
		TwoDimensionalPlot.__init__(self, parent, *args, **kwargs)

		self.padding_left = 50

	@property
	def control(self):
		return TwoDimensionalPlot.control.__get__(self)


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
		self.waveform_plot.x_data = linspace(0, len(waveform) / frequency.value, len(waveform))
		self.waveform_plot.y_data = waveform

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
