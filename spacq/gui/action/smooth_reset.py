from functools import partial
from threading import Thread
import wx

from spacq.iteration.variables import OutputVariable
from spacq.tool.box import sift

from ..tool.box import MessageDialog


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

	def choose_variables(self):
		"""
		Return all the selected variables, ensuring that their resources are valid.
		"""

		all_vars = sift(self.global_store.variables.values(), OutputVariable)
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
			MessageDialog(self, ', '.join(missing_resources), 'Missing resources').Show()
		if unwritable_resources:
			MessageDialog(self, ', '.join(unwritable_resources), 'Unwritable resources').Show()
		if missing_resources or unwritable_resources:
			return None

		return vars

	def reset(self, from_zero):
		vars = self.choose_variables()
		if vars is None:
			return

		self.to_button.Disable()
		self.from_button.Disable()

		def exception_callback(e):
			MessageDialog(self, str(e), 'Error writing to resource').Show()

		def sweep_all_vars():
			try:
				thrs = []
				for var in vars:
					resource = self.global_store.resources[var.resource_name]

					if from_zero:
						value_from, value_to = 0, var.with_type(var.const)
					else:
						value_from, value_to = var.with_type(var.const), 0

					thr = Thread(target=resource.sweep, args=(value_from, value_to, self.reset_steps_input.Value),
							kwargs={'exception_callback': partial(wx.CallAfter, exception_callback)})
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
