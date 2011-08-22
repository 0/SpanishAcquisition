import logging
log = logging.getLogger(__name__)

from os import path

from spacq.tool.box import Enum

from ..units import IncompatibleDimensions, Quantity
from ..waveform import Generator
from .tool.box import find_location, format_error, load_values

"""
Abstract syntax tree bits for pulse programs.
"""


def draw_thing(thing, depth):
	"""
	Draws something at a given depth.
	"""

	if isinstance(thing, ASTNode):
		if thing.is_list:
			result = ('{0}\n'.format(thing.__class__.__name__) +
				''.join(draw_thing(item, depth + 1) for item in thing.items))
		else:
			result = thing.draw(depth)
	else:
		result = str(thing) + '\n'

	return ' ' * depth + result


class Environment(object):
	"""
	An AST-traversal environment.
	"""

	# Traversal stages:
	#  declarations: collect variable names and types
	#  values: collect variable values
	#  commands: verify commands for outputs
	#  waveforms: generate waveforms
	stages = Enum(['declarations', 'values', 'commands', 'waveforms'])

	# The stages that must happen (in this order) before waveform generation.
	# These only require the data which is contained in the pulse program itself.
	prep_stages = [stages.declarations, stages.values, stages.commands]

	def __init__(self):
		self.stage = None
		self.stack = []

		# Declared variable names (with types as values).
		self.variables = {}

		# Variable and attribute values.
		#  Keys are tuples of strings:
		#   ('x',): x is a variable
		#   ('x', 'y'): y is an attribute
		self.values = {}

		# Whether acquisition has already been requested.
		self.acquisition = False

		# Any errors; each error is of the form
		#  (error string, (row, col, code line))
		self.errors = []

		# Whether to actually generate waveforms.
		self.dry_run = False

		# Waveform generators for the output channels.
		# Keys are output names.
		self.generators = {}

		# Generated waveforms.
		self.waveforms = {}

		# Where to look for shapes.
		self.cwd = None

		# Shapes that could not be found.
		self.missing_shapes = set()

		# Default frequency.
		self.frequency = Quantity(1, 'Hz')

	@property
	def missing_values(self):
		existing_values = set(self.values.keys())

		return self.all_values - existing_values

	def add_error(self, msg, loc=None):
		"""
		Add an error.
		"""

		self.errors.append((msg, loc))

	def pre_stage(self):
		"""
		Set up for a stage.
		"""

		if self.stage == self.stages.waveforms:
			if self.missing_values:
				values = ', '.join('.'.join(x) for x in sorted(self.missing_values))

				raise ValueError('Cannot generate waveforms while values are missing: {0}'.format(values))

			# Set up output waveform generators.
			for output in self.waveforms:
				self.generators[output] = Generator(frequency=self.frequency, dry_run=self.dry_run)

	def post_stage(self):
		"""
		Clean up after a stage has completed.
		"""

		if self.stage == self.stages.declarations:
			# Prepare for output waveform generators.
			for output in [var for var, type in self.variables.items() if type == 'output']:
				self.generators[output] = None
				self.waveforms[output] = None

			# Generate labels for all necessary values.
			self.all_values = set()
			for name, type in self.variables.items():
				if type == 'pulse':
					for attr in ['amplitude', 'length', 'shape']:
						self.all_values.add((name, attr))
				elif type == 'acq_marker':
					for attr in ['marker_num', 'output']:
						self.all_values.add((name, attr))
				elif type != 'output':
					self.all_values.add((name,))
		elif self.stage == self.stages.waveforms:
			# Finalize waveform creation.
			for output in self.generators:
				self.waveforms[output] = self.generators[output].waveform

	def set_value(self, target, value):
		"""
		Set a value if the types work out. TypeError otherwise.
		"""

		# Type checking.
		var_type = self.variables[target[0]]
		if var_type == 'acq_marker':
			if len(target) == 1:
				raise TypeError('Must assign dictionary to acq_marker')
			else:
				if target[1] == 'marker_num':
					if not isinstance(value, int):
						raise TypeError('Must assign int to acq_marker num')
				elif target[1] == 'output':
					if not isinstance(value, basestring):
						raise TypeError('Must assign string to acq_marker num')
		elif var_type == 'delay':
			try:
				value.assert_dimensions('s')
			except (AttributeError, IncompatibleDimensions):
				raise TypeError('Must assign time quantity to delay')
		elif var_type == 'int':
			if not isinstance(value, int):
				raise TypeError('Must assign integer to int')
		elif var_type == 'pulse':
			if len(target) == 1:
				raise TypeError('Must assign dictionary to pulse')
			else:
				if target[1] == 'amplitude':
					try:
						value.assert_dimensions('V')
					except (AttributeError, IncompatibleDimensions):
						raise TypeError('Must assign voltage quantity to pulse amplitude')
				elif target[1] == 'length':
					try:
						value.assert_dimensions('s')
					except (AttributeError, IncompatibleDimensions):
						raise TypeError('Must assign time quantity to pulse length')
				elif target[1] == 'shape':
					if not isinstance(value, basestring):
						raise TypeError('Must assign string to pulse shape')
		else:
			raise TypeError('Cannot assign to variable of type "{0}"'.format(var_type))

		if target in self.values and self.values[target] is not None:
			raise TypeError('Re-assignment of {0}'.format(target))
		else:
			self.values[target] = value

	def traverse_tree(self, root):
		"""
		Modify the Environment, given a pulse program AST.
		"""

		self.pre_stage()
		root.visit(self)
		self.post_stage()

	def format_errors(self):
		result = []

		# Sort by line number, then column number, and ignore duplicates.
		for error in sorted(set(self.errors),
				key=(lambda x: (x[1][0], x[1][1]) if x[1] is not None else (-1, -1))):
			if error[1] is not None:
				result.append(format_error(error[0], *error[1]))
			else:
				result.append(format_error(error[0]))

		return result


class ASTNode(object):
	names = []
	is_list = False

	def __init__(self, *args):
		log.debug('Creating node of type "{0}".'.format(self.__class__.__name__))

		if len(args) == 3:
			self.s = args[0]
			self.loc = args[1]

			tok = args[2]
		else:
			self.s = None
			self.loc = None

			if len(args) == 1:
				tok = args[0]
			else:
				tok = None

		log.debug('Received tokens: {0!r}'.format(tok))

		if self.is_list:
			self.items = list(tok)
		else:
			for name in self.names:
				setattr(self, name, tok[name])

	def __eq__(self, other):
		return repr(self) == repr(other)

	def draw(self, depth):
		return ' ' * depth + self.__class__.__name__ + '\n'

	@property
	def location(self):
		return find_location(self.s, self.loc)


class Acquire(ASTNode):
	def __repr__(self):
		return 'acquire'

	def visit(self, env):
		if env.stage == env.stages.declarations:
			if len(env.stack) != 1:
				env.add_error('Acquisition not at top level', self.location)

			env.variables['_acq_marker'] = 'acq_marker'
		if env.stage == env.stages.commands:
			if env.acquisition:
				env.add_error('Repeated acquisition', self.location)
			else:
				env.acquisition = True
		elif env.stage == env.stages.waveforms:
			acq_marker = env.values[('_acq_marker', 'marker_num')]
			acq_output = env.values[('_acq_marker', 'output')]

			env.generators[acq_output].marker(acq_marker, True)


class Assignment(ASTNode):
	names = ['target', 'value']

	def __repr__(self):
		return '{0!r} = {1!r}'.format(self.target, self.value)

	def draw(self, depth):
		return 'Assignment\n' + draw_thing(self.target, depth + 1) + draw_thing(self.value, depth + 1)

	def assign_value(self, env, target, value):
		try:
			env.set_value(target, value)
		except KeyError as e:
			env.add_error('Undeclared variable "{0}"'.format(e), self.location)
		except TypeError as e:
			env.add_error(str(e), self.location)

	def visit(self, env):
		if env.stage == env.stages.declarations:
			if isinstance(self.target, ASTNode):
				return self.target.visit(env)
			else:
				return (self.target,)
		elif env.stage == env.stages.values:
			if len(env.stack) != 1 and env.stack[-1].__class__ != Declaration:
				env.add_error('Assignment neither at top level nor inside declaration', self.location)

			if isinstance(self.target, ASTNode):
				env.stack.append(self)
				target = self.target.visit(env)
				env.stack.pop()
			else:
				target = (self.target,)

			if target[0] not in env.variables:
				env.add_error('Undeclared variable "{0}"'.format(target[0]), self.location)
			else:
				if isinstance(self.value, Dictionary):
					for k, v in self.value.visit(env).items():
						self.assign_value(env, target + (k,), v)
				else:
					self.assign_value(env, target, self.value)


class Attribute(ASTNode):
	names = ['variable', 'name']

	def __repr__(self):
		return '{0!r}.{1!r}'.format(self.variable, self.name)

	def draw(self, depth):
		return 'Attribute\n' + draw_thing(self.variable, depth + 1) + draw_thing(self.name, depth + 1)

	def visit(self, env):
		result = (self.variable, self.name)

		if env.stage == env.stages.values:
			if result not in env.all_values:
				env.add_error('Unrecognized attribute "{0}"'.format('.'.join(result)), self.location)

		return result


class Block(ASTNode):
	is_list = True

	def __repr__(self):
		return '{{{0}}}'.format(', '.join(repr(item) for item in self.items))

	def draw(self, depth=0):
		# A default of 0 allows this to be called on the AST as a whole.

		return draw_thing(self, depth)

	def visit(self, env):
		env.stack.append(self)
		for item in self.items:
			item.visit(env)
		env.stack.pop()


class Declaration(ASTNode):
	names = ['type', 'variables']

	def __repr__(self):
		return '{0!r} {1}'.format(self.type, ', '.join(repr(variable) for variable in self.variables))

	def draw(self, depth):
		result = ['Declaration\n' + draw_thing(self.type, depth + 1)]

		for variable in self.variables:
			result.append(draw_thing(variable, depth + 1))

		return ''.join(result)

	def visit(self, env):
		if env.stage == env.stages.declarations:
			if len(env.stack) != 1:
				env.add_error('Declaration not at top level', self.location)

			for variable in self.variables:
				env.stack.append(self)
				visited = variable.visit(env)
				env.stack.pop()

				if env.stage == env.stages.declarations:
					new_var_name = visited[0]

					if new_var_name in env.variables:
						env.add_error('Re-declaration of "{0}"'.format(new_var_name), variable.location)
					else:
						env.variables[new_var_name] = self.type
		else:
			for variable in self.variables:
				env.stack.append(self)
				visited = variable.visit(env)
				env.stack.pop()


class Delay(ASTNode):
	names = ['length']

	def __repr__(self):
		return '{0!r}'.format(self.length)

	def draw(self, depth):
		return 'Delay\n' + draw_thing(self.length, depth + 1)

	def visit(self, env):
		if env.stage == env.stages.commands:
			if isinstance(self.length, basestring):
				try:
					if env.variables[self.length] != 'delay':
						env.add_error('Not a delay', self.location)
				except KeyError:
					env.add_error('Undeclared variable "{0}"'.format(self.length), self.location)
			else:
				if not self.length.assert_dimensions('s', exception=False):
					env.add_error('Delay must be a time value', self.location)
		if env.stage == env.stages.waveforms:
			if isinstance(self.length, basestring):
				length = env.values[(self.length,)]
			else:
				length = self.length

			for waveform in env.generators.values():
				waveform.set_next(0.0)
				waveform.delay(length)


class Dictionary(ASTNode):
	is_list = True

	def __repr__(self):
		return '{{{0}}}'.format(', '.join(repr(item) for item in self.items))

	def visit(self, env):
		return dict(x.visit(env) for x in self.items)


class DictionaryItem(ASTNode):
	names = ['key', 'value']

	def __repr__(self):
		return '{0!r}: {1!r}'.format(self.key, self.value)

	def draw(self, depth):
		return repr(self) + '\n'

	def visit(self, env):
		return (self.key, self.value)


class Loop(ASTNode):
	names = ['times', 'block']

	def __repr__(self):
		return 'times {0!r} {1!r}'.format(self.times, self.block)

	def draw(self, depth):
		return 'Loop\n' + draw_thing(self.times, depth + 1) + draw_thing(self.block, depth + 1)

	def visit(self, env):
		if env.stage == env.stages.commands:
			if isinstance(self.times, basestring):
				try:
					if env.variables[self.times] != 'int':
						env.add_error('Repetition count must be int', self.location)
				except KeyError:
					env.add_error('Undeclared variable "{0}"'.format(self.times), self.location)

		if env.stage == env.stages.waveforms:
			if isinstance(self.times, basestring):
				times = env.values[(self.times,)]
			else:
				times = self.times

			for _ in xrange(times):
				env.stack.append(self)
				self.block.visit(env)
				env.stack.pop()
		else:
			env.stack.append(self)
			self.block.visit(env)
			env.stack.pop()


class ParallelPulses(ASTNode):
	is_list = True

	def __repr__(self):
		return '{0}'.format(' '.join(repr(item) for item in self.items))

	def visit(self, env):
		env.stack.append(self)
		for item in self.items:
			item.visit(env)
		env.stack.pop()

		if env.stage == env.stages.waveforms:
			max_length = max(len(waveform._wave) for waveform in env.generators.values())

			for waveform in env.generators.values():
				if len(waveform._wave) < max_length:
					waveform.append([0.0] * (max_length - len(waveform._wave)))


class Pulse(ASTNode):
	names = ['sequence', 'target']

	def __repr__(self):
		return '{0!r}:{1!r}'.format(self.sequence, self.target)

	def draw(self, depth):
		return 'Pulse\n' + draw_thing(self.sequence, depth + 1) + draw_thing(self.target, depth + 1)

	def visit(self, env):
		if env.stage == env.stages.commands:
			if self.target not in env.generators:
				env.add_error('Undefined output "{0}"'.format(self.target), self.location)

		env.stack.append(self)
		self.sequence.visit(env)
		env.stack.pop()


class PulseSequence(ASTNode):
	is_list = True

	def __repr__(self):
		return '({0})'.format(', '.join(repr(item) for item in self.items))

	def visit(self, env):
		if env.stage == env.stages.commands:
			for item in self.items:
				if isinstance(item, Delay):
					if not item.length.assert_dimensions('s', exception=False):
						env.add_error('Delay must be a time value', self.location)

					continue

				try:
					type = env.variables[item]
				except KeyError:
					env.add_error('Undeclared variable "{0}"'.format(item), self.location)
				else:
					if type not in ['delay', 'pulse']:
						env.add_error('Invalid command "{0}"'.format(item), self.location)
		elif env.stage == env.stages.waveforms:
			target = env.generators[env.stack[-1].target]

			for item in self.items:
				if isinstance(item, basestring):
					type = env.variables[item]

					if type == 'delay':
						target.set_next(0.0)
						target.delay(env.values[(item,)])
					elif type == 'pulse':
						amplitude = float(env.values[(item, 'amplitude')].value)
						length = env.values[(item, 'length')]
						shape = env.values[(item, 'shape')]

						if shape not in env.missing_shapes:
							if shape == 'square':
								target.square(amplitude, length)
							else:
								# Figure out all the locations where the file can be.
								paths = [shape]
								if env.cwd is not None:
									paths.append(path.join(env.cwd, shape))

								data = None
								for p in paths:
									try:
										with open(p) as f:
											data = load_values(f)
									except IOError:
										continue
									except ValueError:
										raise ValueError('Not a shape file: {0}'.format(p))

								if data is None:
									env.add_error('File "{0}" (due to "{1}") not found'.format(shape, item),
											self.location)
									env.missing_shapes.add(shape)
								else:
									target.pulse(data, amplitude, length)
				else:
					target.set_next(0.0)
					target.delay(item.length)


class Variable(ASTNode):
	names = ['name']

	def __repr__(self):
		return '{0!r}'.format(self.name)

	def draw(self, depth):
		return 'Variable\n' + draw_thing(self.name, depth + 1)

	def visit(self, env):
		return (self.name,)
