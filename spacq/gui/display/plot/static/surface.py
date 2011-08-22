from numpy import array
import wx

from spacq.interface.list_columns import ListParser
from spacq.tool.box import triples_to_mesh

from ....tool.box import MessageDialog
from ..surface import SurfacePlot
from .common.plot_setup import PlotSetupDialog


class SurfacePlotPanel(wx.Panel):
	def __init__(self, parent, surface_data, x_bounds, y_bounds, x_label, y_label, z_label,
			style, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Plot.
		self.plot = SurfacePlot(self, style=style)
		panel_box.Add(self.plot.control, proportion=1, flag=wx.EXPAND)

		self.SetSizer(panel_box)

		self.plot.x_label, self.plot.y_label, self.plot.z_label = x_label, y_label, z_label
		self.plot.surface_data = (surface_data, x_bounds, y_bounds)


class SurfacePlotFrame(wx.Frame):
	def __init__(self, parent, surface_data, x_bounds, y_bounds, x_label, y_label, z_label,
			style, *args, **kwargs):
		wx.Frame.__init__(self,  parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Plot panel.
		self.panel = SurfacePlotPanel(self, surface_data, x_bounds, y_bounds, x_label,
				y_label, z_label, style)
		frame_box.Add(self.panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnClose(self, evt):
		self.panel.plot.close()

		evt.Skip()


class SurfacePlotSetupDialog(PlotSetupDialog):
	def __init__(self, parent, headings, data, *args, **kwargs):
		PlotSetupDialog.__init__(self, parent, headings, ['x', 'y', 'z'],
				*args, **kwargs)

		self.parent = parent
		self.headings = headings
		self.data = data

	def make_plot(self):
		try:
			x_data, y_data, z_data = [self.data[:,axis].astype(float) for axis in self.axes]
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return

		try:
			surface_data, x_bounds, y_bounds, _ = triples_to_mesh(x_data, y_data, z_data)
		except Exception as e:
			MessageDialog(self, str(e), 'Conversion failure').Show()
			return

		x_label, y_label, z_label = [self.headings[x] for x in self.axes]
		title = '{0} vs ({1}, {2})'.format(z_label, x_label, y_label)

		frame = SurfacePlotFrame(self.parent, surface_data, x_bounds, y_bounds,
				x_label, y_label, z_label, title=title, style='surface')
		frame.Show()

		return True


class WaveformsPlotSetupDialog(PlotSetupDialog):
	def __init__(self, parent, headings, data, *args, **kwargs):
		PlotSetupDialog.__init__(self, parent, headings, ['z'],
				*args, **kwargs)

		self.parent = parent
		self.headings = headings
		self.data = data

	def make_plot(self):
		axis = self.axes[0]
		lp = ListParser()

		try:
			surface_data = array([[x[1] for x in lp(row)] for row in self.data[:,axis]])
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return

		x_axis = [x[0] for x in lp(self.data[:,axis][0])]
		x_bounds = (x_axis[0], x_axis[-1])

		x_label, y_label, z_label = 'Waveform (s)', 'History', self.headings[axis]
		title = '{0} vs ({1}, {2})'.format(z_label, x_label, y_label)

		frame = SurfacePlotFrame(self.parent, surface_data, x_bounds, (1, len(surface_data)),
				x_label, y_label, z_label, title=title, style='waveform')
		frame.Show()

		return True
