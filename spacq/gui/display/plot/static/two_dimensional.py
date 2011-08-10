import wx

from ....tool.box import MessageDialog
from ..two_dimensional import TwoDimensionalPlot
from .common.plot_setup import PlotSetupDialog


class TwoDimensionalPlotPanel(wx.Panel):
	def __init__(self, parent, x_data, y_data, x_label, y_label, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Plot.
		self.plot = TwoDimensionalPlot(self)
		panel_box.Add(self.plot.control, proportion=1, flag=wx.EXPAND)

		self.SetSizer(panel_box)

		self.plot.x_label, self.plot.y_label = x_label, y_label
		self.plot.x_data, self.plot.y_data = x_data, y_data


class TwoDimensionalPlotFrame(wx.Frame):
	def __init__(self, parent, x_data, y_data, x_label, y_label, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Plot panel.
		panel = TwoDimensionalPlotPanel(self, x_data, y_data, x_label, y_label)
		panel.SetMinSize((400, 300))
		frame_box.Add(panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)


class TwoDimensionalPlotSetupDialog(PlotSetupDialog):
	def __init__(self, parent, headings, data, *args, **kwargs):
		PlotSetupDialog.__init__(self, parent, headings, ['x', 'y'],
				*args, **kwargs)

		self.parent = parent
		self.headings = headings
		self.data = data

	def make_plot(self):
		try:
			x_data, y_data = [self.data[:,axis].astype(float) for axis in self.axes]
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return

		x_label, y_label = [self.headings[x] for x in self.axes]
		title = '{0} vs {1}'.format(y_label, x_label)

		frame = TwoDimensionalPlotFrame(self.parent, x_data, y_data,
				x_label, y_label, title=title)
		frame.Show()

		return True
