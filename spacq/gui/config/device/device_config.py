import wx
from wx.lib.masked.ipaddrctrl import IpAddrCtrl

from spacq.devices.config import device_tree, ConnectionError, DeviceConfig

from ...tool.box import load_pickled, save_pickled, Dialog, MessageDialog
from .resource_tree import DeviceResourcesPanel

"""
Device configuration for and through the GUI.
"""


class DeviceConfigPanel(wx.Panel):
	"""
	Set up a device for consumption of its resources.
	"""

	def __init__(self, parent, connection_callback=None, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.connection_callback = connection_callback

		# Implementation info.
		## Find all the available devices.
		self.device_tree = device_tree()
		self.manufacturers = [''] + sorted(self.device_tree.keys())
		self.models = ['']

		## Chosen values.
		self.manufacturer = None
		self.model = None

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Address.
		address_static_box = wx.StaticBox(self, label='Address')
		address_box = wx.StaticBoxSizer(address_static_box, wx.VERTICAL)
		address_sizer = wx.BoxSizer(wx.HORIZONTAL)
		address_box.Add(address_sizer, flag=wx.EXPAND)
		panel_box.Add(address_box, flag=wx.EXPAND|wx.ALL, border=5)

		### Ethernet.
		ethernet_static_box = wx.StaticBox(self)
		ethernet_box = wx.StaticBoxSizer(ethernet_static_box, wx.VERTICAL)
		address_sizer.Add(ethernet_box, proportion=1)

		self.address_mode_eth = wx.RadioButton(self, label='Ethernet', style=wx.RB_GROUP)
		ethernet_box.Add(self.address_mode_eth)

		ethernet_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=5)
		ethernet_box.Add(ethernet_sizer, flag=wx.EXPAND)

		ethernet_sizer.Add(wx.StaticText(self, label='IP address:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.ip_address_input = IpAddrCtrl(self)
		ethernet_sizer.Add(self.ip_address_input, flag=wx.CENTER)

		### GPIB.
		self.gpib_static_box = wx.StaticBox(self)
		gpib_box = wx.StaticBoxSizer(self.gpib_static_box, wx.VERTICAL)
		address_sizer.Add(gpib_box, proportion=1)

		self.address_mode_gpib = wx.RadioButton(self, label='GPIB')
		gpib_box.Add(self.address_mode_gpib)

		gpib_sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5)
		gpib_box.Add(gpib_sizer, flag=wx.EXPAND)

		gpib_sizer.Add(wx.StaticText(self, label='Board:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.gpib_board_input = wx.SpinCtrl(self, min=0, max=100, initial=0)
		gpib_sizer.Add(self.gpib_board_input, flag=wx.CENTER)

		gpib_sizer.Add(wx.StaticText(self, label='PAD:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.gpib_pad_input = wx.SpinCtrl(self, min=1, max=30, initial=1)
		gpib_sizer.Add(self.gpib_pad_input, flag=wx.CENTER)

		gpib_sizer.Add(wx.StaticText(self, label='SAD:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.gpib_sad_input = wx.SpinCtrl(self, min=0, max=30, initial=0)
		gpib_sizer.Add(self.gpib_sad_input, flag=wx.CENTER)

		### USB.
		usb_static_box = wx.StaticBox(self)
		usb_box = wx.StaticBoxSizer(usb_static_box, wx.VERTICAL)
		address_box.Add(usb_box, flag=wx.EXPAND)

		self.address_mode_usb = wx.RadioButton(self, label='USB')
		usb_box.Add(self.address_mode_usb)

		usb_sizer = wx.BoxSizer(wx.HORIZONTAL)
		usb_box.Add(usb_sizer, flag=wx.EXPAND)

		usb_sizer.Add(wx.StaticText(self, label='USB resource: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.usb_resource_input = wx.TextCtrl(self, size=(300, -1))
		usb_sizer.Add(self.usb_resource_input, proportion=1)

		## Implementation.
		implementation_static_box = wx.StaticBox(self, label='Implementation')
		implementation_box = wx.StaticBoxSizer(implementation_static_box, wx.HORIZONTAL)
		panel_box.Add(implementation_box, flag=wx.EXPAND|wx.ALL, border=5)

		self.manufacturer_input = wx.Choice(self, choices=self.manufacturers)
		self.Bind(wx.EVT_CHOICE, self.OnManufacturer, self.manufacturer_input)
		implementation_box.Add(self.manufacturer_input, proportion=1)

		self.model_input = wx.Choice(self, choices=self.models)
		self.Bind(wx.EVT_CHOICE, self.OnModel, self.model_input)
		implementation_box.Add(self.model_input, proportion=1)

		self.mock_input = wx.CheckBox(self, label='Mock')
		implementation_box.Add(self.mock_input, flag=wx.CENTER)

		## Connection buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		panel_box.Add(button_box, flag=wx.CENTER|wx.ALL, border=5)

		self.connect_button = wx.Button(self, label='Connect')
		self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)
		button_box.Add(self.connect_button)

		self.disconnect_button = wx.Button(self, label='Disconnect')
		self.Bind(wx.EVT_BUTTON, self.OnDisconnect, self.disconnect_button)
		button_box.Add(self.disconnect_button)

		self.SetSizerAndFit(panel_box)

	def get_address_mode(self):
		if self.address_mode_eth.Value:
			return DeviceConfig.address_modes.ethernet
		elif self.address_mode_gpib.Value:
			return DeviceConfig.address_modes.gpib
		elif self.address_mode_usb.Value:
			return DeviceConfig.address_modes.usb

	def GetValue(self):
		dev_cfg = DeviceConfig(name=self.name)

		# Address mode.
		dev_cfg.address_mode = self.get_address_mode()

		## Ethernet.
		possible_address = self.ip_address_input.GetAddress()
		if self.ip_address_input.IsValid() and len(possible_address) > 6:
			dev_cfg.ip_address = possible_address
		else:
			dev_cfg.ip_address = None

		## GPIB.
		dev_cfg.gpib_board = self.gpib_board_input.Value
		dev_cfg.gpib_pad = self.gpib_pad_input.Value
		dev_cfg.gpib_sad = self.gpib_sad_input.Value

		## USB.
		possible_resource = self.usb_resource_input.Value
		if possible_resource:
			dev_cfg.usb_resource = possible_resource
		else:
			dev_cfg.usb_resource = None

		# Implementation.
		dev_cfg.manufacturer = self.manufacturer
		dev_cfg.model = self.model
		dev_cfg.mock = self.mock_input.Value

		# Device.
		dev_cfg.device = self.device

		# Resource labels.
		dev_cfg.resource_labels = self.resource_labels

		return dev_cfg

	def SetValue(self, dev_cfg):
		self.name = dev_cfg.name

		# Address mode.
		if dev_cfg.address_mode == DeviceConfig.address_modes.ethernet:
			self.address_mode_eth.Value = True
		elif dev_cfg.address_mode == DeviceConfig.address_modes.gpib:
			self.address_mode_gpib.Value = True
		elif dev_cfg.address_mode == DeviceConfig.address_modes.usb:
			self.address_mode_usb.Value = True

		## Ethernet.
		if dev_cfg.ip_address:
			self.ip_address_input.SetValue(dev_cfg.ip_address)

		## GPIB.
		self.gpib_board_input.Value = dev_cfg.gpib_board
		self.gpib_pad_input.Value = dev_cfg.gpib_pad
		self.gpib_sad_input.Value = dev_cfg.gpib_sad

		## USB.
		if dev_cfg.usb_resource:
			self.usb_resource_input.Value = dev_cfg.usb_resource

		# Implementation.
		if dev_cfg.manufacturer is not None:
			self.manufacturer_input.StringSelection = dev_cfg.manufacturer
			self.OnManufacturer()

		if dev_cfg.model is not None:
			self.model_input.StringSelection = dev_cfg.model
			self.OnModel()

		self.mock_input.Value = dev_cfg.mock

		# Device.
		self.device = dev_cfg.device
		if self.device is not None:
			self.connect_button.Disable()
			self.disconnect_button.Enable()
		else:
			self.connect_button.Enable()
			self.disconnect_button.Disable()

		# Resource labels.
		self.resource_labels = dev_cfg.resource_labels

		if self.device is not None and self.connection_callback is not None:
			self.connection_callback(self.device, self.resource_labels)

	def OnManufacturer(self, evt=None):
		self.manufacturer = self.manufacturers[self.manufacturer_input.Selection]

		self.models = ['']
		if self.manufacturer:
			self.models.extend(self.device_tree[self.manufacturer].keys())
		else:
			self.manufacturer = None

		self.model_input.SetItems(self.models)

	def OnModel(self, evt=None):
		self.model = self.models[self.model_input.Selection]

		if self.model:
			model = self.device_tree[self.manufacturer][self.model]

			if 'real' in model and 'mock' not in model:
				self.mock_input.Value = False
				self.mock_input.Disable()
			elif 'real' not in model and 'mock' in model:
				self.mock_input.Value = True
				self.mock_input.Disable()
			else:
				self.mock_input.Enable()
		else:
			self.model = None

	def OnDisconnect(self, evt=None):
		self.device = None

		if self.connection_callback is not None:
			self.connection_callback(None, {})

		self.disconnect_button.Disable()

	def OnConnect(self, evt=None):
		dev_cfg = self.GetValue()
		try:
			dev_cfg.connect()
		except ConnectionError as e:
			MessageDialog(self, str(e), 'Connection error').Show()
			return

		self.device = dev_cfg.device

		if self.connection_callback is not None:
			self.connection_callback(self.device, self.resource_labels)

		self.connect_button.Disable()


class DeviceConfigDialog(Dialog):
	"""
	A dialog for configuring a device, including connection and resources.
	"""

	def __init__(self, parent, ok_callback, *args, **kwargs):
		Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,
				*args, **kwargs)

		self.ok_callback = ok_callback

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Tabs.
		self.notebook = wx.Notebook(self)
		dialog_box.Add(self.notebook, proportion=1, flag=wx.EXPAND)

		self.resources_panel = DeviceResourcesPanel(self.notebook)
		self.connection_panel = DeviceConfigPanel(self.notebook,
				connection_callback=self.resources_panel.set_device)

		self.notebook.AddPage(self.connection_panel, 'Connection')
		self.notebook.AddPage(self.resources_panel, 'Resources')

		## End buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER|wx.TOP, border=10)

		### OK, cancel.
		dialog_button_box = wx.BoxSizer(wx.HORIZONTAL)
		button_box.Add(dialog_button_box)

		ok_button = wx.Button(self, wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
		dialog_button_box.Add(ok_button)

		cancel_button = wx.Button(self, wx.ID_CANCEL)
		dialog_button_box.Add(cancel_button)

		### Save, load.
		save_button_box = wx.BoxSizer(wx.HORIZONTAL)
		button_box.Add(save_button_box, flag=wx.LEFT, border=20)

		save_button = wx.Button(self, wx.ID_SAVE, label='Save...')
		self.Bind(wx.EVT_BUTTON, self.OnSave, save_button)
		save_button_box.Add(save_button)

		load_button = wx.Button(self, wx.ID_OPEN, label='Load...')
		self.Bind(wx.EVT_BUTTON, self.OnLoad, load_button)
		save_button_box.Add(load_button)

		self.SetSizerAndFit(dialog_box)

	def GetValue(self):
		dev_cfg = self.connection_panel.GetValue()
		labels, resources = self.resources_panel.GetValue()

		dev_cfg.resources = resources

		# Preserve labels between device instances.
		if dev_cfg.device is not None:
			dev_cfg.resource_labels = labels

		return dev_cfg

	def SetValue(self, dev_cfg):
		self.connection_panel.SetValue(dev_cfg)
		self.resources_panel.SetValue(dev_cfg.resource_labels, dev_cfg.resources)

	def OnOk(self, evt=None):
		if self.ok_callback(self):
			self.Destroy()

	def OnSave(self, evt=None):
		try:
			save_pickled(self, self.GetValue(), extension='dev',
					file_type='Device configuration')
		except IOError as e:
			MessageDialog(self, str(e), 'Save error').Show()
			return

	def OnLoad(self, evt=None):
		try:
			value = load_pickled(self, extension='dev', file_type='Device configuration')

			try:
				if value is not None:
					value.name = self.connection_panel.name
					self.SetValue(value)
			except Exception as e:
				raise IOError('Could not set values.', e)
		except IOError as e:
			MessageDialog(self, str(e), 'Load error').Show()
			return
