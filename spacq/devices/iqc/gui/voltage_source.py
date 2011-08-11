from functools import partial
from pubsub import pub
from threading import Thread
from time import sleep
import wx
from wx.lib.agw.floatspin import FloatSpin

from spacq.gui.tool.box import load_csv, save_csv, Dialog, MessageDialog
from spacq.interface.units import Quantity

"""
Configuration for a VoltageSource.
"""


class VoltageSourceTunerDialog(Dialog):
	"""
	A dialog for tuning a voltage source port.
	"""

	def __init__(self, parent, global_store, ok_callback, port,	*args, **kwargs):
		Dialog.__init__(self, parent, title='Port {0} tuning'.format(port.num))

		self.global_store = global_store
		self.ok_callback = ok_callback
		self.port = port

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Self-calibration.
		calibration_static_box = wx.StaticBox(self, label='DAC self-calibration')
		calibration_box = wx.StaticBoxSizer(calibration_static_box, wx.VERTICAL)
		dialog_box.Add(calibration_box, flag=wx.EXPAND|wx.ALL, border=5)

		self.calibrate_button = wx.Button(self, label='Self-calibrate')
		self.Bind(wx.EVT_BUTTON, self.OnCalibrate, self.calibrate_button)
		calibration_box.Add(self.calibrate_button, flag=wx.EXPAND)

		## Tuning.
		tuning_static_box = wx.StaticBox(self, label='Tuning')
		tuning_box = wx.StaticBoxSizer(tuning_static_box, wx.VERTICAL)
		dialog_box.Add(tuning_box, flag=wx.EXPAND)

		### Autotune.
		autotuning_static_box = wx.StaticBox(self, label='Autotuning')
		autotuning_box = wx.StaticBoxSizer(autotuning_static_box, wx.VERTICAL)
		tuning_box.Add(autotuning_box, flag=wx.EXPAND|wx.ALL, border=5)

		autotuning_sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5)
		autotuning_box.Add(autotuning_sizer, flag=wx.CENTER)

		autotuning_sizer.Add(wx.StaticText(self, label='Resource name:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.resource_name_input = wx.TextCtrl(self, size=(300,-1))
		autotuning_sizer.Add(self.resource_name_input)

		autotuning_sizer.Add(wx.StaticText(self, label='Max:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.automax_input = FloatSpin(self, value=1, min_val=-10, max_val=10, increment=1,
				digits=5)
		autotuning_sizer.Add(self.automax_input)

		autotuning_sizer.Add(wx.StaticText(self, label='Min:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.automin_input = FloatSpin(self, value=-1, min_val=-10, max_val=10, increment=1,
				digits=5)
		autotuning_sizer.Add(self.automin_input)

		self.autotune_button = wx.Button(self, label='Autotune')
		self.Bind(wx.EVT_BUTTON, self.OnAutotune, self.autotune_button)
		autotuning_box.Add(self.autotune_button, flag=wx.EXPAND)

		### Manual tune.
		tuning_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=5)
		tuning_box.Add(tuning_sizer, flag=wx.CENTER)

		tuning_sizer.Add(wx.StaticText(self, label='Gain:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.gain_input = FloatSpin(self, value=0, min_val=-1e6, max_val=1e6, increment=1,
				digits=5)
		tuning_sizer.Add(self.gain_input)

		tuning_sizer.Add(wx.StaticText(self, label='Offset:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.offset_input = FloatSpin(self, value=0, min_val=-1e6, max_val=1e6, increment=1,
				digits=5)
		tuning_sizer.Add(self.offset_input)

		## End buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER|wx.ALL, border=5)

		ok_button = wx.Button(self, wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
		button_box.Add(ok_button)

		cancel_button = wx.Button(self, wx.ID_CANCEL)
		button_box.Add(cancel_button)

		self.SetSizerAndFit(dialog_box)

	def autotune(self, resource):
		gain, offset = self.port.autotune(resource, set_result=False,
				min_value=self.automin_input.GetValue(),
				max_value=self.automax_input.GetValue())

		wx.CallAfter(self.gain_input.SetValue, gain)
		wx.CallAfter(self.offset_input.SetValue, offset)
		wx.CallAfter(self.autotune_button.Enable)

	def self_calbrate(self):
		self.port.apply_settings(calibrate=True)

		sleep(self.port.calibration_delay)
		wx.CallAfter(self.calibrate_button.Enable)

	def SetValue(self, gain, offset):
		self.gain_input.SetValue(gain)
		self.offset_input.SetValue(offset)

	def GetValue(self):
		return (self.gain_input.GetValue(), self.offset_input.GetValue())

	def OnAutotune(self, evt=None):
		name = self.resource_name_input.Value

		if not name:
			MessageDialog(self, 'No resource provided').Show()
			return

		try:
			resource = self.global_store.resources[name]
		except KeyError:
			MessageDialog(self, name, 'Missing resource').Show()
			return

		if not resource.readable:
			MessageDialog(self, name, 'Unreadable resource').Show()
			return

		self.autotune_button.Disable()

		thr = Thread(target=self.autotune, args=(resource,))
		thr.daemon = True
		thr.start()

	def OnCalibrate(self, evt=None):
		self.calibrate_button.Disable()

		thr = Thread(target=self.self_calbrate)
		thr.daemon = True
		thr.start()

	def OnOk(self, evt=None):
		self.ok_callback(self)

		self.Destroy()


class VoltageSourceSettingsPanel(wx.Panel):
	"""
	All the settings for a voltage source.
	"""

	def __init__(self, parent, global_store, vsrc, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self.vsrc = vsrc

		self.port_value_inputs = []
		self.port_buttons = []

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Ports.
		ports_box = wx.FlexGridSizer(rows=8, cols=2)
		panel_box.Add(ports_box)

		for port in xrange(16):
			port_static_box = wx.StaticBox(self, label='Port {0} '.format(port))
			port_box = wx.StaticBoxSizer(port_static_box, wx.HORIZONTAL)
			ports_box.Add(port_box, flag=wx.ALL, border=5)

			spin = FloatSpin(self, value=0, min_val=-10, max_val=10, increment=1, digits=6)
			self.port_value_inputs.append(spin)
			port_box.Add(spin)

			port_box.Add(wx.StaticText(self, label='V'))

			set_button = wx.Button(self, label='Set', style=wx.BU_EXACTFIT)
			set_button.Bind(wx.EVT_BUTTON, partial(self.OnSetVoltage, port))
			port_box.Add(set_button)

			tune_button = wx.Button(self, label='Tune...', style=wx.BU_EXACTFIT)
			tune_button.Bind(wx.EVT_BUTTON, partial(self.OnTune, port))
			port_box.Add(tune_button)

			self.port_buttons.append((set_button, tune_button))

		## All ports.
		button_static_box = wx.StaticBox(self, label='All ports')
		button_box = wx.StaticBoxSizer(button_static_box, wx.HORIZONTAL)
		panel_box.Add(button_box, flag=wx.CENTER)

		### Zero.
		zero_all_button = wx.Button(self, label='Zero')
		self.Bind(wx.EVT_BUTTON, self.OnZeroAll, zero_all_button)
		button_box.Add(zero_all_button, flag=wx.CENTER)

		### Self-calibrate.
		self.calibrate_all_button = wx.Button(self, label='Self-calibrate')
		self.Bind(wx.EVT_BUTTON, self.OnCalibrateAll, self.calibrate_all_button)
		button_box.Add(self.calibrate_all_button, flag=wx.CENTER)

		### Load tuning.
		tuning_data_static_box = wx.StaticBox(self, label='Tuning data')
		tuning_data_box = wx.StaticBoxSizer(tuning_data_static_box, wx.HORIZONTAL)
		button_box.Add(tuning_data_box)

		#### Save.
		tuning_data_save_button = wx.Button(self, label='Save...')
		self.Bind(wx.EVT_BUTTON, self.OnSave, tuning_data_save_button)
		tuning_data_box.Add(tuning_data_save_button)

		#### Load.
		tuning_data_load_button = wx.Button(self, label='Load...')
		self.Bind(wx.EVT_BUTTON, self.OnLoad, tuning_data_load_button)
		tuning_data_box.Add(tuning_data_load_button)

		self.SetSizer(panel_box)

	def self_calbrate_all(self):
		delay = 0 # s

		for port in self.vsrc.ports:
			# Use the largest delay.
			if port.calibration_delay > delay:
				delay = port.calibration_delay

			port.apply_settings(calibrate=True)

		sleep(delay)
		wx.CallAfter(self.calibrate_all_button.Enable)

	def zero_all(self):
		for port in self.vsrc.ports:
			port.voltage = Quantity(0.0, 'V')

	def OnSetVoltage(self, port_num, evt=None):
		try:
			self.vsrc.ports[port_num].voltage = Quantity(self.port_value_inputs[port_num].GetValue(), 'V')
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()

	def OnTune(self, port_num, evt=None):
		port = self.vsrc.ports[port_num]

		def ok_callback(dlg):
			port.gain, port.offset = dlg.GetValue()

		dlg = VoltageSourceTunerDialog(self, self.global_store, ok_callback, port)
		dlg.SetValue(port.gain, port.offset)
		dlg.Show()

	def OnCalibrateAll(self, evt=None):
		self.calibrate_all_button.Disable()

		thr = Thread(target=self.self_calbrate_all)
		thr.daemon = True
		thr.start()

	def OnZeroAll(self, evt=None):
		thr = Thread(target=self.zero_all)
		thr.daemon = True
		thr.start()

	def OnSave(self, evt=None):
		values = [[port.gain, port.offset] for port in self.vsrc.ports]

		try:
			save_csv(self, values)
		except IOError as e:
			MessageDialog(self, str(e), 'Save error').Show()
			return

	def OnLoad(self, evt=None):
		try:
			result = load_csv(self)

			if result is None:
				return

			has_header, values, _ = result

			if has_header:
				port_values = values[1:]
			else:
				port_values = values

			if len(port_values) != len(self.vsrc.ports):
				raise ValueError('Invalid number of ports.')

			for i, port_value in enumerate(port_values):
				if len(port_value) != 2:
					raise ValueError('Invalid number of settings for port {0}.'.format(i))

				try:
					float(port_value[0])
					float(port_value[1])
				except TypeError:
					raise ValueError('Not a number for port {0}.'.format(i))
		except (IOError, ValueError) as e:
			MessageDialog(self, str(e), 'Load error').Show()
			return

		for port, values in zip(self.vsrc.ports, port_values):
			port.gain = float(values[0])
			port.offset = float(values[1])


class VoltageSourceSettingsDialog(Dialog):
	"""
	A wrapper for VoltageSourceSettingsPanel.
	"""

	def __init__(self, parent, global_store, vsrc_name, *args, **kwargs):
		# If the device doesn't exist, give up.
		try:
			vsrc = global_store.devices[vsrc_name].device
		except (KeyError, AttributeError):
			self.Destroy()

			return

		Dialog.__init__(self, parent, title='Voltage source settings', *args, **kwargs)

		self.vsrc_name = vsrc_name

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Settings panel.
		self.panel = VoltageSourceSettingsPanel(self, global_store, vsrc)
		dialog_box.Add(self.panel)

		self.SetSizerAndFit(dialog_box)

		# Subscriptions.
		pub.subscribe(self.msg_device, 'device.added')
		pub.subscribe(self.msg_device, 'device.removed')

	def msg_device(self, name, value=None):
		if name == self.vsrc_name:
			# Device has changed, so we can't trust it anymore.
			self.Destroy()

			return
