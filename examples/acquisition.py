#!/usr/bin/env python2

import logging
logging.basicConfig(level=logging.WARNING)

import wx

from spacq import VERSION
from spacq.gui.action.data_capture import DataCapturePanel
from spacq.gui.action.smooth_reset import SmoothResetPanel
from spacq.gui.config.devices import DeviceConfigFrame
from spacq.gui.config.pulse import PulseProgramFrame
from spacq.gui.config.variables import VariablesPanel
from spacq.gui.display.plot.live.list import ListMeasurementFrame
from spacq.gui.display.plot.live.scalar import ScalarMeasurementFrame
from spacq.gui.global_store import GlobalStore
from spacq.gui.tool.box import MessageDialog


class SweepingAcquisitionFrame(wx.Frame):
	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Variables.
		self.variables_panel = VariablesPanel(self, global_store)
		self.variables_panel.SetMinSize((800, 300))
		frame_box.Add(self.variables_panel, proportion=1, flag=wx.EXPAND)

		## Bottom.
		bottom_box = wx.BoxSizer(wx.HORIZONTAL)
		frame_box.Add(bottom_box, flag=wx.EXPAND)

		### Data capture.
		self.data_capture_panel = DataCapturePanel(self, global_store, style=wx.BORDER_RAISED)
		bottom_box.Add(self.data_capture_panel, proportion=1, flag=wx.EXPAND)

		### Smooth reset.
		self.smooth_reset_panel = SmoothResetPanel(self, global_store, style=wx.BORDER_RAISED)
		bottom_box.Add(self.smooth_reset_panel, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnClose(self, evt):
		if self.data_capture_panel.capture_dialogs > 0:
			msg = 'Cannot exit, as a sweep is currently in progress.'
			MessageDialog(self, msg, 'Sweep in progress').Show()

			evt.Veto()
		else:
			evt.Skip()


class AcquisitionApp(wx.App):
	def OnInit(self):
		self.global_store = GlobalStore()

		# Frames.
		self.acq_frame = SweepingAcquisitionFrame(None, self.global_store, title='Acquisition')
		self.device_config_frame = None
		self.pulse_program_frame = None

		# Menu.
		menuBar = wx.MenuBar()

		## Configuration.
		menu = wx.Menu()
		menuBar.Append(menu, '&Configuration')

		### Devices.
		item = menu.Append(wx.ID_ANY, '&Devices...')
		self.Bind(wx.EVT_MENU, self.OnMenuConfigurationDevices, item)

		### Measurements.
		submenu = wx.Menu()
		menu.AppendMenu(wx.ID_ANY, '&Measurements', submenu)

		item = submenu.Append(wx.ID_ANY, 'Add &scalar...')
		self.Bind(wx.EVT_MENU, self.OnMenuConfigurationMeasurementsAddScalar, item)

		item = submenu.Append(wx.ID_ANY, 'Add &list...')
		self.Bind(wx.EVT_MENU, self.OnMenuConfigurationMeasurementsAddList, item)

		### Pulse program.
		item = menu.Append(wx.ID_ANY, '&Pulse program...')
		self.Bind(wx.EVT_MENU, self.OnMenuConfigurationPulseProgram, item)

		## Help.
		menu = wx.Menu()
		menuBar.Append(menu, '&Help')

		### About.
		item = menu.Append(wx.ID_ABOUT, '&About...')
		self.Bind(wx.EVT_MENU, self.OnMenuHelpAbout, item)

		self.acq_frame.SetMenuBar(menuBar)

		# Display.
		self.acq_frame.SetSizerAndFit(self.acq_frame.Sizer)
		self.acq_frame.Show()
		self.SetTopWindow(self.acq_frame)
		self.acq_frame.Raise()

		return True

	def OnMenuConfigurationDevices(self, evt=None):
		def close_callback():
			self.device_config_frame = None

		if self.device_config_frame is None:
			self.device_config_frame = DeviceConfigFrame(self.acq_frame, self.global_store, close_callback)
			self.device_config_frame.Fit()
			self.device_config_frame.Show()

		self.device_config_frame.Raise()

	def OnMenuConfigurationMeasurementsAddScalar(self, evt=None):
		measurement_frame = ScalarMeasurementFrame(self.acq_frame, self.global_store)
		measurement_frame.Show()

	def OnMenuConfigurationMeasurementsAddList(self, evt=None):
		measurement_frame = ListMeasurementFrame(self.acq_frame, self.global_store)
		measurement_frame.Show()

	def OnMenuConfigurationPulseProgram(self, evt=None):
		def close_callback():
			self.pulse_program_frame = None

		if self.pulse_program_frame is None:
			self.pulse_program_frame = PulseProgramFrame(self.acq_frame, self.global_store, close_callback)
			self.pulse_program_frame.Fit()
			self.pulse_program_frame.Show()

		self.pulse_program_frame.Raise()

	def OnMenuHelpAbout(self, evt=None):
		info = wx.AboutDialogInfo()
		info.SetName('Acquisition')
		info.SetDescription(
			'An application for sweeping device values and acquiring data.\n'
			'\n'
			'Using Spanish Acquisition version {0}.'.format(VERSION)
		)

		wx.AboutBox(info)


if __name__ == "__main__":
	app = AcquisitionApp()
	app.MainLoop()
