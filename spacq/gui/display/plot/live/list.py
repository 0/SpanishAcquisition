import logging
log = logging.getLogger(__name__)

import numpy
from pubsub import pub
import wx

from ....config.measurement import MeasurementConfigPanel
from ....tool.box import Dialog, MessageDialog

try:
	from ..surface import SurfacePlot
except ImportError as e:
	plot_available = False
	log.debug('Could not import SurfacePlot: {0}'.format(str(e)))
else:
	plot_available = True

"""
A historical live view plot for list values.
"""


class PlotSettings(object):
	"""
	Wrapper for all the settings configured via dialog.
	"""

	def __init__(self):
		self.enabled = plot_available
		self.num_lines = 100


class PlotSettingsDialog(Dialog):
	"""
	Set up the live view plot.
	"""

	def __init__(self, parent, ok_callback, *args, **kwargs):
		Dialog.__init__(self, parent=parent, title='Plot settings')

		self.ok_callback = ok_callback

		dialog_box = wx.BoxSizer(wx.VERTICAL)

		# Enabled.
		self.enabled_checkbox = wx.CheckBox(self, label='Enabled')
		if not plot_available:
			self.enabled_checkbox.Disable()
		dialog_box.Add(self.enabled_checkbox, flag=wx.ALL, border=5)

		# Capture.
		capture_static_box = wx.StaticBox(self, label='Capture')
		capture_box = wx.StaticBoxSizer(capture_static_box, wx.VERTICAL)
		capture_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=5)
		capture_box.Add(capture_sizer, flag=wx.CENTER)
		dialog_box.Add(capture_box, flag=wx.EXPAND|wx.ALL, border=5)

		## Number of lines.
		capture_sizer.Add(wx.StaticText(self, label='Lines:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.lines_input = wx.SpinCtrl(self, min=2, max=1e4, initial=100)
		capture_sizer.Add(self.lines_input, flag=wx.CENTER)

		# End buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER)

		ok_button = wx.Button(self, wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
		button_box.Add(ok_button)

		cancel_button = wx.Button(self, wx.ID_CANCEL)
		button_box.Add(cancel_button)

		self.SetSizerAndFit(dialog_box)

	def OnOk(self, evt=None):
		self.ok_callback(self)

		self.Destroy()

	def GetValue(self):
		plot_settings = PlotSettings()
		plot_settings.enabled = self.enabled_checkbox.Value
		plot_settings.num_lines = self.lines_input.Value

		return plot_settings

	def SetValue(self, plot_settings):
		self.enabled_checkbox.Value = plot_settings.enabled
		self.lines_input.Value = plot_settings.num_lines


class ListLiveViewPanel(wx.Panel):
	"""
	A panel to display a live view plot of a list resource.
	"""

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self._measurement_resource_name = None

		# Defaults.
		self.plot_settings = PlotSettings()

		self.enabled = False
		self.capturing_data = False
		self.resource_backup = None

		# Initialize recorded values.
		self.init_values()

		# Plot and toolbar.
		display_box = wx.BoxSizer(wx.VERTICAL)

		## Plot.
		if plot_available:
			self.plot = SurfacePlot(self, style='waveform')
			display_box.Add(self.plot.control, proportion=1, flag=wx.EXPAND)

			self.plot.x_label = 'Waveform time (s)'
			self.plot.y_label = 'History'
		else:
			display_box.Add((500, -1), proportion=1, flag=wx.EXPAND)

		## Controls.
		if plot_available:
			controls_box = wx.BoxSizer(wx.HORIZONTAL)
			display_box.Add(controls_box, flag=wx.CENTER|wx.ALL, border=5)

			### Capture.
			capture_static_box = wx.StaticBox(self, label='Control')
			capture_box = wx.StaticBoxSizer(capture_static_box)
			controls_box.Add(capture_box, flag=wx.CENTER)

			self.reset_button = wx.Button(self, label='Reset')
			self.Bind(wx.EVT_BUTTON, self.OnReset, self.reset_button)
			capture_box.Add(self.reset_button, flag=wx.CENTER)

			### Settings.
			settings_static_box = wx.StaticBox(self, label='Settings')
			settings_box = wx.StaticBoxSizer(settings_static_box, wx.HORIZONTAL)
			controls_box.Add(settings_box, flag=wx.CENTER|wx.LEFT, border=10)

			self.plot_settings_button = wx.Button(self, label='Plot...')
			self.Bind(wx.EVT_BUTTON, self.OnPlotSettings, self.plot_settings_button)
			settings_box.Add(self.plot_settings_button, flag=wx.CENTER)

		self.SetSizer(display_box)

		# Subscriptions.
		pub.subscribe(self.msg_data_capture_start, 'data_capture.start')
		pub.subscribe(self.msg_data_capture_data, 'data_capture.data')
		pub.subscribe(self.msg_data_capture_stop, 'data_capture.stop')

	@property
	def measurement_resource_name(self):
		if self._measurement_resource_name is None:
			return ''
		else:
			return self._measurement_resource_name

	@measurement_resource_name.setter
	def measurement_resource_name(self, value):
		if value:
			self._measurement_resource_name = value
			try:
				self.resource = self.global_store.resources[self._measurement_resource_name]
			except KeyError:
				self.resource = None
		else:
			self._measurement_resource_name = None
			self.resource = None

	def init_values(self):
		"""
		Clear captured values.
		"""

		self._lines = None
		self.time_range = (0.0, 0.0)

	def update_plot(self):
		"""
		Redraw the plot.
		"""

		# Wait for at least one line.
		if self._lines is None:
			self.plot.surface_data = None
		else:
			self.plot.surface_data = (self._lines, self.time_range, (1, len(self._lines)))

		wx.CallAfter(self.plot.redraw)

	def add_values(self, values):
		"""
		Update the plot with a new list of values.
		"""

		if not self.plot_settings.enabled:
			return

		# Extract the times and the data values.
		times, values = zip(*values)
		time_range = min(times), max(times)

		# Sanity check, since the new values must match existing ones.
		if self._lines is not None:
			if len(self._lines[-1]) != len(values):
				log.warning('Data length mismatch: was {0}, became {1}'.format(len(self._lines[-1]), len(values)))
				self.init_values()
			elif self.time_range != time_range:
				log.warning('Time range mismatch: was {0}, became {1}'.format(self.time_range, time_range))
				self.init_values()

		# Update values.
		if self._lines is None:
			self._lines = numpy.array([values])
			self.time_range = time_range
		else:
			self._lines = numpy.append(self._lines, [values], 0)

		cut_idx = len(self._lines) - self.plot_settings.num_lines
		if cut_idx > 0:
			self._lines = self._lines[cut_idx:]

		# Plot.
		self.update_plot()

	def close(self):
		"""
		Perform cleanup.
		"""

		# Unsubscriptions.
		pub.unsubscribe(self.msg_data_capture_start, 'data_capture.start')
		pub.unsubscribe(self.msg_data_capture_data, 'data_capture.data')
		pub.unsubscribe(self.msg_data_capture_stop, 'data_capture.stop')

	def OnReset(self, evt=None):
		self.init_values()
		self.update_plot()

	def OnPlotSettings(self, evt=None):
		"""
		Open the plot settings dialog.
		"""

		def ok_callback(dlg):
			self.plot_settings = dlg.GetValue()

		dlg = PlotSettingsDialog(self, ok_callback)
		dlg.SetValue(self.plot_settings)
		dlg.Show()

	def msg_data_capture_start(self, name):
		if name == self.measurement_resource_name:
			if self.enabled:
				self.capturing_data = True

	def msg_data_capture_data(self, name, value):
		if name == self.measurement_resource_name:
			if self.capturing_data:
				self.add_values(value)

	def msg_data_capture_stop(self, name):
		if name == self.measurement_resource_name:
			if self.capturing_data:
				self.capturing_data = False


class ListMeasurementFrame(wx.Frame):
	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Measurement setup.
		self.measurement_config_panel = MeasurementConfigPanel(self, global_store, scaling=False)
		frame_box.Add(self.measurement_config_panel, flag=wx.EXPAND)

		## Live view.
		self.live_view_panel = ListLiveViewPanel(self, global_store)
		frame_box.Add(self.live_view_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnClose(self, evt):
		if self.live_view_panel.capturing_data:
			msg = 'Cannot close, as a sweep is currently in progress.'
			MessageDialog(self, msg, 'Sweep in progress').Show()

			evt.Veto()
			return

		self.measurement_config_panel.close()
		self.live_view_panel.close()

		evt.Skip()
