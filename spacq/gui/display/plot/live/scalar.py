import logging
log = logging.getLogger(__name__)

import functools
import math
import numpy
from pubsub import pub
from threading import Lock
import time
import wx
from wx.lib.agw import floatspin

from spacq.interface.resources import AcquisitionThread
from spacq.interface.units import Quantity

from ....config.measurement import MeasurementConfigPanel
from ....tool.box import Dialog, MessageDialog

try:
	from ..two_dimensional import TwoDimensionalPlot
except ImportError as e:
	plot_available = False
	log.debug('Could not import TwoDimensionalPlot: {0}'.format(str(e)))
else:
	plot_available = True

"""
A historical live view plot for scalar values.
"""


class PlotSettings(object):
	"""
	Wrapper for all the settings configured via dialog.
	"""

	def __init__(self):
		self.enabled = plot_available
		self.num_points = 500
		self.delay = Quantity(0.2, 's')
		self.update_x = True
		self.time_value = 0
		self.time_mode = 0
		self.update_y = True
		self.y_scale = 0
		self.units_from = ''
		self.units_to = ''


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

		## Number of points.
		capture_sizer.Add(wx.StaticText(self, label='Points:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.points_input = wx.SpinCtrl(self, min=2, max=1e4, initial=100)
		capture_sizer.Add(self.points_input, flag=wx.CENTER)

		## Delay.
		capture_sizer.Add(wx.StaticText(self, label='Delay (s):'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		# TODO: Input should be a time amount directly (eg. '200 ms').
		self.delay_input = floatspin.FloatSpin(self, min_val=0.2, max_val=1e4, increment=0.1, digits=2)
		capture_sizer.Add(self.delay_input, flag=wx.CENTER)

		# Axes.
		axes_static_box = wx.StaticBox(self, label='Axes')
		axes_box = wx.StaticBoxSizer(axes_static_box, wx.HORIZONTAL)
		dialog_box.Add(axes_box, flag=wx.EXPAND|wx.ALL, border=5)

		## x
		x_static_box = wx.StaticBox(self, label='x')
		x_box = wx.StaticBoxSizer(x_static_box, wx.VERTICAL)
		axes_box.Add(x_box, flag=wx.EXPAND)

		self.update_x_axis = wx.CheckBox(self, label='Autofit')
		x_box.Add(self.update_x_axis)

		### Value.
		self.time_value = wx.RadioBox(self, label='Value', choices=['Time', 'Points'])
		x_box.Add(self.time_value, flag=wx.EXPAND)

		### Mode.
		self.time_mode = wx.RadioBox(self, label='Mode', choices=['Relative', 'Absolute'])
		x_box.Add(self.time_mode, flag=wx.EXPAND)

		## y
		y_static_box = wx.StaticBox(self, label='y')
		y_box = wx.StaticBoxSizer(y_static_box, wx.VERTICAL)
		axes_box.Add(y_box, flag=wx.EXPAND)

		self.update_y_axis = wx.CheckBox(self, label='Autofit')
		y_box.Add(self.update_y_axis)

		### Conversion.
		conversion_static_box = wx.StaticBox(self, label='Conversion')
		conversion_box = wx.StaticBoxSizer(conversion_static_box, wx.VERTICAL)
		conversion_sizer = wx.FlexGridSizer(rows=1, cols=2, hgap=5)
		conversion_box.Add(conversion_sizer)
		y_box.Add(conversion_box)

		conversion_sizer.Add(wx.StaticText(self, label='Exp. scale:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.y_scale = floatspin.FloatSpin(self, min_val=-100, max_val=100, increment=1, digits=2)
		conversion_sizer.Add(self.y_scale)

		#### Units.
		units_static_box = wx.StaticBox(self, label='Units')
		units_box = wx.StaticBoxSizer(units_static_box, wx.VERTICAL)
		units_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=5)
		units_box.Add(units_sizer)
		conversion_box.Add(units_box, flag=wx.EXPAND)

		units_sizer.Add(wx.StaticText(self, label='From:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.units_from_input = wx.TextCtrl(self)
		units_sizer.Add(self.units_from_input)

		units_sizer.Add(wx.StaticText(self, label='To:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.units_to_input = wx.TextCtrl(self)
		units_sizer.Add(self.units_to_input)

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
		plot_settings.num_points = self.points_input.Value
		plot_settings.delay = Quantity(self.delay_input.GetValue(), 's')
		plot_settings.update_x = self.update_x_axis.Value
		plot_settings.time_value = self.time_value.Selection
		plot_settings.time_mode = self.time_mode.Selection
		plot_settings.update_y = self.update_y_axis.Value
		plot_settings.y_scale = self.y_scale.GetValue()
		plot_settings.units_from = self.units_from_input.Value
		plot_settings.units_to = self.units_to_input.Value

		return plot_settings

	def SetValue(self, plot_settings):
		self.enabled_checkbox.Value = plot_settings.enabled
		self.points_input.Value = plot_settings.num_points
		self.delay_input.SetValue(plot_settings.delay.value)
		self.update_x_axis.Value = plot_settings.update_x
		self.time_value.Selection = plot_settings.time_value
		self.time_mode.Selection = plot_settings.time_mode
		self.update_y_axis.Value = plot_settings.update_y
		self.y_scale.SetValue(plot_settings.y_scale)
		self.units_from_input.Value = plot_settings.units_from
		self.units_to_input.Value = plot_settings.units_to


class ScalarLiveViewPanel(wx.Panel):
	"""
	A panel to display a live view plot of a scalar resource.
	"""

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self._measurement_resource_name = None

		# Defaults.
		self.plot_settings = PlotSettings()
		self.unit_conversion = 0

		self.enabled = False
		self.capturing_data = False
		self.restart_live_view = False
		self.resource_backup = None

		# This lock blocks the acquisition thread from acquiring.
		self.running_lock = Lock()

		# Initialize recorded values.
		self.init_values()

		# Plot and toolbar.
		display_box = wx.BoxSizer(wx.VERTICAL)

		## Plot.
		if plot_available:
			self.plot = TwoDimensionalPlot(self, color='blue')
			display_box.Add(self.plot.control, proportion=1, flag=wx.EXPAND)

			self.plot.x_label = 'Time (s)'
		else:
			display_box.Add((500, -1), proportion=1, flag=wx.EXPAND)

		## Controls.
		if plot_available:
			controls_box = wx.BoxSizer(wx.HORIZONTAL)
			display_box.Add(controls_box, flag=wx.CENTER|wx.ALL, border=5)

			### Numeric display.
			numeric_display_static_box = wx.StaticBox(self, label='Reading')
			numeric_display_box = wx.StaticBoxSizer(numeric_display_static_box, wx.HORIZONTAL)
			controls_box.Add(numeric_display_box, flag=wx.CENTER)

			self.numeric_display = wx.TextCtrl(self, size=(100, -1), style=wx.TE_READONLY)
			self.numeric_display.BackgroundColour = wx.LIGHT_GREY
			numeric_display_box.Add(self.numeric_display)

			### Capture.
			capture_static_box = wx.StaticBox(self, label='Control')
			capture_box = wx.StaticBoxSizer(capture_static_box)
			controls_box.Add(capture_box, flag=wx.CENTER|wx.LEFT, border=10)

			self.run_button = wx.Button(self, label='Run')
			self.Bind(wx.EVT_BUTTON, self.OnRun, self.run_button)
			capture_box.Add(self.run_button, flag=wx.CENTER)

			self.pause_button = wx.Button(self, label='Pause')
			self.Bind(wx.EVT_BUTTON, self.OnPause, self.pause_button)
			capture_box.Add(self.pause_button, flag=wx.CENTER)

			self.reset_button = wx.Button(self, label='Reset')
			self.Bind(wx.EVT_BUTTON, self.OnReset, self.reset_button)
			capture_box.Add(self.reset_button, flag=wx.CENTER|wx.LEFT, border=10)

			### Settings.
			settings_static_box = wx.StaticBox(self, label='Settings')
			settings_box = wx.StaticBoxSizer(settings_static_box, wx.HORIZONTAL)
			controls_box.Add(settings_box, flag=wx.CENTER|wx.LEFT, border=10)

			self.plot_settings_button = wx.Button(self, label='Plot...')
			self.Bind(wx.EVT_BUTTON, self.OnPlotSettings, self.plot_settings_button)
			settings_box.Add(self.plot_settings_button, flag=wx.CENTER)

		self.SetSizer(display_box)

		# Acquisition thread.
		callback = functools.partial(wx.CallAfter, self.add_value)
		self.acq_thread = AcquisitionThread(self.plot_settings.delay, callback,
				running_lock=self.running_lock)
		self.acq_thread.daemon = True
		self.acq_thread.start()

		# Wait for a resource to begin capturing.
		self.OnPause()
		self.run_button.Disable()

		# Subscriptions.
		pub.subscribe(self.msg_resource, 'resource.added')
		pub.subscribe(self.msg_resource, 'resource.removed')
		pub.subscribe(self.msg_data_capture_start, 'data_capture.start')
		pub.subscribe(self.msg_data_capture_data, 'data_capture.data')
		pub.subscribe(self.msg_data_capture_stop, 'data_capture.stop')

	@property
	def running(self):
		return self.pause_button.Enabled

	@property
	def resource(self):
		return self.acq_thread.resource

	@resource.setter
	def resource(self, value):
		# Ignore unreadable resources.
		if value is not None and not value.readable:
			value = None

		if self.running:
			# Currently running.
			running = True
			self.OnPause()
		else:
			running = False

		self.acq_thread.resource = value

		self.run_button.Enable(value is not None)

		# Resume if applicable.
		if running:
			self.OnRun()

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

		self._points = numpy.array([])
		self._times = numpy.array([])
		self._values = numpy.array([])

		self.current_value = None

		self.start_time = None

	def update_plot(self):
		"""
		Redraw the plot.
		"""

		if not len(self._points) > 0:
			display_time = [0]
			display_values = [0]
		else:
			if self.plot_settings.time_value == 0: # Time.
				display_time = self._times

				if self.plot_settings.time_mode == 0: # Relative.
					# Calculate the number of seconds passed since each point.
					max_time = self._times[-1]
					display_time = [x - max_time for x in display_time]
				elif self.plot_settings.time_mode == 1: # Absolute.
					display_time = [x - self.start_time for x in display_time]
			elif self.plot_settings.time_value == 1: # Points.
				display_time = self._points

				if self.plot_settings.time_mode == 0: # Relative.
					# Calculate the number of seconds passed since each point.
					max_point = self._points[-1]
					display_time = [x - max_point for x in display_time]

			display_values = [x * 10 ** (self.plot_settings.y_scale + self.unit_conversion) for
					x in self._values]

		if self.plot_settings.update_x:
			self.plot.x_autoscale()
		if self.plot_settings.update_y:
			self.plot.y_autoscale()

		self.plot.x_data, self.plot.y_data = display_time, display_values

	def add_value(self, value):
		"""
		Update the plot with a new value.
		"""

		if not self.plot_settings.enabled:
			return

		# Extract the value of a Quantity.
		try:
			value = value.value
		except AttributeError:
			pass

		# Update values.
		try:
			self._points = numpy.append(self._points, self._points[-1] + 1)
		except IndexError:
			self._points = numpy.append(self._points, 0)
		cur_time = time.time()
		self._times = numpy.append(self._times, cur_time)
		self._values = numpy.append(self._values, value)

		if self.start_time is None:
			self.start_time = cur_time

		cut_idx = len(self._points) - int(self.plot_settings.num_points)
		if cut_idx > 0:
			self._points = self._points[cut_idx:]
			self._times = self._times[cut_idx:]
			self._values = self._values[cut_idx:]

		# Set number display.
		self.current_value = value * 10 ** (self.plot_settings.y_scale + self.unit_conversion)
		self.numeric_display.Value = '{0:.6g}'.format(self.current_value)

		# Plot.
		self.update_plot()

	def close(self):
		"""
		Perform cleanup.
		"""

		# Unsubscriptions.
		pub.unsubscribe(self.msg_resource, 'resource.added')
		pub.unsubscribe(self.msg_resource, 'resource.removed')
		pub.unsubscribe(self.msg_data_capture_start, 'data_capture.start')
		pub.unsubscribe(self.msg_data_capture_data, 'data_capture.data')
		pub.unsubscribe(self.msg_data_capture_stop, 'data_capture.stop')

		# Ensure the thread exits.
		self.acq_thread.resource = None
		self.acq_thread.done = True
		if not self.running:
			self.running_lock.release()
		self.acq_thread.join()
		del self.acq_thread

	def OnRun(self, evt=None):
		"""
		Let the acquisition thread run.
		"""

		self.run_button.Disable()

		if self.acq_thread.resource is None:
			return

		self.running_lock.release()

		self.pause_button.Enable()

	def OnPause(self, evt=None):
		"""
		Block the acquisition thread.
		"""

		if not self.running:
			return

		self.running_lock.acquire()

		if self.acq_thread.resource is not None:
			self.run_button.Enable()
		self.pause_button.Disable()

	def OnReset(self, evt=None):
		self.init_values()
		self.update_plot()

	def OnPlotSettings(self, evt=None):
		"""
		Open the plot settings dialog.
		"""

		def ok_callback(dlg):
			self.plot_settings = dlg.GetValue()

			if self.plot_settings.units_from and self.plot_settings.units_to:
				try:
					quantity_from = Quantity(1, self.plot_settings.units_from)
					quantity_to = Quantity(1, self.plot_settings.units_to)
				except ValueError as e:
					self.unit_conversion = 0
					MessageDialog(self, str(e), 'Invalid unit').Show()
				else:
					# We don't actually care about the units; just the prefix values.
					self.unit_conversion = math.log(quantity_from.value, 10) - math.log(quantity_to.value, 10)
			else:
				self.unit_conversion = 0

			self.acq_thread.delay = self.plot_settings.delay

			if self.plot_settings.time_value == 0:
				self.plot.x_label = 'Time (s)'
			elif self.plot_settings.time_value == 1:
				self.plot.x_label = 'Points'

			if self.plot_settings.y_scale != 0:
				self.plot.y_label = '/ 10 ^ {0}'.format(self.plot_settings.y_scale)
			else:
				self.plot.y_label = ''

			if self.plot_settings.units_to:
				self.plot.y_label += ' ({0})'.format(self.plot_settings.units_to)

			self.update_plot()

		dlg = PlotSettingsDialog(self, ok_callback)
		dlg.SetValue(self.plot_settings)
		dlg.Show()

	def msg_resource(self, name, value=None):
		if self.measurement_resource_name is not None and name == self.measurement_resource_name:
			self.resource = value

	def msg_data_capture_start(self, name):
		if name == self.measurement_resource_name:
			if self.enabled:
				self.capturing_data = True

				# Keep track of whether to restart the capture afterwards.
				self.restart_live_view = self.running

				# Disable live view.
				self.resource_backup = self.resource
				self.resource = None

	def msg_data_capture_data(self, name, value):
		if name == self.measurement_resource_name:
			if self.capturing_data:
				self.add_value(value)

	def msg_data_capture_stop(self, name):
		if name == self.measurement_resource_name:
			if self.capturing_data:
				self.capturing_data = False

				# Re-enable live view.
				self.resource = self.resource_backup
				self.resource_backup = None

				if self.restart_live_view:
					self.OnRun()


class ScalarMeasurementFrame(wx.Frame):
	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Measurement setup.
		self.measurement_config_panel = MeasurementConfigPanel(self, global_store)
		frame_box.Add(self.measurement_config_panel, flag=wx.EXPAND)

		## Live view.
		self.live_view_panel = ScalarLiveViewPanel(self, global_store)
		self.live_view_panel.SetMinSize((-1, 400))
		frame_box.Add(self.live_view_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnClose(self, evt):
		if self.live_view_panel.capturing_data:
			msg = 'Cannot close, as a sweep is currently in progress.'
			MessageDialog(self, msg, 'Sweep in progress').Show()

			evt.Veto()
			return

		self.live_view_panel.close()
		self.measurement_config_panel.close()

		evt.Skip()
