from numpy import linspace
import wx

from spacq.interface.units import Quantity

from .plot.two_dimensional import TwoDimensionalPlot


class WaveformDisplay(TwoDimensionalPlot):
	def __init__(self, parent, *args, **kwargs):
		TwoDimensionalPlot.__init__(self, parent, *args, **kwargs)

		self.padding_left = 50

	@property
	def control(self):
		return TwoDimensionalPlot.control.__get__(self)


class PulseProgramPanel(wx.Panel):
	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self._frequency = Quantity('1.0 GHz')
		self.output = ''
		self.prog = None
		self.dir = None

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Waveform plot.
		self.waveform_plot = WaveformDisplay(self)
		panel_box.Add(self.waveform_plot.control, proportion=1, flag=wx.EXPAND)

		self.SetSizer(panel_box)

	def draw_waveform(self):
		if self.prog is None:
			self.waveform_plot.x_data = [0]
			self.waveform_plot.y_data = [0]

			return

		self.prog.generate_waveforms(self.frequency.value)

		waveform = self.prog.env.waveforms[self.output].wave

		self.waveform_plot.x_data = linspace(0, len(waveform) / self.frequency.value, len(waveform))
		self.waveform_plot.y_data = waveform

		self.waveform_plot.x_autoscale()
		self.waveform_plot.y_autoscale()

	@property
	def frequency(self):
		"""
		The frequency of the resulting waveform.
		"""

		return self._frequency

	@frequency.setter
	def frequency(self, value):
		self._frequency = value

		self.draw_waveform()

	def GetValue(self):
		return self.prog, self.dir

	def SetValue(self, prog, dir=None):
		self.prog = prog
		self.dir = dir

		self.draw_waveform()
