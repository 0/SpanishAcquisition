import wx
from wx.lib.agw.floatspin import FloatSpin

from ..tool.box import Dialog

"""
Pre-amp configuration.

Only used to inform the application of the settings, not to configure the device itself.
"""


class PreAmpSettings(object):
	def __init__(self):
		self.sensitivity_range = 0 # 10 ^ (...) A V^-1


class PreAmpSettingsDialog(Dialog):
	def __init__(self, parent, ok_callback, *args, **kwargs):
		Dialog.__init__(self, parent, title='Pre-amp settings')

		self.ok_callback = ok_callback

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Sensitivity.
		sensitivity_box = wx.FlexGridSizer(rows=1, cols=2, hgap=5)
		dialog_box.Add(sensitivity_box, flag=wx.EXPAND|wx.ALL, border=5)

		sensitivity_box.Add(wx.StaticText(self, label='Sensitivity range:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.sensitivity_input = FloatSpin(self, value=0, min_val=-100, max_val=100,
				increment=1, digits=2)
		sensitivity_box.Add(self.sensitivity_input)

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
		result = PreAmpSettings()

		# Sensitivity.
		result.sensitivity_range = self.sensitivity_input.GetValue()

		return result

	def SetValue(self, value):
		# Sensitivity.
		self.sensitivity_input.SetValue(value.sensitivity_range)

	def OnOk(self, evt=None):
		self.ok_callback(self)

		self.Destroy()
