from pubsub import pub
import wx

from spacq.iteration.variables import InputVariable
from spacq.gui.tool.box import MessageDialog

from ..display.plot.live.scalar import ScalarLiveViewPanel
from .scaling import ScalingSettings, ScalingSettingsDialog


class MeasurementConfigFrame(wx.Frame):
	"""
	Measurement configuration and live view frame.
	"""

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store

		self.scaling_settings = ScalingSettings()

		# Ensure that we get a unique name.
		with self.global_store.variables.lock:
			num = 1
			done = False
			while not done:
				name = 'New measurement {0}'.format(num)
				self.var = InputVariable(name=name)

				try:
					self.global_store.variables[name] = self.var
				except KeyError:
					num += 1
				else:
					done = True

		# Keep track of the scaling wrapper and resource.
		self.scaling_wrap_token = '{0}.{1}'.format(self.__class__.__name__, self.wrap_with_scaling.__name__)
		self.resource = None
		self.unwrapping = False

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Configuration.
		configuration_box = wx.BoxSizer(wx.HORIZONTAL)
		frame_box.Add(configuration_box, flag=wx.EXPAND|wx.ALL, border=5)

		self.enabled_checkbox = wx.CheckBox(self, label='Capture')
		self.enabled_checkbox.Value = self.var.enabled
		configuration_box.Add(self.enabled_checkbox, flag=wx.CENTER|wx.RIGHT, border=15)

		### Names.
		names_box = wx.FlexGridSizer(rows=2, cols=2, hgap=5)
		names_box.AddGrowableCol(1, 1)
		configuration_box.Add(names_box, flag=wx.EXPAND, proportion=1)

		names_box.Add(wx.StaticText(self, label='Resource name:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.resource_name_input = wx.TextCtrl(self, value=self.var.resource_name)
		names_box.Add(self.resource_name_input, flag=wx.EXPAND)

		names_box.Add(wx.StaticText(self, label='Measurement name:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.measurement_name_input = wx.TextCtrl(self, value=self.var.name)
		names_box.Add(self.measurement_name_input, flag=wx.EXPAND)

		set_button = wx.Button(self, label='Set', style=wx.BU_EXACTFIT)
		self.Bind(wx.EVT_BUTTON, self.OnSet, set_button)
		configuration_box.Add(set_button, flag=wx.EXPAND)

		### Scaling.
		scaling_button = wx.Button(self, label='Scaling...', style=wx.BU_EXACTFIT)
		self.Bind(wx.EVT_BUTTON, self.OnScaling, scaling_button)
		configuration_box.Add(scaling_button, flag=wx.EXPAND|wx.LEFT, border=10)

		## Live view.
		self.live_view_panel = ScalarLiveViewPanel(self, global_store)
		self.live_view_panel.SetMinSize((-1, 400))
		frame_box.Add(self.live_view_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizer(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

		self.OnSet()

		# Subscriptions.
		pub.subscribe(self.msg_resource, 'resource.added')
		pub.subscribe(self.msg_resource, 'resource.removed')

	def wrap_with_scaling(self, name, resource):
		# Don't double-wrap.
		if resource.is_wrapped_by(self.scaling_wrap_token):
			return

		# Modify the resource value by the scaling.
		def transform(x):
			# Close over self, so that updating scaling settings automatically takes effect.
			return self.scaling_settings.transform(x)
		wrapped_resource = resource.wrapped(self.scaling_wrap_token, transform)

		with self.global_store.lock:
			del self.global_store.resources[name]
			self.global_store.resources[name] = wrapped_resource

	def unwrap_with_scaling(self):
		if self.resource is None:
			return

		# Don't allow immediate re-wrapping.
		self.unwrapping = True

		name = self.live_view_panel.measurement_resource_name
		unwrapped_resource = self.resource.unwrapped(self.scaling_wrap_token)

		with self.global_store.lock:
			del self.global_store.resources[name]
			self.global_store.resources[name] = unwrapped_resource

		self.resource = None
		self.unwrapping = False

	def OnSet(self, evt=None):
		if self.live_view_panel.capturing_data:
			msg = 'Cannot change values, as a sweep is currently in progress.'
			MessageDialog(self, msg, 'Sweep in progress').Show()

			return

		# Update variable.
		if self.var.resource_name != self.resource_name_input.Value:
			# Ensure that the resource is unwrapped before releasing it.
			self.unwrap_with_scaling()

			self.var.resource_name = name = self.resource_name_input.Value

			# Inform the panel.
			self.live_view_panel.measurement_resource_name = name

			# Grab the new resource if it already exists.
			try:
				self.resource = self.global_store.resources[name]
			except KeyError:
				pass
			else:
				self.wrap_with_scaling(name, self.resource)

		self.var.enabled = self.enabled_checkbox.Value
		self.live_view_panel.enabled = self.enabled_checkbox.Value

		# Move variable.
		if self.var.name != self.measurement_name_input.Value:
			# Attempt to add a new entry first.
			var_new_name = self.measurement_name_input.Value
			try:
				self.global_store.variables[var_new_name] = self.var
			except KeyError:
				MessageDialog(self, var_new_name, 'Variable name conflicts').Show()
			else:
				# Remove the old entry.
				del self.global_store.variables[self.var.name]

			self.var.name = var_new_name

		self.Title = '{0} ({1}){2}'.format(self.var.name, self.var.resource_name,
				'' if self.var.enabled else ' [Disabled]')

	def OnScaling(self, evt=None):
		def ok_callback(dlg):
			self.scaling_settings = dlg.GetValue()

		dlg = ScalingSettingsDialog(self, ok_callback)
		dlg.SetValue(self.scaling_settings)
		dlg.Show()

	def OnClose(self, evt):
		if self.live_view_panel.capturing_data:
			msg = 'Cannot close, as a sweep is currently in progress.'
			MessageDialog(self, msg, 'Sweep in progress').Show()

			evt.Veto()
			return

		self.unwrap_with_scaling()
		self.live_view_panel.close()

		del self.global_store.variables[self.var.name]

		evt.Skip()

	def msg_resource(self, name, value=None):
		resource_name = self.live_view_panel.measurement_resource_name

		if name == resource_name:
			self.resource = value

			if value is not None and not self.unwrapping:
				self.wrap_with_scaling(resource_name, value)
