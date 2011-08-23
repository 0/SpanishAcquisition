from functools import partial
from threading import Thread
import wx
from wx.lib import filebrowsebutton
from wx.lib.scrolledpanel import ScrolledPanel

from spacq.interface.pulse.parser import PulseError, PulseSyntaxError
from spacq.interface.pulse.program import Program
from spacq.interface.resources import Resource
from spacq.interface.units import IncompatibleDimensions, Quantity

from ..display.waveform import WaveformFrame
from ..tool.box import OK_BACKGROUND_COLOR, determine_wildcard, MessageDialog


class FileBrowseButton(filebrowsebutton.FileBrowseButton):
	ChangeValue = filebrowsebutton.FileBrowseButton.SetValue

	def SetBackgroundColour(self, colour):
		self.textControl.SetBackgroundColour(colour)


def pos_int_converter(x):
	try:
		result = int(x)

		if result <= 0:
			raise ValueError()

		return result
	except ValueError:
		raise ValueError('Expected positive integer')

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
	use_resource_labels = False

	spacer_height = 15

	def extract_variables(self, prog):
		"""
		By default, extract the variables which pertain to the current type.
		"""

		return [k for k, v in prog.variables.items() if v == self.type]

	def extract_parameters(self, prog):
		"""
		By default, extract the parameters which pertain to the current type.
		"""

		variables = self.extract_variables(prog)

		return sorted([item for item in prog.all_values for variable in variables if item[0] == variable])

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

		# Also resource label input field.
		if self.use_resource_labels:
			cols += 1

		return cols

	@property
	def input_col(self):
		"""
		The 0-based position of the growable input column.
		"""

		if self.use_resource_labels:
			# Second-to-last column.
			return self.num_cols - 2
		else:
			# Last column.
			return self.num_cols - 1

	def get_value(self, parameter):
		"""
		Get the value of a parameter as a string, or raise KeyError if not available.
		"""

		return str(self.values[parameter])

	def get_resource_label(self, parameter):
		"""
		Get the resource label for a parameter, or empty string if not available.
		"""

		try:
			return self.resource_labels[parameter]
		except KeyError:
			return ''

	@property
	def posn(self):
		return (self.cur_row, self.cur_col)

	def add_headings(self):
		"""
		Add column headings.
		"""

		if self.use_resource_labels:
			# Default value.
			self.parameter_sizer.Add(wx.StaticText(self, label='Default value'), (self.cur_row, self.input_col),
					flag=wx.EXPAND)

			# Resource label.
			self.parameter_sizer.Add(wx.StaticText(self, label='Resource label'), (self.cur_row, self.input_col + 1),
					flag=wx.EXPAND)
		else:
			self.parameter_sizer.Add(wx.StaticText(self, label=''), (self.cur_row, 0),
					flag=wx.EXPAND)

		self.cur_row += 1

	def add_resource_label(self, parameter):
		"""
		Add a resource label input.
		"""

		resource_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.Bind(wx.EVT_TEXT, partial(self.OnResourceChange, parameter), resource_input)
		self.Bind(wx.EVT_TEXT_ENTER, partial(self.OnResourceInput, parameter), resource_input)

		self.parameter_sizer.Add(resource_input, self.posn, flag=wx.EXPAND)
		self.cur_col += 1

		label = self.get_resource_label(parameter)
		resource_input.ChangeValue(label)
		resource_input.default_background_color = resource_input.BackgroundColour
		if label:
			resource_input.BackgroundColour = OK_BACKGROUND_COLOR

	def add_row(self, parameter, input_type='text', increment_row=True):
		"""
		Add a parameter to the sizer and display the value if it is available.
		"""

		self.cur_col = 0

		if not self.hide_variables:
			if self.last_variable == parameter[0]:
				label = ''
			else:
				label = parameter[0]
				self.last_variable = parameter[0]

			self.parameter_sizer.Add(wx.StaticText(self, label=label), self.posn,
					flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			self.cur_col += 1

		if self.attributes:
			self.parameter_sizer.Add(wx.StaticText(self, label=parameter[1]), self.posn,
					flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
			self.cur_col += 1

		if input_type == 'text':
			input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)

			self.Bind(wx.EVT_TEXT, partial(self.OnChange, parameter), input)
			self.Bind(wx.EVT_TEXT_ENTER, partial(self.OnInput, parameter), input)
		elif input_type == 'file':
			input = FileBrowseButton(self, labelText='File:', changeCallback=partial(self.OnInput, parameter))
		else:
			raise ValueError('Unrecognized type "{0}"'.format(input_type))

		self.parameter_sizer.Add(input, self.posn, flag=wx.EXPAND)
		self.cur_col += 1

		input.default_background_color = input.BackgroundColour

		try:
			input.ChangeValue(self.get_value(parameter))
		except KeyError:
			# No default value set.
			pass
		else:
			input.SetBackgroundColour(OK_BACKGROUND_COLOR)

		if self.use_resource_labels:
			self.add_resource_label(parameter)

		if increment_row:
			self.cur_row += 1

	def converter(self, parameter, x):
		"""
		Identity.
		"""

		return x

	def __init__(self, parent, global_store, prog, *args, **kwargs):
		ScrolledPanel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self.prog = prog

		self.values = prog.values
		self.resource_labels = prog.resource_labels
		self.resources = prog.resources

		self.last_variable = None
		self.cur_row, self.cur_col = 0, 0

		parameters = self.extract_parameters(prog)

		# Panel.
		self.parameter_sizer = wx.GridBagSizer(hgap=5)

		self.parameter_sizer.AddGrowableCol(self.input_col, 1)
		if self.use_resource_labels:
			self.parameter_sizer.AddGrowableCol(self.input_col + 1, 1)

		## Headings.
		self.add_headings()

		## Parameter inputs.
		for parameter in parameters:
			self.add_row(parameter)

		self.SetSizer(self.parameter_sizer)
		self.SetupScrolling()

	def set_value(self, parameter, value):
		self.values[parameter] = value

	def del_value(self, parameter):
		try:
			del self.values[parameter]
		except KeyError:
			pass

	def set_resource_label(self, parameter, value, resource):
		self.resource_labels[parameter] = value
		self.resources[parameter] = resource

	def del_resource_label(self, parameter):
		try:
			label = self.resource_labels[parameter]
		except KeyError:
			pass
		else:
			del self.resource_labels[parameter]
			del self.resources[parameter]
			del self.global_store.resources[label]

	def OnChange(self, parameter, evt):
		# Awaiting validation.
		self.del_value(parameter)

		evt.EventObject.BackgroundColour = evt.EventObject.default_background_color

	def OnInput(self, parameter, evt):
		try:
			value = self.converter(parameter, evt.String)
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()

			return

		# Validated.
		self.set_value(parameter, value)

		evt.EventObject.BackgroundColour = OK_BACKGROUND_COLOR

	def OnResourceChange(self, parameter, evt):
		# Awaiting validation.
		self.del_resource_label(parameter)

		evt.EventObject.BackgroundColour = evt.EventObject.default_background_color

	def OnResourceInput(self, parameter, evt):
		label = evt.String

		try:
			# Do nothing if there has not been a change.
			if label == self.resource_labels[parameter]:
				return
		except KeyError:
			pass

		# The actual setter is generated when the program is cloned.
		resource = Resource(setter=lambda x: None)

		try:
			self.global_store.resources[label] = resource
		except KeyError as e:
			MessageDialog(self, str(e[0]), 'Resource label conflicts').Show()

			return

		# Validated.
		self.set_resource_label(parameter, label, resource)

		evt.EventObject.BackgroundColour = OK_BACKGROUND_COLOR


class AcqMarkerPanel(ParameterPanel):
	type = 'acq_marker'
	name = 'Acquisition'
	attributes = True
	hide_variables = True

	def converter(self, parameter, x):
		x = ParameterPanel.converter(self, parameter, x)

		if parameter[1] == 'marker_num':
			return pos_int_converter(x)
		elif parameter[1] == 'output':
			try:
				if self.prog.variables[x] == 'output':
					return x
				else:
					raise KeyError()
			except KeyError:
				raise ValueError('Expected valid output name')

	def __init__(self, *args, **kwargs):
		ParameterPanel.__init__(self, *args, **kwargs)

		# Spacer.
		self.parameter_sizer.Add((-1, self.spacer_height), (self.cur_row, 0))
		self.cur_row += 1

		# Times to average.
		self.parameter_sizer.Add(wx.StaticText(self, label='Times to average'), (self.cur_row, 0),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.times_average_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.parameter_sizer.Add(self.times_average_input, (self.cur_row, 1), flag=wx.EXPAND)
		self.cur_row += 1

		self.times_average_input.Value = str(self.prog.times_average)
		self.times_average_input.default_background_color = self.times_average_input.BackgroundColour
		self.times_average_input.BackgroundColour = OK_BACKGROUND_COLOR

		self.Bind(wx.EVT_TEXT, self.OnTimesAverageChange, self.times_average_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnTimesAverageInput, self.times_average_input)

		# Post-trigger delay.
		self.parameter_sizer.Add(wx.StaticText(self, label='Post-trigger delay'), (self.cur_row, 0),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.delay_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.parameter_sizer.Add(self.delay_input, (self.cur_row, 1), flag=wx.EXPAND)
		self.cur_row += 1

		self.delay_input.Value = str(self.prog.acq_delay)
		self.delay_input.default_background_color = self.delay_input.BackgroundColour
		self.delay_input.BackgroundColour = OK_BACKGROUND_COLOR

		self.Bind(wx.EVT_TEXT, self.OnDelayChange, self.delay_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnDelayInput, self.delay_input)

	def OnTimesAverageChange(self, evt=None):
		self.times_average_input.BackgroundColour = self.times_average_input.default_background_color

	def OnTimesAverageInput(self, evt=None):
		try:
			value = pos_int_converter(self.times_average_input.Value)
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()

			return

		self.prog.times_average = value

		self.times_average_input.BackgroundColour = OK_BACKGROUND_COLOR

	def OnDelayChange(self, evt=None):
		self.delay_input.BackgroundColour = self.delay_input.default_background_color

	def OnDelayInput(self, evt=None):
		try:
			value = quantity_converter(self.delay_input.Value, 's', 'time')
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()

			return

		self.prog.acq_delay = value

		self.delay_input.BackgroundColour = OK_BACKGROUND_COLOR


class DelayPanel(ParameterPanel):
	type = 'delay'
	name = 'Delays'
	use_resource_labels = True

	def converter(self, parameter, x):
		x = ParameterPanel.converter(self, parameter, x)

		return quantity_converter(x)


class IntPanel(ParameterPanel):
	type = 'int'
	name = 'Integers'
	use_resource_labels = True

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

	def get_value(self, parameter):
		result = self.prog.output_channels[parameter[0]]

		if result is not None:
			return str(result)
		else:
			raise KeyError(parameter[0])

	def add_row(self, parameter):
		ParameterPanel.add_row(self, parameter, increment_row=False)

		view_button = wx.Button(self, label='View')
		self.parameter_sizer.Add(view_button, self.posn)
		self.cur_col += 1
		self.Bind(wx.EVT_BUTTON, partial(self.OnView, parameter), view_button)

		self.cur_row += 1

	def converter(self, parameter, x):
		if x == '':
			return x
		else:
			return pos_int_converter(x)

	def __init__(self, *args, **kwargs):
		ParameterPanel.__init__(self, *args, **kwargs)

		# Spacer.
		self.parameter_sizer.Add((-1, self.spacer_height), (self.cur_row, 0))
		self.cur_row += 1

		# Frequency input.
		self.parameter_sizer.Add(wx.StaticText(self, label='Sampling rate'), (self.cur_row, 0),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.freq_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.parameter_sizer.Add(self.freq_input, (self.cur_row, 1), flag=wx.EXPAND)
		self.cur_row += 1

		self.freq_input.Value = str(self.prog.frequency)
		self.freq_input.default_background_color = self.freq_input.BackgroundColour
		self.freq_input.BackgroundColour = OK_BACKGROUND_COLOR

		self.Bind(wx.EVT_TEXT, self.OnFrequencyChange, self.freq_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnFrequencyInput, self.freq_input)

		# Spacer.
		self.parameter_sizer.Add((-1, self.spacer_height), (self.cur_row, 0))
		self.cur_row += 1

		# AWG input.
		self.parameter_sizer.Add(wx.StaticText(self, label='AWG'), (self.cur_row, 0),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.awg_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.parameter_sizer.Add(self.awg_input, (self.cur_row, 1), flag=wx.EXPAND)
		self.cur_row += 1

		self.awg_input.Value = self.prog.awg
		self.awg_input.default_background_color = self.awg_input.BackgroundColour
		self.awg_input.BackgroundColour = OK_BACKGROUND_COLOR

		self.Bind(wx.EVT_TEXT, self.OnAWGChange, self.awg_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnAWGInput, self.awg_input)

		# Oscilloscope input.
		self.parameter_sizer.Add(wx.StaticText(self, label='Oscilloscope'), (self.cur_row, 0),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.oscilloscope_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.parameter_sizer.Add(self.oscilloscope_input, (self.cur_row, 1), flag=wx.EXPAND)
		self.cur_row += 1

		self.oscilloscope_input.Value = self.prog.oscilloscope
		self.oscilloscope_input.default_background_color = self.oscilloscope_input.BackgroundColour
		self.oscilloscope_input.BackgroundColour = OK_BACKGROUND_COLOR

		self.Bind(wx.EVT_TEXT, self.OnOscilloscopeChange, self.oscilloscope_input)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnOscilloscopeInput, self.oscilloscope_input)

	def set_value(self, parameter, value):
		if value == '':
			value = None

		self.prog.output_channels[parameter[0]] = value

	def OnFrequencyChange(self, evt=None):
		self.freq_input.BackgroundColour = self.freq_input.default_background_color

	def OnFrequencyInput(self, evt=None):
		try:
			value = quantity_converter(self.freq_input.Value, 'Hz', 'frequency')
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()

			return

		self.prog.frequency = value

		self.freq_input.BackgroundColour = OK_BACKGROUND_COLOR

	def OnAWGChange(self, evt=None):
		self.awg_input.BackgroundColour = self.awg_input.default_background_color

	def OnAWGInput(self, evt=None):
		self.prog.awg = self.awg_input.Value

		self.awg_input.BackgroundColour = OK_BACKGROUND_COLOR

	def OnOscilloscopeChange(self, evt=None):
		self.oscilloscope_input.BackgroundColour = self.oscilloscope_input.default_background_color

	def OnOscilloscopeInput(self, evt=None):
		self.prog.oscilloscope = self.oscilloscope_input.Value

		self.oscilloscope_input.BackgroundColour = OK_BACKGROUND_COLOR

	def OnView(self, parameter, evt=None):
		def show_frame(waveform, markers, frequency):
			view_frame = WaveformFrame(self, parameter[0])
			view_frame.SetValue(waveform, markers, frequency)
			view_frame.Show()

		def show_error(error, monospace=False):
			MessageDialog(self, error, 'Waveform generation error', monospace=monospace).Show()

		def show_waveform():
			try:
				waveforms = self.prog.generate_waveforms()
			except ValueError as e:
				wx.CallAfter(show_error, str(e))

				return
			except PulseError as e:
				wx.CallAfter(show_error, '\n'.join((e[0])), monospace=True)

				return

			waveform, markers = waveforms[parameter[0]]

			wx.CallAfter(show_frame, waveform, markers, self.prog.frequency)

		thr = Thread(target=show_waveform)
		thr.daemon = True
		thr.start()


class PulsePanel(ParameterPanel):
	type = 'pulse'
	name = 'Pulses'
	attributes = True
	use_resource_labels = True

	def add_resource_label(self, parameter):
		if parameter[1] == 'shape':
			self.cur_col += 1
		else:
			ParameterPanel.add_resource_label(self, parameter)

	def add_row(self, parameter):
		kwargs = {}
		if parameter[1] == 'shape':
			kwargs['input_type'] = 'file'

		return ParameterPanel.add_row(self, parameter, **kwargs)

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

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store

		self.prog = None

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Notebook.
		self.parameter_notebook = wx.Notebook(self)
		self.parameter_notebook.SetMinSize((600, 400))
		panel_box.Add(self.parameter_notebook, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

		self.SetSizerAndFit(panel_box)

	def create_parameter_panels(self, prog):
		types = set(prog.variables.values())

		for type in sorted(types):
			try:
				result = self.panel_types[type](self.parameter_notebook, self.global_store, prog)
			except KeyError:
				MessageDialog('Unrecognized variable type "{0}"'.format(type)).Show()

				return

			self.parameter_notebook.AddPage(result, result.name)

	def OnOpen(self, prog):
		self.prog = prog

		self.create_parameter_panels(self.prog)

	def OnClose(self):
		self.prog = None

		self.parameter_notebook.DeleteAllPages()


class PulseProgramFrame(wx.Frame):
	default_title = 'Pulse program'

	def __init__(self, parent, global_store, close_callback, *args, **kwargs):
		if 'title' not in kwargs:
			kwargs['title'] = self.default_title
		else:
			self.default_title = kwargs['title']

		wx.Frame.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
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

		self.pulse_panel = PulseProgramPanel(self, self.global_store)
		frame_box.Add(self.pulse_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Reload existing program.
		if self.global_store.pulse_program is not None:
			self.load_program(self.global_store.pulse_program)

	def load_program(self, prog):
			self.Title = '{0} - {1}'.format(prog.filename, self.default_title)

			self.pulse_panel.OnOpen(prog)

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

			self.load_program(prog)

			self.global_store.pulse_program = prog

	def OnMenuFileClose(self, evt=None):
		if self.global_store.pulse_program is None:
			return

		self.pulse_panel.OnClose()

		self.Title = self.default_title

		for label in self.global_store.pulse_program.resource_labels.values():
			del self.global_store.resources[label]

		self.global_store.pulse_program = None

	def OnClose(self, evt):
		self.close_callback()

		evt.Skip()
