import ObjectListView
import wx

from spacq.interface.units import Quantity
from spacq.iteration.variables import OutputVariable, LinSpaceConfig, ArbitraryConfig

from ..tool.box import Dialog, MessageDialog, load_pickled, save_pickled

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


class LinSpaceConfigPanel(wx.Panel):
	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Config.
		config_sizer = wx.FlexGridSizer(rows=3, cols=2)
		config_sizer.AddGrowableCol(1, 1)
		panel_box.Add(config_sizer, proportion=1, flag=wx.EXPAND)

		### Initial.
		config_sizer.Add(wx.StaticText(self, label='Initial:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
		self.initial_input = wx.TextCtrl(self)
		config_sizer.Add(self.initial_input, flag=wx.EXPAND|wx.ALL, border=5)

		### Final.
		config_sizer.Add(wx.StaticText(self, label='Final:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
		self.final_input = wx.TextCtrl(self)
		config_sizer.Add(self.final_input, flag=wx.EXPAND|wx.ALL, border=5)

		### Steps.
		config_sizer.Add(wx.StaticText(self, label='Steps:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
		self.steps_input = wx.SpinCtrl(self, min=1, initial=1, max=1e9)
		config_sizer.Add(self.steps_input, flag=wx.EXPAND|wx.ALL, border=5)

		self.SetSizerAndFit(panel_box)

	def GetValue(self):
		# Ensure the values are sane.
		try:
			initial = float(self.initial_input.Value)
		except ValueError:
			raise ValueError('Invalid initial value.')

		try:
			final = float(self.final_input.Value)
		except ValueError:
			raise ValueError('Invalid final value.')

		return LinSpaceConfig(initial, final, self.steps_input.Value)

	def SetValue(self, config):
		self.initial_input.Value, self.final_input.Value, self.steps_input.Value = (str(config.initial),
				str(config.final), config.steps)


class ArbitraryConfigPanel(wx.Panel):
	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Config.
		config_sizer = wx.FlexGridSizer(rows=1, cols=2)
		config_sizer.AddGrowableCol(1, 1)
		panel_box.Add(config_sizer, proportion=1, flag=wx.EXPAND)

		### Values.
		config_sizer.Add(wx.StaticText(self, label='Values:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
		self.values_input = wx.TextCtrl(self)
		config_sizer.Add(self.values_input, flag=wx.EXPAND|wx.ALL, border=5)

		self.SetSizerAndFit(panel_box)

	def GetValue(self):
		raw_values = self.values_input.Value.split(',')

		# Ensure the values are sane.
		try:
			values = [float(x) for x in raw_values]
		except ValueError as e:
			raise ValueError('Invalid value: {0}'.format(str(e)))

		return ArbitraryConfig(values)

	def SetValue(self, config):
		self.values_input.Value = ', '.join('{0:n}'.format(x) for x in config.values)


class VariableEditor(Dialog):
	def __init__(self, parent, ok_callback, *args, **kwargs):
		kwargs['style'] = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER

		Dialog.__init__(self, parent, *args, **kwargs)

		self.ok_callback = ok_callback

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Config.
		self.config_notebook = wx.Notebook(self)
		dialog_box.Add(self.config_notebook, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

		self.config_panel_types = []

		### Linear.
		linspace_config_panel = LinSpaceConfigPanel(self.config_notebook)
		self.config_panel_types.append(LinSpaceConfig)
		self.config_notebook.AddPage(linspace_config_panel, 'Linear')

		### Arbitrary.
		arbitrary_config_panel = ArbitraryConfigPanel(self.config_notebook)
		self.config_panel_types.append(ArbitraryConfig)
		self.config_notebook.AddPage(arbitrary_config_panel, 'Arbitrary')

		## Smooth set.
		smooth_static_box = wx.StaticBox(self, label='Smooth set')
		smooth_box = wx.StaticBoxSizer(smooth_static_box, wx.HORIZONTAL)
		dialog_box.Add(smooth_box, flag=wx.CENTER|wx.ALL, border=5)

		smooth_box.Add(wx.StaticText(self, label='Steps:'), flag=wx.CENTER)

		self.smooth_steps_input = wx.SpinCtrl(self, min=1, initial=10)
		smooth_box.Add(self.smooth_steps_input, flag=wx.CENTER|wx.ALL, border=5)

		self.smooth_from_checkbox = wx.CheckBox(self, label='From const')
		smooth_box.Add(self.smooth_from_checkbox, flag=wx.CENTER|wx.ALL, border=5)

		self.smooth_to_checkbox = wx.CheckBox(self, label='To const')
		smooth_box.Add(self.smooth_to_checkbox, flag=wx.CENTER|wx.ALL, border=5)

		self.smooth_transition_checkbox = wx.CheckBox(self, label='Transition')
		smooth_box.Add(self.smooth_transition_checkbox, flag=wx.CENTER|wx.ALL, border=5)

		## Type.
		type_static_box = wx.StaticBox(self, label='Type')
		type_box = wx.StaticBoxSizer(type_static_box, wx.HORIZONTAL)
		dialog_box.Add(type_box, flag=wx.CENTER|wx.ALL, border=5)

		self.type_float = wx.RadioButton(self, label='Float', style=wx.RB_GROUP)
		type_box.Add(self.type_float, flag=wx.CENTER|wx.ALL, border=5)

		self.type_integer = wx.RadioButton(self, label='Integer')
		type_box.Add(self.type_integer, flag=wx.CENTER|wx.ALL, border=5)

		### Units.
		quantity_static_box = wx.StaticBox(self, label='Quantity')
		quantity_box = wx.StaticBoxSizer(quantity_static_box, wx.HORIZONTAL)
		type_box.Add(quantity_box)

		self.type_quantity = wx.RadioButton(self)
		quantity_box.Add(self.type_quantity, flag=wx.CENTER)

		self.units_input = wx.TextCtrl(self)
		quantity_box.Add(self.units_input)

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
		if self.type_float.Value:
			type = 'float'
			units = None
		elif self.type_integer.Value:
			type = 'integer'
			units = None
		else:
			type = 'quantity'
			units = self.units_input.Value

			# Ensure that the units are valid.
			Quantity(1, units)

		return (self.config_notebook.CurrentPage.GetValue(), self.smooth_steps_input.Value,
				self.smooth_from_checkbox.Value, self.smooth_to_checkbox.Value,
				self.smooth_transition_checkbox.Value, type, units)

	def SetValue(self, config, smooth_steps, smooth_from, smooth_to, smooth_transition, type, units):
		config_type = self.config_panel_types.index(config.__class__)
		self.config_notebook.ChangeSelection(config_type)
		self.config_notebook.CurrentPage.SetValue(config)

		(self.smooth_steps_input.Value, self.smooth_from_checkbox.Value,
				self.smooth_to_checkbox.Value,
				self.smooth_transition_checkbox.Value) = smooth_steps, smooth_from, smooth_to, smooth_transition

		if type == 'float':
			self.type_float.Value = True
		elif type == 'integer':
			self.type_integer.Value = True
		else:
			self.type_quantity.Value = True
			self.units_input.Value = units if units is not None else ''

	def OnOk(self, evt=None):
		if self.ok_callback(self):
			self.Destroy()


class VariablesPanel(wx.Panel):
	col_name = VariableColumnDefn(checkStateGetter='enabled', title='Name', valueGetter='name',
			width=150, align='left')
	col_order = VariableColumnDefn(title='#', valueGetter='order', width=40)
	col_resource = VariableColumnDefn(title='Resource', valueGetter='resource_name',
			width=150, align='left')
	col_values = VariableColumnDefn(title='Values', valueGetter=lambda x: str(x),
			isSpaceFilling=True, align='left')
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

		self.olv.SetColumns([self.col_name, self.col_order, self.col_resource, self.col_values,
				self.col_wait, self.col_const])
		self.olv.SetSortColumn(self.col_order)

		self.olv.cellEditMode = self.olv.CELLEDIT_DOUBLECLICK
		self.olv.Bind(ObjectListView.EVT_CELL_EDIT_STARTING, self.OnCellEditStarting)
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

	def OnCellEditStarting(self, evt):
		col = evt.objectListView.columns[evt.subItemIndex]
		var = evt.rowModel

		# Ignore frivolous requests.
		if evt.rowIndex < 0:
			evt.Veto()
			return

		if col == self.col_values:
			def ok_callback(dlg):
				try:
					values = dlg.GetValue()
				except ValueError as e:
					MessageDialog(self, str(e), 'Invalid value').Show()
					return False

				(var.config, var.smooth_steps, var.smooth_from, var.smooth_to,
						var.smooth_transition, var.type, var.units) = values

				return True

			dlg = VariableEditor(self, ok_callback, title=var.name)
			dlg.SetValue(var.config, var.smooth_steps, var.smooth_from, var.smooth_to, var.smooth_transition,
					var.type, var.units)
			dlg.Show()

			# No need to use the default editor.
			evt.Veto()

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
				MessageDialog(self, var_new_name, 'Variable name conflicts').Show()
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
			MessageDialog(self, str(e), 'Save error').Show()
			return

	def OnLoad(self, evt=None):
		"""
		Load some rows to the OLV.
		"""

		try:
			values = load_pickled(self, extension='var', file_type='Variables')
		except IOError as e:
			MessageDialog(self, str(e), 'Load error').Show()
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
				MessageDialog(self, ', '.join(conflicting_names), 'Variable names conflict').Show()

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
				var = OutputVariable(name=name, order=self.max_order()+1)

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
