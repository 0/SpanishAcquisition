from os.path import dirname
import wx

from spacq.interface.pulse.program import Program
from spacq.interface.units import IncompatibleDimensions, Quantity

from ..display.pulse import PulseProgramPanel
from ..tool.box import determine_wildcard, MessageDialog


class PulseProgramFrame(wx.Frame):
	def __init__(self, parent, close_callback, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		self.close_callback = close_callback

		# Menu.
		menuBar = wx.MenuBar()

		## File.
		menu = wx.Menu()
		menuBar.Append(menu, '&File')

		item = menu.Append(wx.ID_OPEN, '&Open...')
		self.Bind(wx.EVT_MENU, self.OnMenuFileOpen, item)

		item = menu.Append(wx.ID_CLOSE, '&Close')
		self.Bind(wx.EVT_MENU, self.OnMenuFileClose, item)

		self.SetMenuBar(menuBar)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Configuration.
		configuration_box = wx.BoxSizer(wx.HORIZONTAL)
		frame_box.Add(configuration_box, flag=wx.EXPAND|wx.ALL, border=5)

		### Values
		values_sizer = wx.FlexGridSizer(rows=2, cols=2)
		values_sizer.AddGrowableCol(1, 1)
		configuration_box.Add(values_sizer, proportion=1, flag=wx.EXPAND)

		#### Output.
		values_sizer.Add(wx.StaticText(self, label='Output: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.output_input = wx.TextCtrl(self)
		values_sizer.Add(self.output_input, flag=wx.EXPAND)

		#### Frequency.
		values_sizer.Add(wx.StaticText(self, label='Frequency: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.frequency_input = wx.TextCtrl(self)
		values_sizer.Add(self.frequency_input, flag=wx.EXPAND)

		### Set.
		set_frequency_button = wx.Button(self, label='Set')
		self.Bind(wx.EVT_BUTTON, self.OnSet, set_frequency_button)
		configuration_box.Add(set_frequency_button, flag=wx.EXPAND)

		## Display.
		self.pulse_panel = PulseProgramPanel(self)
		self.pulse_panel.SetMinSize((800, 600))
		frame_box.Add(self.pulse_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.frequency_input.Value = str(self.pulse_panel.frequency)
		self.output_input.Value = str(self.pulse_panel.output)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnSet(self, evt=None):
		try:
			q = Quantity(self.frequency_input.Value)
			q.assert_dimensions('Hz')
		except ValueError:
			MessageDialog(self, 'Expected a quantity like "1.2 GHz".', 'Invalid quantity').Show()
			return
		except IncompatibleDimensions:
			MessageDialog(self, 'Expected a frequency value.', 'Not a frequency').Show()
			return

		self.pulse_panel.frequency = q
		self.pulse_panel.output = self.output_input.Value

	def OnMenuFileOpen(self, evt=None):
		wildcard = determine_wildcard('pulse', 'Pulse program')
		dlg = wx.FileDialog(parent=self, message='Load...', wildcard=wildcard,
				style=wx.FD_OPEN)

		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()

			prog = Program.from_file(path)

			self.pulse_panel.SetValue(prog, dir=dirname(path))

	def OnMenuFileClose(self, evt=None):
		self.pulse_panel.SetValue(None)

	def OnClose(self, evt=None):
		self.close_callback()
