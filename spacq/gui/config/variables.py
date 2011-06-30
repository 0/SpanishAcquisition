import ObjectListView
import wx

from spacq.iteration.variables import LinSpaceVariable

from ..tool.box import ErrorMessageDialog, load_pickled, save_pickled

"""
An interface for creating and editing Variable objects.
"""


class VariableColumnDefn(ObjectListView.ColumnDefn):
	"""
	A column with useful defaults.
	"""

	def __init__(self, width=90, align='centre', groupKeyGetter='order', *args, **kwargs):
		ObjectListView.ColumnDefn.__init__(self, width=width, align=align,
				groupKeyGetter=groupKeyGetter, *args, **kwargs)

		# No auto-width if space filling.
		if self.isSpaceFilling:
			self.width = 0


class VariablesPanel(wx.Panel):
	col_name = VariableColumnDefn(checkStateGetter='enabled', title='Name', valueGetter='name',
			isSpaceFilling=True, align='left')
	col_order = VariableColumnDefn(title='#', valueGetter='order', width=40)
	col_resource = VariableColumnDefn(title='Resource', valueGetter='resource_name',
			isSpaceFilling=True, align='left')
	col_initial = VariableColumnDefn(title='Initial', valueGetter='initial')
	col_final = VariableColumnDefn(title='Final', valueGetter='final')
	col_steps = VariableColumnDefn(title='Steps', valueGetter='steps')
	col_wait = VariableColumnDefn(title='Wait time', valueGetter='wait')
	col_const = VariableColumnDefn(checkStateGetter='use_const', title='Const. value',
			valueGetter='const')

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## OLV.
		self.olv = ObjectListView.GroupListView(self)
		panel_box.Add(self.olv, proportion=1, flag=wx.ALL|wx.EXPAND)

		self.olv.SetColumns([self.col_name, self.col_order, self.col_resource, self.col_initial,
				self.col_final, self.col_steps, self.col_wait, self.col_const])
		self.olv.SetSortColumn(self.col_order)

		self.olv.cellEditMode = self.olv.CELLEDIT_DOUBLECLICK
		self.olv.Bind(ObjectListView.EVT_CELL_EDIT_FINISHING, self.OnCellEditFinishing)
		self.olv.Bind(ObjectListView.EVT_CELL_EDIT_FINISHED, self.OnCellEditFinished)

		## Buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		panel_box.Add(button_box, proportion=0, flag=wx.ALL|wx.CENTER)

		### Row buttons.
		row_box = wx.BoxSizer(wx.HORIZONTAL)
		button_box.Add(row_box)

		add_button = wx.Button(self, wx.ID_ADD)
		add_button.Bind(wx.EVT_BUTTON, self.OnAddVariable)
		row_box.Add(add_button)

		remove_button = wx.Button(self, wx.ID_REMOVE)
		remove_button.Bind(wx.EVT_BUTTON, self.OnRemoveVariables)
		row_box.Add(remove_button)

		### Export buttons.
		export_box = wx.BoxSizer(wx.HORIZONTAL)
		button_box.Add(export_box, flag=wx.LEFT, border=20)

		save_button = wx.Button(self, wx.ID_SAVE, label='Save...')
		save_button.Bind(wx.EVT_BUTTON, self.OnSave)
		export_box.Add(save_button)

		load_button = wx.Button(self, wx.ID_OPEN, label='Load...')
		load_button.Bind(wx.EVT_BUTTON, self.OnLoad)
		export_box.Add(load_button)

		self.SetSizer(panel_box)

	def max_order(self):
		"""
		Find the highest-used order in the OLV.
		"""

		try:
			return max(x.order for x in self.olv.GetObjects())
		except ValueError:
			return 0

	def OnCellEditFinishing(self, evt):
		col = evt.objectListView.columns[evt.subItemIndex]

		if col == self.col_name:
			var = evt.rowModel # With old name.
			var_new_name = evt.editor.Value

			if var_new_name == var.name:
				# Not actually changed.
				return

			# Attempt to add a new entry first.
			try:
				self.global_store.variables[var_new_name] = var
			except KeyError:
				ErrorMessageDialog(self, var_new_name, 'Variable name conflicts').Show()
				evt.Veto()
				return

			# Remove the old entry.
			del self.global_store.variables[var.name]

	def OnCellEditFinished(self, evt):
		col = evt.objectListView.columns[evt.subItemIndex]

		if col == self.col_order:
			self.olv.RebuildGroups()

	def OnSave(self, evt=None):
		"""
		Save all the rows in the OLV.
		"""

		try:
			save_pickled(self, self.olv.GetObjects(), extension='var', file_type='Variables')
		except IOError as e:
			ErrorMessageDialog(self, str(e), 'Save error').Show()
			return

	def OnLoad(self, evt=None):
		"""
		Load some rows to the OLV.
		"""

		try:
			values = load_pickled(self, extension='var', file_type='Variables')
		except IOError as e:
			ErrorMessageDialog(self, str(e), 'Load error').Show()
			return

		if values is not None:
			# Clear the OLV.
			for var in self.olv.GetObjects():
				del self.global_store.variables[var.name]
				self.olv.RemoveObject(var)

			conflicting_names = []
			for var in values:
				try:
					self.global_store.variables[var.name] = var
				except KeyError:
					conflicting_names.append(var.name)
					continue

				self.olv.AddObject(var)

			if conflicting_names:
				ErrorMessageDialog(self, ', '.join(conflicting_names), 'Variable names conflict').Show()

	def OnAddVariable(self, evt=None):
		"""
		Add a blank variable to the OLV.
		"""

		# Ensure that we get a unique name.
		with self.global_store.variables.lock:
			num = 1
			done = False
			while not done:
				name = 'New variable {0}'.format(num)
				var = LinSpaceVariable(name=name, order=self.max_order()+1)

				try:
					self.global_store.variables[name] = var
				except KeyError:
					num += 1
				else:
					done = True

		self.olv.AddObject(var)

		# OLV likes to select a random item at this point.
		self.olv.DeselectAll()

	def OnRemoveVariables(self, evt=None):
		"""
		Remove all selected variables from the OLV.
		"""

		selected = self.olv.GetSelectedObjects()

		if selected:
			self.olv.RemoveObjects(selected)

		for row in selected:
			del self.global_store.variables[row.name]
