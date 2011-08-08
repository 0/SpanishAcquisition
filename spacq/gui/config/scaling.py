import wx
from wx.lib.agw.floatspin import FloatSpin

from spacq.interface.units import Quantity

from ..tool.box import Dialog

"""
Resource scaling configuration.
"""


class ScalingSettings(object):
	"""
	Set up scaling of the form:
		f(x) = a * x * (10 ** b) + c
	"""

	def __init__(self):
		self.linear_scale = 1
		self.exponential_scale = 0
		self.offset = 0

	def transform(self, x):
		"""
		Perform a transform according to the scaling.
		"""

		if self.offset == 0:
			return self.linear_scale * x * (10 ** self.exponential_scale)
		elif isinstance(x, Quantity):
			return self.linear_scale * x * (10 ** self.exponential_scale) + Quantity(self.offset, x.original_units)
		else:
			return self.linear_scale * x * (10 ** self.exponential_scale) + self.offset


class ScalingSettingsDialog(Dialog):
	def __init__(self, parent, ok_callback, *args, **kwargs):
		Dialog.__init__(self, parent, title='Scaling settings')

		self.ok_callback = ok_callback

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Settings.
		settings_box = wx.FlexGridSizer(rows=3, cols=2, hgap=5)
		dialog_box.Add(settings_box, flag=wx.EXPAND|wx.ALL, border=5)

		### Linear scale.
		settings_box.Add(wx.StaticText(self, label='Linear scale:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.linear_scale_input = FloatSpin(self, value=0, min_val=-1e9, max_val=1e9,
				increment=1, digits=5)
		settings_box.Add(self.linear_scale_input, flag=wx.EXPAND)

		### Exponential scale.
		settings_box.Add(wx.StaticText(self, label='Exponential scale:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.exponential_scale_input = FloatSpin(self, value=0, min_val=-100, max_val=100,
				increment=1, digits=2)
		settings_box.Add(self.exponential_scale_input, flag=wx.EXPAND)

		### Offset.
		settings_box.Add(wx.StaticText(self, label='Offset:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.offset_input = FloatSpin(self, value=0, min_val=-1e9, max_val=1e9,
				increment=1, digits=5, size=(200, -1))
		settings_box.Add(self.offset_input, flag=wx.EXPAND)

		## End buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER|wx.ALL, border=5)

		ok_button = wx.Button(self, wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
		button_box.Add(ok_button)

		cancel_button = wx.Button(self, wx.ID_CANCEL)
		button_box.Add(cancel_button)

		self.SetSizerAndFit(dialog_box)

	def GetValue(self):
		result = ScalingSettings()

		result.linear_scale = self.linear_scale_input.GetValue()
		result.exponential_scale = self.exponential_scale_input.GetValue()
		result.offset = self.offset_input.GetValue()

		return result

	def SetValue(self, value):
		self.linear_scale_input.SetValue(value.linear_scale)
		self.exponential_scale_input.SetValue(value.exponential_scale)
		self.offset_input.SetValue(value.offset)

	def OnOk(self, evt=None):
		self.ok_callback(self)

		self.Destroy()
