import logging
log = logging.getLogger(__name__)

import csv
from datetime import timedelta
from functools import partial
from itertools import izip
import os
from pubsub import pub
from threading import Lock, Thread
import time
import wx
from wx.lib.filebrowsebutton import DirBrowseButton

from spacq.iteration.variables import sort_variables, InputVariable, OutputVariable
from spacq.tool.box import flatten, sift, Enum

from ..tool.box import Dialog, MessageDialog, YesNoQuestionDialog


class DataCaptureDialog(Dialog):
	"""
	A progress dialog which runs over an iterator, sets the corresponding resources, and captures the measured data.
	"""

	modes = Enum(['init', 'next', 'transition', 'write', 'dwell', 'read', 'stall', 'ramp_down', 'end'])

	timer_delay = 50 # ms
	stall_time = 2 # s

	def __init__(self, parent, resources, variables, num_items, measurement_resources,
			measurement_variables, continuous=False, *args, **kwargs):
		kwargs['style'] = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER

		Dialog.__init__(self, parent, title='Sweeping...', *args, **kwargs)

		self.parent = parent
		self.resources = resources
		self.variables = variables
		self.num_items = num_items
		self.measurement_resources = measurement_resources
		self.measurement_variables = measurement_variables
		self.continuous = continuous

		# Only show elapsed time in continuous mode.
		self.show_remaining_time = not self.continuous

		# The callbacks should be set before calling start(), if necessary.
		self.data_callback = None
		self.close_callback = None

		self.last_checked_time = -1
		self.elapsed_time = 0 # us

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

		# Map the modes to methods.
		self.mode_actions = dict((mode, getattr(self, mode)) for mode in self.modes)

		self.cancelling = False
		self.done = False

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

		# Try to cancel cleanly instead of giving up.
		self.Bind(wx.EVT_CLOSE, self.OnCancel)

	def create_iterator(self, pos):
		"""
		Create an iterator for an order of variables.
		"""

		return izip(*(var.iterator for var in self.variables[pos]))

	@property
	def in_mode(self):
		"""
		Are we currently executing a mode?
		"""

		return self.mode_thread is not None and self.mode_thread.is_alive()

	@property
	def mode(self):
		"""
		The current mode.
		"""

		return self._mode

	@mode.setter
	def mode(self, value):
		"""
		Note: Does not check that the current thread has stopped.
		"""

		self._mode = value

		self.mode_thread = Thread(target=self.mode_actions[self._mode])
		self.mode_thread.daemon = True
		self.mode_thread.start()

	def start(self):
		"""
		Begin the sweep.
		"""

		self.mode = self.modes.init

		self.timer.Start(self.timer_delay)

	def resource_exception_handler(self, resource_name, e, write=True):
		"""
		Called when a write to or read from a Resource raises e.
		"""

		msg = 'Resource: {0}\nError: {1}'.format(resource_name, str(e))
		dir = 'to' if write else 'from'
		MessageDialog(self.parent, msg, 'Error writing {0} resource'.format(dir)).Show()

		self.abort(fatal=write)

	def ramp(self, resources, values_from, values_to, steps):
		"""
		Slowly sweep the resources.
		"""

		thrs = []
		for (name, resource), value_from, value_to, resource_steps in zip(resources,
				values_from, values_to, steps):
			if resource is None:
				continue

			thr = Thread(target=resource.sweep, args=(value_from, value_to, resource_steps),
					kwargs={'exception_callback': partial(wx.CallAfter, self.resource_exception_handler, name)})
			thrs.append(thr)
			thr.daemon = True
			thr.start()

		for thr in thrs:
			thr.join()

	def write_resource(self, name, resource, value, output):
		"""
		Write a value to a resource and handle exceptions.
		"""

		try:
			resource.value = value
		except Exception as e:
			wx.CallAfter(self.resource_exception_handler, name, e)
			return

	def read_resource(self, name, resource, input, save_callback):
		"""
		Read a value from a resource and handle exceptions.
		"""

		try:
			value = resource.value
		except Exception as e:
			wx.CallAfter(self.resource_exception_handler, name, e, write=False)
			return

		save_callback(value)

	def init(self):
		"""
		Initialize values.
		"""

		self.iterators = None
		self.current_values = None
		self.last_values = None

		self.item = -1

		self.sweep_start_time = time.time()

	def next(self):
		"""
		Get the next set of values from the iterators.
		"""

		self.item += 1
		if self.current_values is not None:
			self.last_values = self.current_values[:]

		if self.iterators is None:
			# First time around.
			self.iterators = []
			for pos in xrange(len(self.variables)):
				self.iterators.append(self.create_iterator(pos))

			self.current_values = [it.next() for it in self.iterators]
			self.changed_indices = range(len(self.variables))
		else:
			pos = len(self.variables) - 1
			while pos >= 0:
				try:
					self.current_values[pos] = self.iterators[pos].next()
					break
				except StopIteration:
					self.iterators[pos] = self.create_iterator(pos)
					self.current_values[pos] = self.iterators[pos].next()

					pos -= 1

			self.changed_indices = range(pos, len(self.variables))

	def transition(self):
		"""
		Perform a transition for variables, as required.
		"""

		if self.last_values is None:
			# Smooth set from const.
			steps, resources, from_values, to_values = [], [], [], []

			for pos in xrange(len(self.variables)):
				# Extract values for this group.
				group_vars, group_resources, current_values = (self.variables[pos],
						self.resources[pos], self.current_values[pos])

				for var, resource, current_value in zip(group_vars, group_resources,
						current_values):
					if var.use_const or not var.smooth_from:
						continue

					steps.append(var.smooth_steps)
					resources.append(resource)
					from_values.append(var.const)
					to_values.append(current_value)

			self.ramp(resources, from_values, to_values, steps)
		else:
			# The first changed group is simply stepping; all others rolled over.
			affected_groups = self.changed_indices[1:]

			steps, resources, from_values, to_values = [], [], [], []

			for pos in affected_groups:
				# Extract values for this group.
				group_vars, group_resources, current_values, last_values = (self.variables[pos],
						self.resources[pos], self.current_values[pos], self.last_values[pos])

				for var, resource, current_value, last_value in zip(group_vars, group_resources,
						current_values, last_values):
					if var.use_const or not var.smooth_transition:
						continue

					steps.append(var.smooth_steps)
					resources.append(resource)
					from_values.append(last_value)
					to_values.append(current_value)

			self.ramp(resources, from_values, to_values, steps)

	def write(self):
		"""
		Write the next values to their resources.
		"""

		thrs = []
		for pos in self.changed_indices:
			for i, ((name, resource), value, output) in enumerate(zip(self.resources[pos],
					self.current_values[pos], self.value_outputs[pos])):

				if resource is not None:
					thr = Thread(target=self.write_resource, args=(name, resource, value, output))
					thrs.append(thr)
					thr.daemon = True
					thr.start()

				output.Value = str(value)

		for thr in thrs:
			thr.join()

	def dwell(self):
		"""
		Wait for all changed variables.
		"""

		delay = max(var._wait.value for pos in self.changed_indices for var in self.variables[pos])

		time.sleep(delay)

	def read(self):
		"""
		Take measurements.
		"""

		measurements = [None] * len(self.measurement_resources)

		thrs = []
		for i, ((name, resource), input) in enumerate(zip(self.measurement_resources, self.value_inputs)):
			if resource is not None:
				def save_callback(value, i=i, input=input):
					measurements[i] = value
					wx.CallAfter(input.SetValue, str(value))

				thr = Thread(target=self.read_resource, args=(name, resource, input, save_callback))
				thrs.append(thr)
				thr.daemon = True
				thr.start()

		for thr in thrs:
			thr.join()

		if self.data_callback is not None:
			self.data_callback([time.time()] + list(flatten(self.current_values)), measurements)

	def stall(self):
		"""
		In case the sweep is too fast, ensure that the user has some time to see the capture dialog.
		"""

		span = time.time() - self.sweep_start_time

		if span < self.stall_time:
			time.sleep(self.stall_time - span)

	def ramp_down(self):
		"""
		Sweep from the last values to const.
		"""

		if not self.current_values:
			return

		# Smooth set to const.
		steps, resources, from_values, to_values = [], [], [], []

		for pos in xrange(len(self.variables)):
			# Extract values for this group.
			group_vars, group_resources, current_values = (self.variables[pos],
					self.resources[pos], self.current_values[pos])

			for var, resource, current_value in zip(group_vars, group_resources,
					current_values):
				if var.use_const or not var.smooth_to:
					continue

				steps.append(var.smooth_steps)
				resources.append(resource)
				from_values.append(current_value)
				to_values.append(var.const)

		self.ramp(resources, from_values, to_values, steps)

	def end(self):
		"""
		The sweep is over.
		"""

		if self.done:
			return

		self.done = True

		if self.close_callback is not None:
			self.close_callback(self)

		wx.CallAfter(self.timer.Stop)
		wx.CallAfter(self.Destroy)

	def abort(self, fatal=False):
		"""
		Ending abruptly for any reason.
		"""

		if not fatal:
			self.continuous = False
			self.mode = self.modes.ramp_down
		else:
			self.mode = self.modes.end

	def OnCancel(self, evt=None):
		if not self.cancel_button.Enabled:
			return

		self.cancel_button.Disable()
		self.cancelling = True

	def OnTimer(self, evt=None):
		log.debug('On timer, mode {0} is {1}active'.format(self.mode, '' if self.in_mode else 'in'))

		# Update progress.
		if self.num_items > 0 and self.item >= 0:
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

		# Prompt to abort.
		if self.cancelling:
			def abort():
				self.cancelling = False
				self.abort()

				self.timer.Start(self.timer_delay)

			def resume():
				self.cancelling = False
				self.cancel_button.Enable()

				self.timer.Start(self.timer_delay)

			self.last_checked_time = -1
			self.timer.Stop()

			YesNoQuestionDialog(self, 'Abort processing?', abort, resume).Show()

			return

		# Switch to the next mode:
		#
		# init -> next -> transition -> write -> dwell -> read -> stall -> ramp_down -> end
		#   ^      ^________________________________________|                  |
		#   |__________________________________________________________________|
		if not self.in_mode:
			if self.mode == self.modes.init:
				self.mode = self.modes.next
			elif self.mode == self.modes.next:
				self.mode = self.modes.transition
			elif self.mode == self.modes.transition:
				self.mode = self.modes.write
			elif self.mode == self.modes.write:
				self.mode = self.modes.dwell
			elif self.mode == self.modes.dwell:
				self.mode = self.modes.read
			elif self.mode == self.modes.read:
				if self.item == self.num_items - 1:
					self.item += 1

					self.mode = self.modes.stall
				else:
					self.mode = self.modes.next
			elif self.mode == self.modes.stall:
				self.mode = self.modes.ramp_down
			elif self.mode == self.modes.ramp_down:
				if self.continuous:
					self.mode = self.modes.init
				else:
					self.mode = self.modes.end
			else:
				raise ValueError(self.mode)


class DataCapturePanel(wx.Panel):
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
			time.sleep(1)
			wx.CallAfter(self.start_button.Enable)
		thr = Thread(target=enable_button)
		thr.daemon = True
		thr.start()

		all_variables = [var for var in self.global_store.variables.values() if var.enabled]
		output_variables = sift(all_variables, OutputVariable)
		input_variables = [var for var in sift(all_variables, InputVariable) if var.resource_name != '']

		if not output_variables:
			MessageDialog(self, 'No output variables defined', 'No variables').Show()
			return

		output_variables, num_items = sort_variables(output_variables)

		resource_names = [tuple(var.resource_name for var in group) for group in output_variables]
		measurement_resource_names = [var.resource_name for var in input_variables]

		continuous = self.continuous_checkbox.Value

		missing_resources = []
		unreadable_resources = []
		unwritable_resources = []

		resources = []
		for group in resource_names:
			group_resources = []

			for name in group:
				if name == '':
					group_resources.append((str(len(resources)), None))
				elif name not in self.global_store.resources:
					missing_resources.append(name)
				else:
					resource = self.global_store.resources[name]

					if resource.writable:
						group_resources.append((name, resource))
					else:
						unwritable_resources.append(name)

			resources.append(tuple(group_resources))

		measurement_resources = []
		for name in measurement_resource_names:
			if name not in self.global_store.resources:
				missing_resources.append(name)
			else:
				resource = self.global_store.resources[name]

				if resource.readable:
					measurement_resources.append((name, resource))
				else:
					unreadable_resources.append(name)

		if missing_resources:
			MessageDialog(self, ', '.join(missing_resources), 'Missing resources').Show()
		if unreadable_resources:
			MessageDialog(self, ', '.join(unreadable_resources), 'Unreadable resources').Show()
		if unwritable_resources:
			MessageDialog(self, ', '.join(unwritable_resources), 'Unwritable resources').Show()
		if missing_resources or unreadable_resources or unwritable_resources:
			return

		exporting = False
		if self.export_enabled.Value:
			dir = self.directory_browse_button.GetValue()
			# YYYY-MM-DD_HH-MM-SS.csv
			name = '{0:04}-{1:02}-{2:02}_{3:02}-{4:02}-{5:02}.csv'.format(*time.localtime())

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
			export_csv.writerow(['__time__'] + [var.name for var in flatten(output_variables)] +
					[var.name for var in input_variables])

		self.capture_dialogs += 1

		dlg = DataCaptureDialog(self, resources, output_variables, num_items, measurement_resources,
				input_variables, continuous)

		for name in measurement_resource_names:
			pub.sendMessage('data_capture.start', name=name)

		# Export buffer.
		max_buf_size = 10
		buf = []
		buf_lock = Lock()

		def flush():
			export_csv.writerows(buf)
			export_file.flush()

			while buf:
				buf.pop()

		def data_callback(values, measurement_values):
			for name, value in zip(measurement_resource_names, measurement_values):
				pub.sendMessage('data_capture.data', name=name, value=value)

			if exporting:
				with buf_lock:
					buf.append(values + measurement_values)

					if len(buf) >= max_buf_size:
						flush()

		def close_callback(dlg):
			self.capture_dialogs -= 1

			if exporting:
				with buf_lock:
					flush()
					export_file.close()

			for name in measurement_resource_names:
				pub.sendMessage('data_capture.stop', name=name)

		dlg.data_callback = data_callback
		dlg.close_callback = close_callback
		dlg.Show()
		dlg.start()
