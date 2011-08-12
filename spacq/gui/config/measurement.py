from pubsub import pub
import wx

from spacq.iteration.variables import InputVariable

from ..tool.box import OK_BACKGROUND_COLOR, MessageDialog
from .scaling import ScalingSettings, ScalingSettingsDialog


class MeasurementConfigPanel(wx.Panel):
	"""
	Measurement configuration panel.
	"""

	def __init__(self, parent, global_store, scaling=True, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.parent = parent
		self.global_store = global_store
		self.scaling = scaling

		if self.scaling:
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
		if self.scaling:
			self.scaling_wrap_token = '{0}.{1}'.format(self.__class__.__name__, self.wrap_with_scaling.__name__)
		self.resource = None
		self.unwrapping = False

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Configuration.
		configuration_box = wx.BoxSizer(wx.HORIZONTAL)
		panel_box.Add(configuration_box, flag=wx.EXPAND|wx.ALL, border=5)

		self.enabled_checkbox = wx.CheckBox(self, label='Capture')
		self.enabled_checkbox.Value = self.var.enabled
		configuration_box.Add(self.enabled_checkbox, flag=wx.CENTER|wx.RIGHT, border=15)

		self.Bind(wx.EVT_CHECKBOX, self.OnCaptureChecked, self.enabled_checkbox)

		### Names.
		names_box = wx.FlexGridSizer(rows=2, cols=2, hgap=5)
		names_box.AddGrowableCol(1, 1)
		configuration_box.Add(names_box, flag=wx.EXPAND, proportion=1)

		names_box.Add(wx.StaticText(self, label='Resource name:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.resource_name_input = wx.TextCtrl(self, value=self.var.resource_name, style=wx.TE_PROCESS_ENTER)
		self.resource_name_input.default_background_color = self.resource_name_input.BackgroundColour
		self.resource_name_input.BackgroundColour = OK_BACKGROUND_COLOR
		names_box.Add(self.resource_name_input, flag=wx.EXPAND)

		self.Bind(wx.EVT_TEXT, self.OnResourceNameChange, self.resource_name_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnResourceNameInput, self.resource_name_input)

		names_box.Add(wx.StaticText(self, label='Measurement name:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.measurement_name_input = wx.TextCtrl(self, value=self.var.name, style=wx.TE_PROCESS_ENTER)
		self.measurement_name_input.default_background_color = self.measurement_name_input.BackgroundColour
		self.measurement_name_input.BackgroundColour = OK_BACKGROUND_COLOR
		names_box.Add(self.measurement_name_input, flag=wx.EXPAND)

		self.Bind(wx.EVT_TEXT, self.OnMeasurementNameChange, self.measurement_name_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnMeasurementNameInput, self.measurement_name_input)

		### Scaling.
		if self.scaling:
			scaling_button = wx.Button(self, label='Scaling...', style=wx.BU_EXACTFIT)
			self.Bind(wx.EVT_BUTTON, self.OnScaling, scaling_button)
			configuration_box.Add(scaling_button, flag=wx.EXPAND|wx.LEFT, border=10)

		self.SetSizerAndFit(panel_box)

		self.set_title()

		# Subscriptions.
		if self.scaling:
			pub.subscribe(self.msg_resource, 'resource.added')
			pub.subscribe(self.msg_resource, 'resource.removed')

	@property
	def live_view_panel(self):
		return self.parent.live_view_panel

	def wrap_with_scaling(self, name, resource):
		if not self.scaling:
			return

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
		if not self.scaling:
			return

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

	def set_title(self):
		self.parent.Title = '{0} ({1}){2}'.format(self.var.name, self.var.resource_name,
				'' if self.var.enabled else ' [Disabled]')

	def close(self):
		self.unwrap_with_scaling()

		del self.global_store.variables[self.var.name]

	def OnCaptureChecked(self, evt=None):
		self.var.enabled = self.live_view_panel.enabled = self.enabled_checkbox.Value
		self.set_title()

	def OnResourceNameChange(self, evt=None):
		self.resource_name_input.BackgroundColour = self.resource_name_input.default_background_color

	def OnResourceNameInput(self, evt=None):
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

		self.resource_name_input.BackgroundColour = OK_BACKGROUND_COLOR
		self.set_title()

	def OnMeasurementNameChange(self, evt=None):
		self.measurement_name_input.BackgroundColour = self.measurement_name_input.default_background_color

	def OnMeasurementNameInput(self, evt=None):
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

		self.measurement_name_input.BackgroundColour = OK_BACKGROUND_COLOR
		self.set_title()

	def OnScaling(self, evt=None):
		def ok_callback(dlg):
			self.scaling_settings = dlg.GetValue()

		dlg = ScalingSettingsDialog(self, ok_callback)
		dlg.SetValue(self.scaling_settings)
		dlg.Show()

	def msg_resource(self, name, value=None):
		resource_name = self.var.resource_name

		if name == resource_name:
			self.resource = value

			if value is not None and not self.unwrapping:
				self.wrap_with_scaling(resource_name, value)
