import csv
from datetime import timedelta
from functools import partial
import os
from pubsub import pub
from threading import Lock, Thread
from time import localtime, sleep, time
import wx
from wx.lib.filebrowsebutton import DirBrowseButton

from spacq.interface.pulse.parser import PulseError
from spacq.iteration.sweep import PulseConfiguration, SweepController
from spacq.iteration.variables import sort_variables, InputVariable, OutputVariable
from spacq.tool.box import flatten, sift

from ..tool.box import Dialog, MessageDialog, YesNoQuestionDialog


class DataCaptureDialog(Dialog, SweepController):
	"""
	A progress dialog which runs over iterators, sets the corresponding resources, and captures the measured data.
	"""

	max_value_len = 50 # characters

	timer_delay = 50 # ms
	stall_time = 2 # s

	status_messages = {
		None: 'Starting up',
		'init': 'Initializing',
		'next': 'Getting next values',
		'transition': 'Smooth setting',
		'write': 'Writing to devices',
		'dwell': 'Waiting for resources to settle',
		'pulse': 'Running pulse program',
		'read': 'Taking measurements',
		'ramp_down': 'Smooth setting',
		'end': 'Finishing',
	}

	def __init__(self, parent, resources, variables, num_items, measurement_resources,
			measurement_variables, pulse_config, continuous=False,
			*args, **kwargs):
		kwargs['style'] = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER

		Dialog.__init__(self, parent, title='Sweeping...', *args, **kwargs)
		SweepController.__init__(self, resources, variables, num_items, measurement_resources,
				measurement_variables, pulse_config, continuous=continuous)

		self.parent = parent

		# Show only elapsed time in continuous mode.
		self.show_remaining_time = not self.continuous

		self.last_checked_time = -1
		self.elapsed_time = 0 # us

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

		self.cancelling = False

		def write_callback(pos, i, value):
			self.value_outputs[pos][i].Value = str(value)[:self.max_value_len]
		self.write_callback = partial(wx.CallAfter, write_callback)

		def read_callback(i, value):
			self.value_inputs[i].Value = str(value)[:self.max_value_len]
		self.read_callback = partial(wx.CallAfter, read_callback)

		self.general_exception_handler = partial(wx.CallAfter, self._general_exception_handler)
		self.resource_exception_handler = partial(wx.CallAfter, self._resource_exception_handler)

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Progress.
		progress_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(progress_box, flag=wx.EXPAND|wx.ALL, border=5)

		### Message.
		self.progress_percent = wx.StaticText(self, label='', size=(40, -1))
		progress_box.Add(self.progress_percent,
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)

		### Bar.
		self.progress_bar = wx.Gauge(self, range=num_items, style=wx.GA_HORIZONTAL)
		progress_box.Add(self.progress_bar, proportion=1)

		## Status.
		self.status_message_output = wx.TextCtrl(self, style=wx.TE_READONLY)
		self.status_message_output.BackgroundColour = wx.LIGHT_GREY
		dialog_box.Add(self.status_message_output, flag=wx.EXPAND)

		## Values.
		self.values_box = wx.FlexGridSizer(rows=len(self.variables), cols=2, hgap=20)
		self.values_box.AddGrowableCol(1, 1)
		dialog_box.Add(self.values_box, flag=wx.EXPAND|wx.ALL, border=5)

		self.value_outputs = []
		for group in self.variables:
			group_outputs = []

			for var in group:
				output = wx.TextCtrl(self, style=wx.TE_READONLY)
				output.BackgroundColour = wx.LIGHT_GREY
				group_outputs.append(output)

				self.values_box.Add(wx.StaticText(self, label=var.name),
						flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
				self.values_box.Add(output, flag=wx.EXPAND)

			self.value_outputs.append(group_outputs)

			# Spacer.
			for _ in xrange(2):
				self.values_box.Add((-1, 15))

		# Separator.
		for _ in xrange(2):
			self.values_box.Add(wx.StaticLine(self), flag=wx.EXPAND|wx.ALL, border=5)

		self.value_inputs = []
		for var in self.measurement_variables:
			input = wx.TextCtrl(self, style=wx.TE_READONLY)
			input.BackgroundColour = wx.LIGHT_GREY
			self.value_inputs.append(input)

			self.values_box.Add(wx.StaticText(self, label=var.name),
					flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			self.values_box.Add(input, flag=wx.EXPAND)

		## Times.
		times_box = wx.FlexGridSizer(rows=2 if self.show_remaining_time else 1, cols=2, hgap=5)
		dialog_box.Add(times_box, proportion=1, flag=wx.CENTER|wx.ALL, border=15)

		### Elapsed.
		times_box.Add(wx.StaticText(self, label='Elapsed time:'))
		self.elapsed_time_output = wx.StaticText(self, label='---:--:--')
		times_box.Add(self.elapsed_time_output)

		### Remaining.
		if self.show_remaining_time:
			times_box.Add(wx.StaticText(self, label='Remaining time:'))
			self.remaining_time_output = wx.StaticText(self, label='---:--:--')
			times_box.Add(self.remaining_time_output)

		## Last continuous.
		if self.continuous:
			self.last_continuous_input = wx.CheckBox(self, label='Last loop of continuous sweep')
			dialog_box.Add(self.last_continuous_input, flag=wx.CENTER)

		## End button.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER)

		self.cancel_button = wx.Button(self, label='Cancel')
		self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancel_button)
		button_box.Add(self.cancel_button)

		self.SetSizerAndFit(dialog_box)

		# Try to cancel cleanly instead of giving up.
		self.Bind(wx.EVT_CLOSE, self.OnCancel)

	def _general_exception_handler(self, f, e):
		"""
		Called when a trampolined function raises e.
		"""

		MessageDialog(self.parent, '{0}'.format(str(e)), 'Sweep error in "{0}"'.format(f)).Show()

	def _resource_exception_handler(self, resource_name, e, write=True):
		"""
		Called when a write to or read from a Resource raises e.
		"""

		msg = 'Resource: {0}\nError: {1}'.format(resource_name, str(e))
		dir = 'writing to' if write else 'reading from'
		MessageDialog(self.parent, msg, 'Error {0} resource'.format(dir)).Show()

		self.abort(fatal=write)

	def start(self):
		thr = Thread(target=SweepController.run, args=(self,))
		thr.daemon = True
		thr.start()

		self.timer.Start(self.timer_delay)

	def dwell(self):
		result = SweepController.dwell(self)

		# Prevent the GUI from locking up.
		sleep(0.005)

		return result

	def end(self):
		try:
			SweepController.end(self)
		except AssertionError:
			return

		# In case the sweep is too fast, ensure that the user has some time to see the dialog.
		span = time() - self.sweep_start_time
		if span < self.stall_time:
			sleep(self.stall_time - span)

		wx.CallAfter(self.timer.Stop)
		wx.CallAfter(self.Destroy)

	def OnCancel(self, evt=None):
		if not self.cancel_button.Enabled:
			return

		self.cancel_button.Disable()
		self.cancelling = True

	def OnTimer(self, evt=None):
		self.status_message_output.Value = self.status_messages[self.current_f]
		if self.continuous:
			self.last_continuous = self.last_continuous_input.Value

		# Update progress.
		if self.num_items > 0 and self.item >= 0:
			amount_done = float(self.item) / self.num_items

			self.progress_bar.Value = self.item
			self.progress_percent.Label = '{0}%'.format(int(100 * amount_done))

			if self.last_checked_time > 0:
				self.elapsed_time += int((time() - self.last_checked_time) * 1e6)
				self.elapsed_time_output.Label = str(timedelta(seconds=self.elapsed_time//1e6))

			self.last_checked_time = time()

			if self.show_remaining_time and amount_done > 0:
				total_time = self.elapsed_time / amount_done
				remaining_time = int(total_time - self.elapsed_time)
				self.remaining_time_output.Label = str(timedelta(seconds=remaining_time//1e6))

		# Prompt to abort.
		if self.cancelling:
			def abort():
				self.cancelling = False

				thr = Thread(target=self.abort)
				thr.daemon = True
				thr.start()

				self.timer.Start(self.timer_delay)

			def resume():
				self.cancelling = False
				self.cancel_button.Enable()

				self.unpause()

				self.timer.Start(self.timer_delay)

			self.pause()

			self.last_checked_time = -1
			self.timer.Stop()

			YesNoQuestionDialog(self, 'Abort processing?', abort, resume).Show()

			return


class DataCapturePanel(wx.Panel):
	"""
	A panel to start the data capture process, optionally exporting the results to a file.
	"""

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store

		self.capture_dialogs = 0

		# Panel.
		panel_box = wx.BoxSizer(wx.HORIZONTAL)

		## Capture.
		capture_static_box = wx.StaticBox(self, label='Capture')
		capture_box = wx.StaticBoxSizer(capture_static_box, wx.VERTICAL)
		panel_box.Add(capture_box, flag=wx.CENTER|wx.ALL, border=5)

		### Start.
		self.start_button = wx.Button(self, label='Start')
		self.Bind(wx.EVT_BUTTON, self.OnBeginCapture, self.start_button)
		capture_box.Add(self.start_button, flag=wx.CENTER)

		### Continuous.
		self.continuous_checkbox = wx.CheckBox(self, label='Continuous')
		capture_box.Add(self.continuous_checkbox, flag=wx.CENTER)

		## Export.
		export_static_box = wx.StaticBox(self, label='Export')
		export_box = wx.StaticBoxSizer(export_static_box, wx.HORIZONTAL)
		panel_box.Add(export_box, proportion=1, flag=wx.CENTER|wx.ALL, border=5)

		### Enabled.
		self.export_enabled = wx.CheckBox(self, label='')
		self.export_enabled.Value = True
		export_box.Add(self.export_enabled, flag=wx.CENTER)

		### Export path.
		export_path_box = wx.BoxSizer(wx.VERTICAL)
		export_box.Add(export_path_box, proportion=1, flag=wx.CENTER)

		#### Directory.
		self.directory_browse_button = DirBrowseButton(self, labelText='Directory:')
		export_path_box.Add(self.directory_browse_button, flag=wx.EXPAND)

		#### Last file.
		last_file_box = wx.BoxSizer(wx.HORIZONTAL)
		export_path_box.Add(last_file_box, flag=wx.EXPAND)

		last_file_box.Add(wx.StaticText(self, label='Last output: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.last_file_name = wx.TextCtrl(self, style=wx.TE_READONLY)
		self.last_file_name.BackgroundColour = wx.LIGHT_GREY
		last_file_box.Add(self.last_file_name, proportion=1)

		self.SetSizer(panel_box)

	def OnBeginCapture(self, evt=None):
		# Prevent accidental double-clicking.
		self.start_button.Disable()
		def enable_button():
			sleep(1)
			wx.CallAfter(self.start_button.Enable)
		thr = Thread(target=enable_button)
		thr.daemon = True
		thr.start()

		all_variables = [var for var in self.global_store.variables.values() if var.enabled]
		output_variables = sift(all_variables, OutputVariable)
		input_variables = [var for var in sift(all_variables, InputVariable) if var.resource_name != '']

		if not output_variables:
			output_variables.append(OutputVariable(order=0, name='<Dummy>', enabled=True))

		output_variables, num_items = sort_variables(output_variables)

		resource_names = [tuple(var.resource_name for var in group) for group in output_variables]
		measurement_resource_names = [var.resource_name for var in input_variables]

		continuous = self.continuous_checkbox.Value

		missing_resources = set()
		unreadable_resources = set()
		unwritable_resources = set()
		missing_devices = set()

		pulse_program = self.global_store.pulse_program

		if pulse_program is not None:
			pulse_program = pulse_program.with_resources

			try:
				pulse_program.generate_waveforms(dry_run=True)
			except PulseError as e:
				MessageDialog(self, '\n'.join(e[0]), 'Pulse program error', monospace=True).Show()
				return
			except Exception as e:
				MessageDialog(self, str(e), 'Pulse program error').Show()
				return

			pulse_awg, pulse_oscilloscope = None, None
			pulse_channels = {}

			try:
				pulse_awg = self.global_store.devices[pulse_program.awg].device
				if pulse_awg is None:
					raise KeyError
			except KeyError:
				missing_devices.add(pulse_program.awg)
			else:
				# Gather used channel numbers.
				pulse_channels = dict((k, v) for k, v in pulse_program.output_channels.items() if v is not None)

				actual_channels = range(1, len(pulse_awg.channels))
				invalid_channels = [k for k, v in pulse_channels.items() if v not in actual_channels]

				if invalid_channels:
					MessageDialog(self, 'Invalid channels for: {0}'.format(', '.join(invalid_channels)), 'Invalid channels').Show()
					return

			try:
				pulse_oscilloscope = self.global_store.devices[pulse_program.oscilloscope].device
				if pulse_oscilloscope is None:
					raise KeyError
			except KeyError:
				missing_devices.add(pulse_program.oscilloscope)

			try:
				pulse_config = PulseConfiguration(pulse_program, pulse_channels, pulse_awg, pulse_oscilloscope)
			except TypeError as e:
				MessageDialog(self, str(e), 'Device configuration error').Show()
				return
		else:
			pulse_config = None

		resources = []
		for group in resource_names:
			group_resources = []

			for name in group:
				if name == '':
					group_resources.append((str(len(resources)), None))
				elif name not in self.global_store.resources:
					missing_resources.add(name)
				else:
					resource = self.global_store.resources[name]

					if resource.writable:
						group_resources.append((name, resource))
					else:
						unwritable_resources.add(name)

			resources.append(tuple(group_resources))

		measurement_resources = []
		measurement_units = []
		for name in measurement_resource_names:
			if name not in self.global_store.resources:
				missing_resources.add(name)
			else:
				resource = self.global_store.resources[name]

				if resource.readable:
					measurement_resources.append((name, resource))
					measurement_units.append(resource.display_units)
				else:
					unreadable_resources.add(name)

		mismatched_resources = []
		for (res_name, resource), var in zip(flatten(resources), flatten(output_variables)):
			if resource is None:
				continue

			if resource.units is not None:
				if not (var.type == 'quantity' and
						resource.verify_dimensions(var.units, exception=False, from_string=True)):
					mismatched_resources.append((res_name, var.name))
			else:
				if var.type not in ['float', 'integer']:
					mismatched_resources.append((res_name, var.name))

		for items, msg in [
			(missing_resources, 'Missing resources'),
			(unreadable_resources, 'Unreadable resources'),
			(unwritable_resources, 'Unwritable resources'),
			(missing_devices, 'Missing devices')]:

			if items:
				MessageDialog(self, ', '.join('"{0}"'.format(x) for x in sorted(items)), msg).Show()

		if mismatched_resources:
			MessageDialog(self, ', '.join('{0}/{1}'.format(x[0], x[1]) for x in mismatched_resources),
					'Mismatched resources').Show()

		if (missing_resources or unreadable_resources or unwritable_resources or
				missing_devices or mismatched_resources):
			return

		exporting = False
		if self.export_enabled.Value:
			dir = self.directory_browse_button.GetValue()
			# YYYY-MM-DD_HH-MM-SS.csv
			name = '{0:04}-{1:02}-{2:02}_{3:02}-{4:02}-{5:02}.csv'.format(*localtime())

			if not dir:
				MessageDialog(self, 'No directory selected.', 'Export path').Show()
				return

			if not os.path.isdir(dir):
				MessageDialog(self, 'Invalid directory selected', 'Export path').Show()
				return

			file_path = os.path.join(dir, name)
			if os.path.exists(file_path):
				MessageDialog(self, file_path, 'File exists').Show()
				return

			# Everything looks alright, so open the file.
			export_file = open(file_path, 'w')
			export_csv = csv.writer(export_file)
			exporting = True

			# Show the path in the GUI.
			self.last_file_name.Value = file_path

			# Write the header.
			export_csv.writerow(['Time (s)'] +
					['{0.name} ({0.units})'.format(var) if var.units is not None else var.name
							for var in flatten(output_variables)] +
					['{0.name} ({1})'.format(var, units) if units is not None else var.name
						for var, units in zip(input_variables, measurement_units)])

		self.capture_dialogs += 1

		dlg = DataCaptureDialog(self, resources, output_variables, num_items, measurement_resources,
				input_variables, pulse_config, continuous=continuous)
		dlg.SetMinSize((500, -1))

		for name in measurement_resource_names:
			wx.CallAfter(pub.sendMessage, 'data_capture.start', name=name)

		# Export buffer.
		max_buf_size = 10
		buf = []
		buf_lock = Lock()

		def flush():
			export_csv.writerows(buf)
			export_file.flush()

			while buf:
				buf.pop()

		def data_callback(cur_time, values, measurement_values):
			for name, value in zip(measurement_resource_names, measurement_values):
				wx.CallAfter(pub.sendMessage, 'data_capture.data', name=name, value=value)

			# Extract values out of quantities, since the units have already been taken care of in the header.
			values = [x.original_value if hasattr(x, 'original_value') else x for x in values]
			measurement_values = [x.original_value if hasattr(x, 'original_value') else x for x in measurement_values]

			if exporting:
				with buf_lock:
					buf.append([cur_time] + values + measurement_values)

					if len(buf) >= max_buf_size:
						flush()

		def close_callback():
			self.capture_dialogs -= 1

			if exporting:
				with buf_lock:
					flush()
					export_file.close()

			for name in measurement_resource_names:
				wx.CallAfter(pub.sendMessage, 'data_capture.stop', name=name)

		dlg.data_callback = data_callback
		dlg.close_callback = close_callback
		dlg.Show()
		dlg.start()
