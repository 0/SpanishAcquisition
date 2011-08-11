from functools import partial
from threading import Thread
import wx
from wx.gizmos import TreeListCtrl

from spacq.interface.resources import NotReadable
from spacq.interface.units import IncompatibleDimensions

from ...tool.box import MessageDialog

"""
A tree of subdevices and resources.
"""


class ResourceFetcher(Thread):
	"""
	A thread which iterates over a list of items, getting resource values.
	"""

	def __init__(self, items, getter, callback, *args, **kwargs):
		"""
		items: List of TreeListCtrl items.
		getter: Given an item, returns a Resource or None.
		callback: Is called with the item and the value of the resource.
		"""

		Thread.__init__(self, *args, **kwargs)

		self.items = items
		self.getter = getter
		self.callback = callback

	def run(self):
		try:
			for item in self.items:
				resource = self.getter(item)

				if resource is not None and resource.readable:
					if resource.slow:
						wx.CallAfter(self.callback, item, '[N/A]')
					else:
						wx.CallAfter(self.callback, item, resource.value)
		except wx.PyDeadObjectError:
			# The values are no longer wanted.
			return


class ItemData(object):
	"""
	Useful information about a node to be stored in its PyData.
	"""

	def __init__(self, path, resource):
		self.path = path
		self.resource = resource

		self.fetched = False


class ResourceTree(TreeListCtrl):
	"""
	A tree list to display an hierarchy of subdevices and resources.
	"""

	def __init__(self, parent, *args, **kwargs):
		TreeListCtrl.__init__(self, parent, *args,
				style=wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_HIDE_ROOT,
				**kwargs)

		self.root = None
		self.resource_labels = []

		self.col_name = 0
		self.AddColumn('Name', 200)
		self.col_r = 1
		self.AddColumn('R', 24)
		self.col_w = 2
		self.AddColumn('W', 24)
		self.col_units = 3
		self.AddColumn('Units', 50)
		self.col_label = 4
		self.AddColumn('Label', 200, edit=True)
		self.col_value = 5
		self.AddColumn('Value', 400, edit=True)

		# Extra 50 for nesting.
		self.SetMinSize((950, -1))

		self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded)
		self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
		self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndLabelEdit)
		self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated)

	def GetChildren(self, item):
		"""
		Non-recursive generator for the children of an item.
		"""

		if self.HasChildren(item):
			child, cookie = self.GetFirstChild(item)

			while child:
				yield child

				child, cookie = self.GetNextChild(item, cookie)

	def GetLeaves(self, item=None):
		"""
		Recursively collect the leaves under an item.
		"""

		if item is None:
			if self.root is None:
				return []
			else:
				item = self.root

		if not self.HasChildren(item):
			return [item]
		else:
			result = []

			for child in self.GetChildren(item):
				result.extend(self.GetLeaves(child))

			return result

	def fell(self):
		"""
		Cut down the tree.
		"""

		self.DeleteAllItems()
		self.root = None

	def spawn_fetch_thread(self, items):
		"""
		Create a thread to populate the items.
		"""

		def fetch(item):
			pydata = self.GetItemPyData(item)

			if pydata is not None:
				if not pydata.fetched:
					pydata.fetched = True

					return pydata.resource

		def set(item, value):
			try:
				self.SetItemText(item, str(value), self.col_value)
			except wx.PyDeadObjectError:
				# The value isn't wanted anymore.
				return

		thr = ResourceFetcher(items, fetch, set)
		thr.daemon = True
		thr.start()

	def build_tree(self, device, resource_labels, root=None, path=None):
		"""
		Recursively append all subdevices and resources.
		"""

		if root is None:
			self.fell()

			self.root = self.AddRoot('')
			root = self.root

			path = ()

		for name, subdev in device.subdevices.items():
			item = self.AppendItem(root, name)
			full_path = path + (name,)

			self.build_tree(subdev, resource_labels, item, full_path)

		for name, resource in device.resources.items():
			item = self.AppendItem(root, name)
			full_path = path + (name,)

			if resource.getter is not None:
				self.SetItemText(item, 'R', self.col_r)

			if resource.setter is not None:
				self.SetItemText(item, 'W', self.col_w)

			if resource.display_units is not None:
				self.SetItemText(item, resource.display_units, self.col_units)

			self.SetItemPyData(item, ItemData(full_path, resource))

			if full_path in resource_labels:
				self.SetItemText(item, resource_labels[full_path], self.col_label)

		self.SortChildren(root)

		if root == self.root:
			self.spawn_fetch_thread(self.GetChildren(self.root))

	def set_value(self, item, value, error_callback=None):
		"""
		Set the value of a resource, as well as the displayed value.
		"""

		pydata = self.GetItemPyData(item)
		resource = pydata.resource

		def update():
			try:
				resource.value = resource.convert(value)
			except IncompatibleDimensions:
				if error_callback is not None:
					error_callback(ValueError('Expected dimensions to match "{0}"'.format(resource.units)))
				else:
					raise
			except Exception as e:
				if error_callback is not None:
					error_callback(e)
				else:
					raise

			try:
				true_value = str(resource.value)
			except NotReadable:
				pass
			else:
				wx.CallAfter(self.SetItemText, item, true_value, self.col_value)

		thr = Thread(target=update)
		thr.daemon = True
		thr.start()

	def OnItemExpanded(self, evt):
		"""
		Get any resources which may now be visible.
		"""

		self.spawn_fetch_thread(self.GetChildren(evt.Item))

	def OnBeginLabelEdit(self, evt):
		# EVT_TREE_END_LABEL_EDIT does not carry this value.
		self.editing_col = evt.Int

		if evt.Int == self.col_label:
			# Only resources can have labels.
			if not (self.GetItemText(evt.Item, self.col_r) or
					self.GetItemText(evt.Item, self.col_w)):
				evt.Veto()
			else:
				self.old_label = self.GetItemText(evt.Item, self.col_label)
		elif evt.Int == self.col_value:
			# Can only write to writable resources.
			if not self.GetItemText(evt.Item, self.col_w):
				evt.Veto()

			pydata = self.GetItemPyData(evt.Item)
			resource = pydata.resource

			if resource.allowed_values is not None:
				options = [str(x) for x in sorted(resource.allowed_values)]

				dlg = wx.SingleChoiceDialog(self, '', 'Choose value', options)
				# Select the current value if possible.
				try:
					dlg.SetSelection(options.index(self.GetItemText(evt.Item, self.col_value)))
				except ValueError:
					pass

				if dlg.ShowModal() == wx.ID_OK:
					try:
						self.set_value(evt.Item, dlg.GetStringSelection())
					except ValueError as e:
						MessageDialog(self, str(e), 'Invalid value').Show()
						return

				# No need for the editor.
				evt.Veto()
		else:
			evt.Veto()

	def OnEndLabelEdit(self, evt):
		if self.editing_col == self.col_label:
			# Prevent duplicates.
			value = evt.Label

			# Don't do anything if unchanged.
			if value != self.old_label:
				if value not in self.resource_labels:
					if self.old_label:
						self.resource_labels.remove(self.old_label)
					if value:
						self.resource_labels.append(value)
				else:
					evt.Veto()
					MessageDialog(self, str(value), 'Duplicate label').Show()
					return
		elif self.editing_col == self.col_value:
			# Update the real value.
			value = evt.Label

			def error_callback(e):
				MessageDialog(self, str(e), 'Invalid value').Show()

			self.set_value(evt.Item, value, error_callback=partial(wx.CallAfter, error_callback))

	def OnActivated(self, evt):
		"""
		Double click to edit.
		"""

		self.EditLabel(evt.Item, evt.Int)


class DeviceResourcesPanel(wx.Panel):
	"""
	A panel for displaying the subdevices and resources of a device.
	"""

	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Tree.
		self.tree = ResourceTree(self)
		panel_box.Add(self.tree, proportion=1, flag=wx.EXPAND)

		self.SetSizer(panel_box)

	def set_device(self, device, resource_labels):
		if device is None:
			self.tree.fell()
		else:
			self.tree.build_tree(device, resource_labels)

	def GetValue(self):
		labels = {}
		resources = {}

		for leaf in self.tree.GetLeaves():
			pydata = self.tree.GetItemPyData(leaf)
			name = self.tree.GetItemText(leaf, self.tree.col_label)

			if name:
				labels[pydata.path] = name
				resources[name] = pydata.resource

		return (labels, resources)

	def SetValue(self, resource_labels, resources):
		for path, name in resource_labels.items():
			for leaf in self.tree.GetLeaves():
				pydata = self.tree.GetItemPyData(leaf)

				if pydata.path == path:
					self.tree.SetItemText(leaf, name, self.tree.col_label)

		self.tree.resource_labels = resource_labels.values()
