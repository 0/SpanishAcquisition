from os.path import basename, dirname

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

		# Output device label.
		self.device = ''

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
		self._env.errors = []
		self._env.traverse_tree(self._ast)

		if self._env.errors:
			raise PulseError(self._env.format_errors())

		return self._env.waveforms
