import logging
log = logging.getLogger(__name__)

from functools import partial, wraps
from itertools import izip
from threading import Condition, Thread
from time import sleep, time

from spacq.tool.box import flatten


def update_current_f(f):
	@wraps(f)
	def wrapped(self):
		self.current_f = f.__name__

		return f(self)

	return wrapped

class SweepController(object):
	"""
	A simple controller for a sweep of several variables.

	init -> next -> transition -> write -> dwell -> read -> ramp_down -> end
	^       ^__________________________________________|            |
	|_______________________________________________________________|
	"""

	def __init__(self, resources, variables, num_items, measurement_resources, measurement_variables,
			continuous=False):
		self.resources = resources
		self.variables = variables
		self.num_items = num_items
		self.measurement_resources = measurement_resources
		self.measurement_variables = measurement_variables
		self.continuous = continuous

		# The callbacks should be set before calling run(), if necessary.
		self.data_callback, self.close_callback, self.write_callback, self.read_callback = [None] * 4
		self.resource_exception_handler = None

		self.current_f = None

		self.item = -1

		self.paused = False
		self.pause_lock = Condition()

		self.last_continuous = False
		self.aborting = False
		self.done = False

	def create_iterator(self, pos):
		"""
		Create an iterator for an order of variables.
		"""

		return izip(*(var.iterator for var in self.variables[pos]))

	def ramp(self, resources, values_from, values_to, steps):
		"""
		Slowly sweep the resources.
		"""

		thrs = []
		for (name, resource), value_from, value_to, resource_steps in zip(resources,
				values_from, values_to, steps):
			if resource is None:
				continue

			kwargs = {}
			if self.resource_exception_handler is not None:
				kwargs['exception_callback'] = partial(self.resource_exception_handler, name)

			thr = Thread(target=resource.sweep, args=(value_from, value_to, resource_steps), kwargs=kwargs)
			thrs.append(thr)
			thr.daemon = True
			thr.start()

		for thr in thrs:
			thr.join()

	def write_resource(self, name, resource, value):
		"""
		Write a value to a resource and handle exceptions.
		"""

		try:
			resource.value = value
		except Exception as e:
			if self.resource_exception_handler is not None:
				self.resource_exception_handler(name, e, write=True)
			return

	def read_resource(self, name, resource, save_callback):
		"""
		Read a value from a resource and handle exceptions.
		"""

		try:
			value = resource.value
		except Exception as e:
			if self.resource_exception_handler is not None:
				self.resource_exception_handler(name, e, write=False)
			return

		save_callback(value)

	def run(self, next_f=None):
		"""
		Run the sweep.
		"""

		if next_f is None:
			next_f = self.init

		# Trampoline.
		while next_f is not None:
			f_name = next_f.__name__

			if self.aborting:
				log.debug('Aborting before function: {0}'.format(f_name))

				return

			if self.paused:
				log.debug('Paused before function: {0}'.format(f_name))

				self.pause_lock.acquire()
				self.pause_lock.wait()

			log.debug('Starting function: {0}'.format(f_name))

			try:
				next_f = next_f()
			except Exception:
				next_f = None

	@update_current_f
	def init(self):
		"""
		Initialize values.
		"""

		self.iterators = None
		self.current_values = None
		self.last_values = None

		self.item = -1

		self.sweep_start_time = time()

		return self.next

	@update_current_f
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

		return self.transition

	@update_current_f
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

		return self.write

	@update_current_f
	def write(self):
		"""
		Write the next values to their resources.
		"""

		thrs = []
		for pos in self.changed_indices:
			for i, ((name, resource), value) in enumerate(zip(self.resources[pos], self.current_values[pos])):

				if resource is not None:
					thr = Thread(target=self.write_resource, args=(name, resource, value))
					thrs.append(thr)
					thr.daemon = True
					thr.start()

				if self.write_callback is not None:
					self.write_callback(pos, i, value)

		for thr in thrs:
			thr.join()

		return self.dwell

	@update_current_f
	def dwell(self):
		"""
		Wait for all changed variables.
		"""

		delay = max(var._wait.value for pos in self.changed_indices for var in self.variables[pos])
		sleep(delay)

		return self.read

	@update_current_f
	def read(self):
		"""
		Take measurements.
		"""

		measurements = [None] * len(self.measurement_resources)

		thrs = []
		for i, (name, resource) in enumerate(self.measurement_resources):
			if resource is not None:
				def save_callback(value, i=i):
					measurements[i] = value
					if self.read_callback is not None:
						self.read_callback(i, value)

				thr = Thread(target=self.read_resource, args=(name, resource, save_callback))
				thrs.append(thr)
				thr.daemon = True
				thr.start()

		for thr in thrs:
			thr.join()

		if self.data_callback is not None:
			self.data_callback(time(), tuple(flatten(self.current_values)), tuple(measurements))

		if self.item == self.num_items - 1:
			self.item += 1

			return self.ramp_down
		else:
			return self.next

	@update_current_f
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

		if self.continuous and not self.last_continuous:
			return self.init
		else:
			return self.end

	@update_current_f
	def end(self):
		"""
		The sweep is over.
		"""

		assert not self.done
		self.done = True

		if self.close_callback is not None:
			self.close_callback()

	def abort(self, fatal=False):
		"""
		Ending abruptly for any reason.
		"""

		self.aborting = True

		if not fatal:
			self.continuous = False
			self.ramp_down()

		self.end()
