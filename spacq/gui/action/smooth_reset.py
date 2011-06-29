import numpy
from threading import Thread
import time
import wx

from ..tool.box import ErrorMessageDialog


class SmoothResetPanel(wx.Panel):
	"""
	A panel to change variables smoothly to and from preset values.
	"""

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Reset.
		reset_static_box = wx.StaticBox(self, label='Smooth reset')
		reset_box = wx.StaticBoxSizer(reset_static_box, wx.VERTICAL)
		panel_box.Add(reset_box, flag=wx.CENTER|wx.ALL, border=10)

		### To zero.
		self.to_button = wx.Button(self, label='To zero')
		self.Bind(wx.EVT_BUTTON, self.OnResetToZero, self.to_button)
		reset_box.Add(self.to_button, flag=wx.EXPAND)

		### From zero.
		self.from_button = wx.Button(self, label='From zero')
		self.Bind(wx.EVT_BUTTON, self.OnResetFromZero, self.from_button)
		reset_box.Add(self.from_button, flag=wx.EXPAND)

		### Steps.
		steps_static_box = wx.StaticBox(self, label='Steps')
		steps_box = wx.StaticBoxSizer(steps_static_box, wx.VERTICAL)
		reset_box.Add(steps_box, flag=wx.EXPAND)

		self.reset_steps_input = wx.SpinCtrl(self, min=1, initial=10)
		steps_box.Add(self.reset_steps_input)

		self.SetSizer(panel_box)

	def sweep_var(self, variable, steps, from_zero):
		if from_zero:
			values = numpy.linspace(0, variable.const, steps)
		else:
			values = numpy.linspace(variable.const, 0, steps)

		resource = self.global_store.resources[variable.resource_name]

		for value in values:
			resource.value = value
			time.sleep(variable._wait.value)

	def choose_variables(self):
		"""
		Return all the selected variables, ensuring that their resources are valid.
		"""

		all_vars = self.global_store.variables.values()
		vars = [var for var in all_vars if var.enabled and var.use_const and var.resource_name]

		missing_resources = []
		unwritable_resources = []
		for var in vars:
			try:
				if not self.global_store.resources[var.resource_name].writable:
					unwritable_resources.append(var.resource_name)
			except KeyError:
				missing_resources.append(var.resource_name)

		if missing_resources:
			ErrorMessageDialog(self, ', '.join(missing_resources), 'Missing resources').Show()
		if unwritable_resources:
			ErrorMessageDialog(self, ', '.join(unwritable_resources), 'Unwritable resources').Show()
		if missing_resources or unwritable_resources:
			return None

		return vars

	def reset(self, from_zero):
		vars = self.choose_variables()
		if vars is None:
			return

		self.to_button.Disable()
		self.from_button.Disable()

		def sweep_all_vars():
			try:
				thrs = []
				for var in vars:
					thr = Thread(target=self.sweep_var,
							args=(var, self.reset_steps_input.Value, from_zero))
					thr.daemon = True
					thrs.append(thr)

				for thr in thrs:
					thr.start()
				for thr in thrs:
					thr.join()
			finally:
				if self:
					wx.CallAfter(self.to_button.Enable)
					wx.CallAfter(self.from_button.Enable)

		thr = Thread(target=sweep_all_vars)
		thr.daemon = True
		thr.start()

	def OnResetToZero(self, evt=None):
		self.reset(False)

	def OnResetFromZero(self, evt=None):
		self.reset(True)
