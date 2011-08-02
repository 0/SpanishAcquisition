from os.path import dirname

from .parser import Parser, PulseError, PulseSyntaxError
from .tree import Environment

"""
Pulse programs as compiled entities.
"""


class Program(object):
	"""
	A prepared, compiled pulse program.
	"""

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
		p.env.cwd = dirname(path)

		return p

	def __init__(self, env, ast):
		"""
		Given a blank Environment and AST, prepare a program.
		"""

		self.env = env
		self.ast = ast

		for stage in self.env.prep_stages:
			self.env.stage = stage
			self.env.traverse_tree(self.ast)

			if self.env.errors:
				raise PulseSyntaxError(self.env.format_errors())

	def generate_waveforms(self, frequency):
		"""
		Generate the waveforms, given that the values are all filled in.
		"""

		self.env.frequency = frequency
		self.env.stage = self.env.stages.waveforms
		self.env.errors = []
		self.env.traverse_tree(self.ast)

		if self.env.errors:
			raise PulseError(self.env.format_errors())
