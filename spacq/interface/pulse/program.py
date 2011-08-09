from copy import copy, deepcopy
from os.path import basename, dirname

from ..units import Quantity
from .parser import Parser, PulseError, PulseSyntaxError
from .tree import Environment

"""
Pulse programs as compiled entities.
"""


class Program(object):
	"""
	A prepared, compiled pulse program.
	"""

	filename = ''

	@classmethod
	def from_string(cls, s):
		"""
		Create a program from a string.
		"""

		env = Environment()
		ast = Parser()(s)

		return Program(env, ast)

	@classmethod
	def from_file(cls, path):
		"""
		Load a program from a file.
		"""

		with open(path) as f:
			prog_lines = f.readlines()

		p = cls.from_string(''.join(prog_lines))
		p._env.cwd = dirname(path)
		p.filename = basename(path)

		return p

	def __init__(self, env, ast):
		"""
		Given a blank Environment and AST, prepare a program.
		"""

		self._env = env
		self._ast = ast

		for stage in self._env.prep_stages:
			self._env.stage = stage
			self._env.traverse_tree(self._ast)

			if self._env.errors:
				raise PulseSyntaxError(self._env.format_errors())

		# Output channel numbers.
		self.output_channels = dict((name, None) for name, type in self._env.variables.items() if type == 'output')

		# Output device labels.
		self.awg = ''
		self.oscilloscope = ''

		# Same structure as values, but optional string-only resource labels and matching Resource objects.
		self.resource_labels = {}
		self.resources = {}

		# Program averaging.
		self.times_average = 1
		self.acq_delay = Quantity(0, 's')

	@property
	def all_values(self):
		return self._env.all_values

	@property
	def frequency(self):
		return self._env.frequency

	@frequency.setter
	def frequency(self, value):
		self._env.frequency = value

	@property
	def missing_values(self):
		return self._env.missing_values

	@property
	def values(self):
		return self._env.values

	@property
	def variables(self):
		return self._env.variables

	def set_value(self, parameter, value):
		"""
		Set a value, even if it has already been set previously.
		"""

		self._env.values[parameter] = value

	def generate_waveforms(self, dry_run=False):
		"""
		Generate the waveforms, given that the values are all filled in.
		"""

		self._env.stage = self._env.stages.waveforms
		self._env.dry_run = dry_run
		self._env.missing_shapes = set()
		self._env.errors = []
		self._env.traverse_tree(self._ast)

		if self._env.errors:
			raise PulseError(self._env.format_errors())

		return self._env.waveforms

	@property
	def with_resources(self):
		"""
		Produce a copy object, with a cloned Environment, and with all resources which exist mutated to point to the corresponding values.

		Note: Because the Resource objects must be shared between copies, there may only ever exist one copy at a time.
		"""

		result = copy(self)

		# We plan to modify the values in the Environment.
		result._env = deepcopy(self._env)

		for parameter, label in self.resource_labels.items():
			def setter(x, parameter=parameter):
				result._env.values[parameter] = x

			res = result.resources[parameter]
			res.setter = setter

			# Type checking.
			var_type = result._env.variables[parameter[0]]
			if var_type == 'delay':
				res.units = 's'
			elif var_type == 'int':
				pass
			elif var_type == 'pulse':
				if parameter[1] == 'amplitude':
					res.units = 'V'
				elif parameter[1] == 'length':
					res.units = 's'

		return result
