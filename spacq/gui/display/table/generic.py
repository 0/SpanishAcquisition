from numpy import array, zeros
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

"""
Embeddable, generic, virtual, tabular display.
"""


class VirtualListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	"""
	A generic virtual list.
	"""

	max_value_len = 250 # Characters.

	def __init__(self, parent, *args, **kwargs):
		wx.ListCtrl.__init__(self, parent,
				style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES,
				*args, **kwargs)

		ListCtrlAutoWidthMixin.__init__(self)

		self.reset()

	def reset(self):
		self.headings = []
		self.data = array([])
		self.display_data = array([])

	def GetValue(self):
		return (self.headings, self.data)

	def SetValue(self, headings, data):
		"""
		headings: A list of strings.
		data: A 2D NumPy array.
		"""

		self.ClearAll()
		self.reset()

		self.headings = headings
		self.data = data

		self.ItemCount = len(data)

		if self.ItemCount > 0:
			self.display_data = zeros(self.data.shape, dtype='|S{0}'.format(self.max_value_len))

			width, height = self.GetSize()
			# Give some room for the scrollbar.
			col_width = (width - 50) / len(self.headings)

			for i, heading in enumerate(self.headings):
				self.InsertColumn(i, heading, width=col_width)

				# Truncate for display.
				self.display_data[:,i] = [x[:self.max_value_len] for x in self.data[:,i]]

		self.Refresh()

	def OnGetItemText(self, item, col):
		"""
		Return cell value for LC_VIRTUAL.
		"""

		return self.display_data[item,col]


class TabularDisplayPanel(wx.Panel):
	"""
	A panel to display arbitrary tabular data.
	"""

	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Table.
		self.table = VirtualListCtrl(self)
		panel_box.Add(self.table, proportion=1, flag=wx.EXPAND)

		self.SetSizer(panel_box)

	def __len__(self):
		return self.table.ItemCount

	def from_csv_data(self, has_header, values):
		"""
		Import the given CSV data into the table.

		If has_header is True, the first row is treated specially.
		If the first header is "__time__", it is converted to relative values.
		"""

		if has_header:
			headers, rows = values[0], array(values[1:])
		else:
			headers, rows = [''] * len(values[0]), array(values)

		# Ensure that all columns have a header.
		for i, header in enumerate(headers):
			if not header:
				headers[i] = 'Column {0}'.format(i + 1)

		self.SetValue(headers, rows)

	def GetValue(self):
		return self.table.GetValue()

	def SetValue(self, headings, values):
		self.table.SetValue(headings, values)


class TabularDisplayFrame(wx.Frame):
	def __init__(self, parent, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Display panel.
		self.display_panel = TabularDisplayPanel(self)
		frame_box.Add(self.display_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizer(frame_box)
