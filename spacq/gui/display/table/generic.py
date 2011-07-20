from numpy import array
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

"""
Embeddable, generic, virtual, tabular display.
"""


class VirtualListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	"""
	A generic virtual list.
	"""

	def __init__(self, parent, *args, **kwargs):
		wx.ListCtrl.__init__(self, parent,
				style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES,
				*args, **kwargs)

		ListCtrlAutoWidthMixin.__init__(self)

		self.headings = []
		self.data = array([])

	def GetValue(self):
		return (self.headings, self.data)

	def SetValue(self, headings, data):
		"""
		headings: A list of strings.
		data: A 2D NumPy array.
		"""

		self.ClearAll()

		self.headings = headings
		self.data = data

		self.ItemCount = len(data)

		if self.ItemCount > 0:
			width, height = self.GetSize()
			# Give some room for the scrollbar.
			col_width = (width - 50) / len(self.headings)

			for i, heading in enumerate(self.headings):
				self.InsertColumn(i, heading, width=col_width)

		self.Refresh()

	def OnGetItemText(self, item, col):
		"""
		Return cell value for LC_VIRTUAL.
		"""

		value = self.data[item,col]

		try:
			return '{0:n}'.format(value)
		except ValueError:
			# Not a number after all.
			return str(value)


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

		# Calculate relative times.
		if headers[0] == '__time__':
			try:
				times = rows[:,0].astype(float)
			except ValueError:
				# Pretend we never tried.
				pass
			else:
				min_time = min(times)

				for i in xrange(len(times)):
					rows[i,0] = times[i] - min_time

		# Ensure that all columns have a header.
		for i, header in enumerate(headers):
			if not header:
				headers[i] = 'Column {0}'.format(i + 1)

		self.SetValue(headers, rows)

	def GetValue(self):
		return self.table.GetValue()

	def SetValue(self, headings, values):
		self.table.SetValue(headings, values)
