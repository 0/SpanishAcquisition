import csv
from datetime import timedelta
import itertools
# FIXME: Python 2.7 provides collections.OrderedDict()
from ordereddict import OrderedDict
import os
from pubsub import pub
from threading import Lock
import time
import wx
from wx.lib.filebrowsebutton import DirBrowseButton

from spacq.iteration.variables import combine_variables, InputVariable, OutputVariable
from spacq.tool.box import sift

from ..tool.box import Dialog, ErrorMessageDialog, YesNoQuestionDialog


class DataCaptureDialog(Dialog):
	"""
	A progress dialog which runs over an iterator, sets the corresponding resources, and captures the measured data.
	"""

	def __init__(self, parent, resources, variables, iterator, last_values, num_items,
			measurement_resources, measurement_variables, continuous=False, *args, **kwargs):
		if 'style' in kwargs:
			kwargs['style'] |= wx.RESIZE_BORDER
		else:
			kwargs['style'] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER

		Dialog.__init__(self, parent, title='Sweeping...', *args, **kwargs)

		self.parent = parent
		self.resources = resources
		self.variables = variables
		self.iterator = iter(iterator)
		self.last_values = last_values
		self.num_items = num_items
		self.measurement_resources = measurement_resources
		self.measurement_variables = measurement_variables
		self.continuous = continuous

		# Only show elapsed time in continuous mode.
		self.show_remaining_time = not self.continuous

		# These should be set before calling "start", if necessary.
		self.data_callback = None
		self.close_callback = None

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

		## Values.
		self.values_box = wx.FlexGridSizer(rows=len(self.variables), cols=2, hgap=20)
		self.values_box.AddGrowableCol(1, 1)
		dialog_box.Add(self.values_box, flag=wx.EXPAND|wx.ALL, border=5)

		self.value_outputs = []
		for var in self.variables:
			output = wx.TextCtrl(self, style=wx.TE_READONLY)
			output.BackgroundColour = wx.LIGHT_GREY
			self.value_outputs.append(output)

			self.values_box.Add(wx.StaticText(self, label=var.name),
					flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			self.values_box.Add(output, flag=wx.EXPAND)

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

		## End button.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER)

		self.cancel_button = wx.Button(self, label='Cancel')
		self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancel_button)
		button_box.Add(self.cancel_button)

		self.SetSizerAndFit(dialog_box)

		# Iteration steps.
		self.old_values = ()
		self.item = 0
		self.sleep_until = 0

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

		# Elapsed time.
		self.last_checked_time = -1
		self.elapsed_time = 0 # us

		# Termination flags.
		self.done = False
		self.cancelling = False

	def start(self):
		"""
		Begin the sweep.
		"""

		self.timer.Start(0, oneShot=True)

	def changed_indices(self, old, new):
		"""
		Find the indices of the values which differ in their change indicators.
		"""

		# Extract the change indicators.
		old, new = old[1::2], new[1::2]

		for i, (o, n) in enumerate(itertools.izip_longest(old, new)):
			if o != n:
				return range(i, max(len(old), len(new)))

	def next_values(self, values):
		"""
		Make use of the next set of values.
		"""

		self.item += 1
		if self.continuous and self.item > self.num_items:
			# Loop around to the start.
			self.item = 1

			# Invalidate all the change indicators.
			self.old_values = tuple(x if i % 2 == 0 else -1 for i, x in enumerate(self.old_values))

		changed = self.changed_indices(self.old_values, values)

		for i, ((name, resource), output, value) in enumerate(zip(self.resources.items(),
				self.value_outputs, values[::2])):
			# Only set resources for updated values.
			if (i not in changed or
					(len(self.old_values) > 2 * i and self.old_values[2 * i] == value)):
				continue

			if resource is not None:
				try:
					resource.value = value
				except Exception as e:
					msg = 'Resource: {0}\nError: {1}'.format(name, str(e))
					ErrorMessageDialog(self.parent, msg, 'Error writing to resource').Show()

					wx.CallAfter(self.end, fatal=True)
					return False

			output.Value = str(value)

		self.old_values = values

		# Determine the dwell time.
		if changed:
			delay = max(self.variables[i]._wait.value for i in changed)
		else:
			delay = 0

		self.sleep_until = time.time() + delay

		return True

	def end(self, fatal=False):
		"""
		Ending for any reason.
		"""

		self.done = True

		if not fatal:
			# Skip to the end.
			self.next_values(self.last_values)

		if self.close_callback is not None:
			self.close_callback(self)

		self.Destroy()

	def OnCancel(self, evt=None):
		self.cancel_button.Disable()

		self.cancelling = True

	def OnTimer(self, evt=None):
		# Determine progress.
		if self.num_items > 0:
			amount_done = float(self.item) / self.num_items

			self.progress_bar.Value = self.item
			self.progress_percent.Label = '{0}%'.format(int(100 * amount_done))

			if self.last_checked_time > 0:
				self.elapsed_time += int((time.time() - self.last_checked_time) * 1e6)
				self.elapsed_time_output.Label = str(timedelta(seconds=self.elapsed_time//1e6))

			self.last_checked_time = time.time()

			if self.show_remaining_time and amount_done > 0:
				total_time = self.elapsed_time / amount_done
				remaining_time = int(total_time - self.elapsed_time)
				self.remaining_time_output.Label = str(timedelta(seconds=remaining_time//1e6))

		# Prompt to cancel.
		if self.cancelling:
			def resume():
				self.cancelling = False
				self.cancel_button.Enable()

				self.timer.Start(0, oneShot=True)

			YesNoQuestionDialog(self, 'Abort processing?', self.end, resume).Show()
			self.last_checked_time = -1
			return

		# Is dwell period over?
		if time.time() >= self.sleep_until:
			if self.old_values:
				current_values = []
				# Some values have already been set, so their dwell period has expired; we can measure.
				for (name, resource), input in zip(self.measurement_resources.items(), self.value_inputs):
					if resource is not None:
						try:
							value = resource.value
						except Exception as e:
							msg = 'Resource: {0}\nError: {1}'.format(name, str(e))
							ErrorMessageDialog(self.parent, msg, 'Error reading from resource').Show()

							wx.CallAfter(self.end)
							return

						current_values.append(value)
						input.Value = str(value)

				if self.data_callback is not None:
					# Ignoring all the change markers.
					real_values = list(self.old_values[::2])

					self.data_callback([time.time()] + real_values, current_values)

			# Get the next set of values.
			try:
				values = self.iterator.next()
			except StopIteration:
				# At this point, we are almost done.
				self.end()

				return

			if not self.next_values(values):
				# Bailing out.
				return

		delay = self.sleep_until - time.time()

		if delay > 0.2:
			# Avoid blocking for over 200 ms.
			delay = 0.2
		elif delay < 0.01:
			# But wait at least 5 ms.
			delay = 0.005

		if not self.done:
			self.timer.Start(delay * 1000, oneShot=True)


class DataCapturePanel(wx.Panel):
	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store

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
		all_variables = [var for var in self.global_store.variables.values() if var.enabled]
		output_variables = sift(all_variables, OutputVariable)
		input_variables = [var for var in sift(all_variables, InputVariable) if var.resource_name != '']

		if not output_variables:
			ErrorMessageDialog(self, 'No output variables defined', 'No variables').Show()
			return

		iterator, last, num_items, output_variables = combine_variables(output_variables)
		resource_names = [var.resource_name for var in output_variables]
		measurement_resource_names = [var.resource_name for var in input_variables]

		continuous = self.continuous_checkbox.Value
		if continuous:
			# Cycle forever.
			iterator = itertools.cycle(iterator)

		missing_resources = []
		unreadable_resources = []
		unwritable_resources = []

		resources = OrderedDict()
		for name in resource_names:
			if name == '':
				# Make a placeholder.
				num = 0
				while num in resources:
					num += 1
				resources[num] = None
			elif name not in self.global_store.resources:
				missing_resources.append(name)
			else:
				resource = self.global_store.resources[name]

				if resource.writable:
					resources[name] = resource
				else:
					unwritable_resources.append(name)

		measurement_resources = OrderedDict()
		for name in measurement_resource_names:
			if name not in self.global_store.resources:
				missing_resources.append(name)
			else:
				resource = self.global_store.resources[name]

				if resource.readable:
					measurement_resources[name] = resource
				else:
					unreadable_resources.append(name)

		if missing_resources:
			ErrorMessageDialog(self, ', '.join(missing_resources), 'Missing resources').Show()
		if unreadable_resources:
			ErrorMessageDialog(self, ', '.join(unreadable_resources), 'Unreadable resources').Show()
		if unwritable_resources:
			ErrorMessageDialog(self, ', '.join(unwritable_resources), 'Unwritable resources').Show()
		if missing_resources or unreadable_resources or unwritable_resources:
			return

		exporting = False
		if self.export_enabled.Value:
			dir = self.directory_browse_button.GetValue()
			# YYYY-MM-DD_HH-MM-SS.csv
			name = '{0:04}-{1:02}-{2:02}_{3:02}-{4:02}-{5:02}.csv'.format(*time.localtime())

			if not dir:
				ErrorMessageDialog(self, 'No directory selected.', 'Export path').Show()
				return

			if not os.path.isdir(dir):
				ErrorMessageDialog(self, 'Invalid directory selected', 'Export path').Show()
				return

			file_path = os.path.join(dir, name)
			if os.path.exists(file_path):
				ErrorMessageDialog(self, file_path, 'File exists').Show()
				return

			# Everything looks alright, so open the file.
			export_file = open(file_path, 'w')
			export_csv = csv.writer(export_file)
			exporting = True

			# Show the path in the GUI.
			self.last_file_name.Value = file_path

			# Write the header.
			export_csv.writerow(['__time__'] + [var.name for var in output_variables] +
					[var.name for var in input_variables])

		dlg = DataCaptureDialog(self, resources, output_variables, iterator, last, num_items,
				measurement_resources, input_variables, continuous)

		for name in measurement_resource_names:
			pub.sendMessage('data_capture.start', name=name)

		# Export buffer.
		max_buf_size = 10
		buf = []
		buf_lock = Lock()

		def data_callback(values, measurement_values):
			for name, value in zip(measurement_resource_names, measurement_values):
				pub.sendMessage('data_capture.data', name=name, value=value)

			if exporting:
				with buf_lock:
					buf.append(values + measurement_values)

					if len(buf) >= max_buf_size:
						export_csv.writerows(buf)
						export_file.flush()

						while buf:
							buf.pop()

		def close_callback(dlg):
			if exporting:
				with buf_lock:
					export_csv.writerows(buf)
					export_file.close()

			for name in measurement_resource_names:
				pub.sendMessage('data_capture.stop', name=name)

		dlg.data_callback = data_callback
		dlg.close_callback = close_callback
		dlg.Show()
		dlg.start()
