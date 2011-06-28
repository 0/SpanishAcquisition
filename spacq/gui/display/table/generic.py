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
		self.rows = []

	def GetValue(self):
		return (self.headings, self.rows)

	def SetValue(self, headings, rows):
		self.ClearAll()

		self.headings = headings
		self.rows = rows
		self.SetItemCount(len(rows))

		if rows:
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

		value = self.rows[item][col]

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

	def GetValue(self):
		return self.table.GetValue()

	def SetValue(self, headings, values):
		self.table.SetValue(headings, values)
