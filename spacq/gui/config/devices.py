import ObjectListView
from threading import Thread
from time import sleep
import wx

from spacq.devices.config import DeviceConfig
from ..tool.box import MessageDialog
from .device.device_config import DeviceConfigDialog

"""
An interface for creating and editing DeviceConfig objects.
"""


class DeviceColumnDefn(ObjectListView.ColumnDefn):
	"""
	A column with useful defaults.
	"""

	def __init__(self, align='left', *args, **kwargs):
		ObjectListView.ColumnDefn.__init__(self, align=align, *args, **kwargs)

		# No auto-width if space filling.
		if self.isSpaceFilling:
			self.width = 0


class DevicesPanel(wx.Panel):
	col_name = DeviceColumnDefn(title='Name', valueGetter='name', width=200)
	col_connection = DeviceColumnDefn(title='Connection', width=110,
			valueGetter=lambda x: '{0}onnected'.format('C' if x.device is not None else 'Disc'))
	col_setup = DeviceColumnDefn(title='Setup', width=70,
			valueGetter=lambda x: 'Setup...' if x.gui_setup is not None else '')
	col_status = DeviceColumnDefn(title='Status', isSpaceFilling=True, isEditable=False,
			valueGetter=lambda x: (x.device.status[0] if x.device.status else 'Idle') if x.device is not None else '')

	def __init__(self, parent, global_store, dialog_owner, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self.dialog_owner = dialog_owner

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## OLV.
		self.olv = ObjectListView.FastObjectListView(self)
		panel_box.Add(self.olv, proportion=1, flag=wx.ALL|wx.EXPAND)

		self.olv.SetColumns([self.col_name, self.col_connection, self.col_setup, self.col_status])
		self.olv.SetSortColumn(self.col_name)

		self.olv.cellEditMode = self.olv.CELLEDIT_DOUBLECLICK
		self.olv.Bind(ObjectListView.EVT_CELL_EDIT_STARTING, self.OnCellEditStarting)
		self.olv.Bind(ObjectListView.EVT_CELL_EDIT_FINISHING, self.OnCellEditFinishing)

		## Buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		panel_box.Add(button_box, proportion=0, flag=wx.ALL|wx.CENTER)

		### Row buttons.
		row_box = wx.BoxSizer(wx.HORIZONTAL)
		button_box.Add(row_box)

		add_button = wx.Button(self, wx.ID_ADD)
		add_button.Bind(wx.EVT_BUTTON, self.OnAddDevice)
		row_box.Add(add_button)

		remove_button = wx.Button(self, wx.ID_REMOVE)
		remove_button.Bind(wx.EVT_BUTTON, self.OnRemoveDevices)
		row_box.Add(remove_button)

		self.SetMinSize((600, 250))
		self.SetSizer(panel_box)

		with self.global_store.devices.lock:
			for name, dev in self.global_store.devices.iteritems():
				self.olv.AddObject(dev)

	def update_resources(self, old, new):
		"""
		Inform everybody of updated resources.
		"""

		(appeared, changed, disappeared) = old.diff_resources(new)

		with self.global_store.resources.lock:
			# Check for conflicts.
			conflicting_resources = [label for label in appeared if label in self.global_store.resources]
			if conflicting_resources:
				return conflicting_resources

			# Set up the resources.
			for label in disappeared.union(changed):
				del self.global_store.resources[label]

			for label in appeared.union(changed):
				self.global_store.resources[label] = new.resources[label]

		return []

	def OnCellEditStarting(self, evt):
		col = evt.objectListView.columns[evt.subItemIndex]
		dev = evt.rowModel

		# Ignore frivolous requests.
		if evt.rowIndex < 0:
			evt.Veto()
			return

		veto = False

		if col == self.col_connection:
			def ok_callback(dlg):
				dev_new = dlg.GetValue()
				# Use the new instance.
				with self.global_store.devices.lock:
					del self.global_store.devices[dev.name]
					self.global_store.devices[dev_new.name] = dev_new

				conflicting_resources = self.update_resources(dev, dev_new)
				if conflicting_resources:
					MessageDialog(self, ', '.join(conflicting_resources), 'Conflicting resources').Show()

					return False

				# Close the old device as necessary.
				if dev.device is not None and dev_new.device != dev.device:
					dev.device.close()

				self.olv.RemoveObject(dev)
				self.olv.AddObject(dev_new)

				return True

			dlg = DeviceConfigDialog(self, ok_callback, title=dev.name)
			dlg.SetValue(dev)
			dlg.Show()

			veto = True
		elif col == self.col_setup:
			if dev.gui_setup is not None:
				dev.gui_setup(self.dialog_owner, self.global_store, dev.name).Show()

			veto = True

		if veto:
			# No need to use the default editor.
			evt.Veto()

	def OnCellEditFinishing(self, evt):
		col = evt.objectListView.columns[evt.subItemIndex]

		if col == self.col_name:
			dev = evt.rowModel # With old name.
			dev_new_name = evt.editor.Value

			if dev_new_name == dev.name:
				# Not actually changed.
				return

			# Attempt to add a new entry first.
			try:
				self.global_store.devices[dev_new_name] = dev
			except KeyError:
				MessageDialog(self, dev_new_name, 'Device name conflicts').Show()
				evt.Veto()
				return

			# Remove the old entry.
			del self.global_store.devices[dev.name]

	def OnAddDevice(self, evt=None):
		"""
		Add a blank variable to the OLV.
		"""

		# Ensure that we get a unique name.
		with self.global_store.devices.lock:
			num = 1
			done = False
			while not done:
				name = 'New device {0}'.format(num)
				dev_cfg = DeviceConfig(name=name)

				try:
					self.global_store.devices[name] = dev_cfg
				except KeyError:
					num += 1
				else:
					done = True

		self.olv.AddObject(dev_cfg)

		# OLV likes to select a random item at this point.
		self.olv.DeselectAll()

	def OnRemoveDevices(self, evt=None):
		"""
		Remove all selected variables from the OLV.
		"""

		selected = self.olv.GetSelectedObjects()

		connected_devices = set()
		for row in selected:
			if row.device is not None:
				connected_devices.add(row.name)

		if connected_devices:
			MessageDialog(self, ', '.join(sorted(connected_devices)), 'Devices still connected').Show()
			return

		if selected:
			self.olv.RemoveObjects(selected)

		for row in selected:
			del self.global_store.devices[row.name]


class DeviceConfigFrame(wx.Frame):
	def __init__(self, parent, global_store, close_callback, *args, **kwargs):
		wx.Frame.__init__(self, parent, title='Device Configuration', *args, **kwargs)

		self.close_callback = close_callback

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Devices.
		self.devices_panel = DevicesPanel(self, global_store, parent)
		frame_box.Add(self.devices_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

		thr = Thread(target=self.status_poller)
		thr.daemon = True
		thr.start()

	def status_poller(self):
		"""
		Keep updating the status as long as the frame is open.
		"""

		while True:
			try:
				wx.CallAfter(self.devices_panel.olv.RefreshObjects)
			except wx.PyDeadObjectError:
				# The panel has left the building.
				return

			sleep(0.2)

	def OnClose(self, evt):
		self.close_callback()

		evt.Skip()
