from functools import partial
import wx

from ...tool.box import Dialog, MessageDialog

"""
Graphical interface for data filters.
"""


class FilterEditDialog(Dialog):
	def __init__(self, parent, headings, ok_callback, *args, **kwargs):
		kwargs['style'] = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER
		kwargs['title'] = kwargs.get('title', 'Add filter')

		Dialog.__init__(self, parent, *args, **kwargs)

		self.ok_callback = ok_callback

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Inputs.
		input_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=5)
		input_sizer.AddGrowableCol(1, 1)
		dialog_box.Add(input_sizer, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

		input_sizer.Add(wx.StaticText(self, label='Column:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.column_input = wx.Choice(self, choices=headings)
		input_sizer.Add(self.column_input, flag=wx.EXPAND)

		input_sizer.Add(wx.StaticText(self, label='Function:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.function_input = wx.TextCtrl(self)
		self.function_input.SetMinSize((300, -1))
		input_sizer.Add(self.function_input, flag=wx.EXPAND)

		## Buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER|wx.ALL, border=5)

		ok_button = wx.Button(self, wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
		button_box.Add(ok_button)

		cancel_button = wx.Button(self, wx.ID_CANCEL)
		button_box.Add(cancel_button)

		self.SetSizerAndFit(dialog_box)

	def GetValue(self):
		return (self.column_input.StringSelection, self.function_input.Value)

	def SetValue(self, values):
		(self.column_input.StringSelection, self.function_input.Value) = values

	def OnOk(self, evt=None):
		try:
			self.ok_callback(self)
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return

		self.Destroy()


class FilterListDialog(Dialog):
	def __init__(self, parent, table, close_callback, filters=None, filter_columns=None,
			*args, **kwargs):
		kwargs['style'] = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER
		kwargs['title'] = kwargs.get('title', 'Filters')

		Dialog.__init__(self, parent, *args, **kwargs)

		self.table = table
		self.close_callback = close_callback

		if filters is None or filter_columns is None:
			self.filters, self.filter_columns = {}, {}
		else:
			self.filters, self.filter_columns = filters, filter_columns

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Filter list.
		self.filter_list = wx.ListBox(self, choices=self.filters.keys())
		self.filter_list.SetMinSize((100, 200))
		self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditFilter, self.filter_list)
		dialog_box.Add(self.filter_list, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

		## Buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER|wx.ALL, border=5)

		add_button = wx.Button(self, wx.ID_ADD)
		add_button.Bind(wx.EVT_BUTTON, self.OnAddFilter)
		button_box.Add(add_button, flag=wx.CENTER)

		remove_button = wx.Button(self, wx.ID_REMOVE)
		remove_button.Bind(wx.EVT_BUTTON, self.OnRemoveFilter)
		button_box.Add(remove_button, flag=wx.CENTER)

		self.SetSizerAndFit(dialog_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def create_filter(self, f_text, col):
		"""
		Create a filter out of text.
		"""

		col_idx = self.table.headings.index(col)

		return lambda i, x: eval(f_text.replace('x', 'float(x[{0}])'.format(col_idx)))

	@property
	def meta_filter(self):
		"""
		Create a meta-filter out of all the filters.
		"""

		filters = [self.create_filter(f, col) for f, col in
				zip(self.filters.values(), self.filter_columns.values())]

		return lambda i, x: all([f(i, x) for f in filters])

	def edit_ok_callback(self, dlg, selection=None):
		col, f = dlg.GetValue()

		name = '{0}: {1}'.format(col, f)

		if selection is not None and name == selection:
			return

		if name in self.filters:
			raise ValueError('Filter "{0}" already exists'.format(name))

		if not f:
			raise ValueError('No function provided')

		f_function = self.create_filter(f, col)

		try:
			self.table.apply_filter(f_function)
		except Exception as e:
			raise ValueError(e)

		if selection is not None:
			self.OnRemoveFilter(selection=selection)
			self.table.apply_filter(f_function)

		self.filters[name] = f
		self.filter_columns[name] = col
		self.filter_list.Items += [name]

	def OnAddFilter(self, evt=None):
		FilterEditDialog(self, self.table.headings, self.edit_ok_callback).Show()

	def OnEditFilter(self, evt=None):
		selection = self.filter_list.StringSelection

		if not selection:
			return

		dlg = FilterEditDialog(self, self.table.headings, partial(self.edit_ok_callback, selection=selection),
				title='Edit filter')
		dlg.SetValue((self.filter_columns[selection], self.filters[selection]))
		dlg.Show()

	def OnRemoveFilter(self, evt=None, selection=None):
		if selection is None:
			selection = self.filter_list.StringSelection

		if not selection:
			return

		try:
			del self.filters[selection]
		except KeyError:
			pass

		try:
			del self.filter_columns[selection]
		except KeyError:
			pass

		self.filter_list.Items = [x for x in self.filter_list.Items if x != selection]

		self.table.apply_filter(self.meta_filter, afresh=True)

	def OnClose(self, evt):
		self.close_callback(self)

		evt.Skip()
