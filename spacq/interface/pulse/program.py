from .parser import Parser
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

		return cls.from_string('\n'.join(prog_lines))

	def __init__(self, env, ast):
		"""
		Given a blank Environment and AST, prepare a program.
		"""

		self.env = env
		self.ast = ast

		for stage in env.prep_stages:
			env.stage = stage
			env.traverse_tree(ast)

			if env.errors:
				raise ValueError(env.errors)

	def generate_waveforms(self, frequency):
		"""
		Generate the waveforms, given that the values are all filled in.
		"""

		self.env.stage = self.env.stages.waveforms
		self.env.frequency = frequency
		self.env.traverse_tree(self.ast)
