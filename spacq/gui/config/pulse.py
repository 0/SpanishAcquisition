from functools import partial
from os.path import basename
from threading import Thread
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from spacq.interface.pulse.parser import PulseError, PulseSyntaxError
from spacq.interface.pulse.program import Program
from spacq.interface.units import IncompatibleDimensions, Quantity

from ..display.waveform import WaveformFrame
from ..tool.box import determine_wildcard, MessageDialog


def quantity_converter(x, symbols='s', dimensions='time', non_negative=True):
	try:
		q = Quantity(x)
		q.assert_dimensions(symbols)
	except (IncompatibleDimensions, ValueError):
		raise ValueError('Expected {0} quantity'.format(dimensions))

	if non_negative and q.value < 0:
		raise ValueError('Expected non-negative quantity')

	return q


class ParameterPanel(ScrolledPanel):
	"""
	A generic panel to display parameters of a particular type.
	"""

	attributes = False
	hide_variables = False

	default_background_color = None
	ok_background_color = 'PALE GREEN'

	def extract_variables(self, prog):
		"""
		By default, extract the variables which pertain to the current type.
		"""

		return [k for k, v in prog.env.variables.items() if v == self.type]

	def extract_parameters(self, prog):
		"""
		By default, extract the parameters which pertain to the current type.
		"""

		variables = self.extract_variables(prog)

		return sorted([item for item in prog.env.all_values for variable in variables if item[0] == variable])

	@property
	def num_cols(self):
		"""
		Number of columns per row.
		"""

		# Label and input field.
		cols = 2

		# Label includes attribute name.
		if self.attributes:
			cols += 1

		# Label excludes variable name.
		if self.hide_variables:
			cols -= 1

		return cols

	@property
	def input_col(self):
		"""
		The 0-based position of the growable input column.
		"""

		# Last column.
		return self.num_cols - 1

	def add_row(self, parameter):
		"""
		Add a parameter to the sizer and display the value if it is available.
		"""

		if not self.hide_variables:
			if self.last_variable == parameter[0]:
				label = ''
			else:
				label = parameter[0]
				self.last_variable = parameter[0]

			self.panel_sizer.Add(wx.StaticText(self, label=label),
					flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		if self.attributes:
			self.panel_sizer.Add(wx.StaticText(self, label=parameter[1]),
					flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)

		input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.parameter_inputs.append(input)
		self.panel_sizer.Add(input, flag=wx.EXPAND)

		if self.default_background_color is None:
			self.default_background_color = input.BackgroundColour

		try:
			input.Value = str(self.values[parameter])
		except KeyError:
			# No default value set.
			pass
		else:
			input.BackgroundColour = self.ok_background_color

		self.Bind(wx.EVT_TEXT, partial(self.OnChange, parameter), input)
		self.Bind(wx.EVT_TEXT_ENTER, partial(self.OnInput, parameter), input)

	def converter(self, parameter, x):
		"""
		Identity.
		"""

		return x

	def __init__(self, parent, prog, *args, **kwargs):
		ScrolledPanel.__init__(self, parent, *args, **kwargs)

		self.prog = prog
		self.values = prog.env.values
		self.parameter_inputs = []
		self.parameters = self.extract_parameters(prog)

		self.last_variable = None

		# Panel.
		self.panel_sizer = wx.FlexGridSizer(rows=len(self.parameters), cols=self.num_cols, hgap=5)

		self.panel_sizer.AddGrowableCol(self.input_col, 1)

		## Parameter inputs.
		for parameter in self.parameters:
			self.add_row(parameter)

		self.SetSizer(self.panel_sizer)
		self.SetupScrolling()

	def set_value(self, parameter, value):
		self.values[parameter] = value

	def OnChange(self, parameter, evt):
		# Awaiting validation.
		self.set_value(parameter, None)

		evt.EventObject.BackgroundColour = self.default_background_color

	def OnInput(self, parameter, evt):
		try:
			value = self.converter(parameter, evt.String)
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()

			return

		# Validated.
		self.set_value(parameter, value)

		evt.EventObject.BackgroundColour = self.ok_background_color


class AcqMarkerPanel(ParameterPanel):
	type = 'acq_marker'
	name = 'Acquisition'
	attributes = True
	hide_variables = True

	def converter(self, parameter, x):
		x = ParameterPanel.converter(self, parameter, x)

		if parameter[1] == 'marker_num':
			try:
				result = int(x)

				if result <= 0:
					raise ValueError()

				return result
			except ValueError:
				raise ValueError('Expected positive integer')
		elif parameter[1] == 'output':
			try:
				if self.prog.env.variables[x] == 'output':
					return x
				else:
					raise KeyError()
			except KeyError:
				raise ValueError('Expected valid output name')


class DelayPanel(ParameterPanel):
	type = 'delay'
	name = 'Delays'

	def converter(self, parameter, x):
		x = ParameterPanel.converter(self, parameter, x)

		return quantity_converter(x)


class IntPanel(ParameterPanel):
	type = 'int'
	name = 'Integers'

	def converter(self, parameter, x):
		x = ParameterPanel.converter(self, parameter, x)

		try:
			return int(x)
		except ValueError:
			raise ValueError('Expected integer')


class OutputPanel(ParameterPanel):
	type = 'output'
	name = 'Outputs'

	def extract_parameters(self, prog):
		return sorted([(x,) for x in self.extract_variables(prog)])

	@property
	def num_cols(self):
		return ParameterPanel.num_cols.__get__(self) + 1

	@property
	def input_col(self):
		return self.num_cols - 2

	def add_row(self, parameter):
		ParameterPanel.add_row(self, parameter)

		view_button = wx.Button(self, label='View')
		self.panel_sizer.Add(view_button)
		self.Bind(wx.EVT_BUTTON, partial(self.OnView, parameter), view_button)

	def __init__(self, *args, **kwargs):
		ParameterPanel.__init__(self, *args, **kwargs)

		# Spacers.
		for _ in xrange(self.num_cols):
			self.panel_sizer.Add((-1, 30))

		# Add frequency input.
		self.panel_sizer.Add(wx.StaticText(self, label='Frequency'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.freq_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.panel_sizer.Add(self.freq_input, flag=wx.EXPAND)

		self.freq_input.Value = str(self.prog.env.frequency)
		self.freq_input.BackgroundColour = self.ok_background_color

		self.Bind(wx.EVT_TEXT, self.OnFrequencyChange, self.freq_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnFrequencyInput, self.freq_input)

	def set_value(self, parameter, value):
		# TODO
		pass

	def OnFrequencyChange(self, evt=None):
		self.freq_input.BackgroundColour = self.default_background_color

	def OnFrequencyInput(self, evt=None):
		try:
			value = quantity_converter(self.freq_input.Value, 'Hz', 'frequency')
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()

			return

		self.prog.env.frequency = value

		self.freq_input.BackgroundColour = self.ok_background_color

	def OnView(self, parameter, evt=None):
		def show_frame(waveform, markers, frequency):
			view_frame = WaveformFrame(self, parameter[0])
			view_frame.SetValue(waveform, markers, frequency)
			view_frame.Show()

		def show_error(error, monospace=False):
			MessageDialog(self, error, 'Waveform generation error', monospace=monospace).Show()

		def show_waveform():
			try:
				self.prog.generate_waveforms()
			except ValueError as e:
				wx.CallAfter(show_error, str(e))

				return
			except PulseError as e:
				wx.CallAfter(show_error, '\n'.join((e[0])), monospace=True)

				return

			waveform = self.prog.env.waveforms[parameter[0]]
			markers = {}
			for num in waveform.markers:
				markers[num] = waveform.get_marker(num)

			wx.CallAfter(show_frame, waveform.wave, markers, self.prog.env.frequency)

		thr = Thread(target=show_waveform)
		thr.daemon = True
		thr.start()


class PulsePanel(ParameterPanel):
	type = 'pulse'
	name = 'Pulses'
	attributes = True

	def converter(self, parameter, x):
		x = ParameterPanel.converter(self, parameter, x)

		if parameter[1] == 'amplitude':
			return quantity_converter(x, 'V', 'voltage', False)
		elif parameter[1] == 'length':
			return quantity_converter(x)
		elif parameter[1] == 'shape':
			return x


class PulseProgramPanel(wx.Panel):
	"""
	A panel to display and change all the parameters of a program.
	"""

	panel_types = {'acq_marker': AcqMarkerPanel, 'delay': DelayPanel, 'int': IntPanel,
			'output': OutputPanel, 'pulse': PulsePanel}

	def __init__(self, parent, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.prog = None

		self.parameter_panels = []

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Notebook.
		self.parameter_notebook = wx.Notebook(self)
		self.parameter_notebook.SetMinSize((600, 400))
		panel_box.Add(self.parameter_notebook, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

		self.SetSizerAndFit(panel_box)

	def create_parameter_panels(self, prog):
		types = set(prog.env.variables.values())

		for type in sorted(types):
			try:
				result = self.panel_types[type](self.parameter_notebook, prog)
			except KeyError:
				MessageDialog('Unrecognized variable type "{0}"'.format(type)).Show()

				return

			self.parameter_panels.append(result)
			self.parameter_notebook.AddPage(result, result.name)

	def OnOpen(self, prog):
		self.prog = prog

		self.create_parameter_panels(self.prog)

	def OnClose(self):
		self.prog = None

		self.parameter_notebook.DeleteAllPages()
		self.parameter_panels = []


class PulseProgramFrame(wx.Frame):
	default_title = 'Pulse program'

	def __init__(self, parent, close_callback, *args, **kwargs):
		if 'title' not in kwargs:
			kwargs['title'] = self.default_title
		else:
			self.default_title = kwargs['title']

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

		self.pulse_panel = PulseProgramPanel(self)
		frame_box.Add(self.pulse_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnMenuFileOpen(self, evt=None):
		wildcard = determine_wildcard('pulse', 'Pulse program')
		dlg = wx.FileDialog(parent=self, message='Load...', wildcard=wildcard,
				style=wx.FD_OPEN)

		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()

			try:
				prog = Program.from_file(path)
			except PulseSyntaxError as e:
				MessageDialog(self, '\n'.join(e[0]), 'Compilation error', monospace=True).Show()

				return

			# Only purge the previous file if this one has been opened successfully.
			self.OnMenuFileClose()

			self.Title = '{0} - {1}'.format(basename(path), self.default_title)

			self.pulse_panel.OnOpen(prog)

	def OnMenuFileClose(self, evt=None):
		self.Title = self.default_title

		self.pulse_panel.OnClose()

	def OnClose(self, evt):
		self.close_callback()

		evt.Skip()
