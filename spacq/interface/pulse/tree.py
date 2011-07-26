"""
Abstract syntax tree bits for pulse programs.
"""


def draw_tree(ast):
	"""
	Draws an AST.

	Technically, draws several ASTs, as there is a root node per top-level statement.
	"""

	return [draw_thing(root, 0) for root in ast]


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


class ASTNode(object):
	names = []
	is_list = False

	def __init__(self, *args):
		if len(args) == 3:
			self.s = args[0]
			self.loc = args[1]

			tok = args[2]
		else:
			self.s = None
			self.loc = None

			if len(args) == 1:
				tok = args[0]

		if self.is_list:
			self.items = list(tok)
		else:
			for name in self.names:
				setattr(self, name, tok[name])

	def __eq__(self, other):
		return repr(self) == repr(other)

	def draw(self, depth):
		return ' ' * depth + self.__class__.__name__ + '\n'


class Acquire(ASTNode):
	def __repr__(self):
		return 'acquire'


class Assignment(ASTNode):
	names = ['target', 'value']

	def __repr__(self):
		return '{0} = {1}'.format(repr(self.target), repr(self.value))

	def draw(self, depth):
		return 'Assignment\n' + draw_thing(self.target, depth + 1) + draw_thing(self.value, depth + 1)


class Attribute(ASTNode):
	names = ['variable', 'name']

	def __repr__(self):
		return '{0}.{1}'.format(repr(self.variable), repr(self.name))

	def draw(self, depth):
		return 'Attribute\n' + draw_thing(self.variable, depth + 1) + draw_thing(self.name, depth + 1)


class Block(ASTNode):
	is_list = True

	def __repr__(self):
		return '{{{0}}}'.format(', '.join(repr(item) for item in self.items))


class Declaration(ASTNode):
	names = ['type', 'variables']

	def __repr__(self):
		return '{0} {1}'.format(repr(self.type), ', '.join(repr(variable) for variable in self.variables))

	def draw(self, depth):
		result = ['Declaration\n' + draw_thing(self.type, depth + 1)]

		for variable in self.variables:
			result.append(draw_thing(variable, depth + 1))

		return ''.join(result)

class Delay(ASTNode):
	names = ['length']

	def __repr__(self):
		return '{0}'.format(repr(self.length))

	def draw(self, depth):
		return 'Delay\n' + draw_thing(self.length, depth + 1)


class Dictionary(ASTNode):
	is_list = True

	def __repr__(self):
		return '{{{0}}}'.format(', '.join(repr(item) for item in self.items))


class DictionaryItem(ASTNode):
	names = ['key', 'value']

	def __repr__(self):
		return '{0}: {1}'.format(repr(self.key), repr(self.value))

	def draw(self, depth):
		return repr(self) + '\n'


class Loop(ASTNode):
	names = ['times', 'block']

	def __repr__(self):
		return 'times {0} {1}'.format(repr(self.times), repr(self.block))

	def draw(self, depth):
		return 'Loop\n' + draw_thing(self.times, depth + 1) + draw_thing(self.block, depth + 1)


class ParallelPulses(ASTNode):
	is_list = True

	def __repr__(self):
		return '{0}'.format(' '.join(repr(item) for item in self.items))


class Pulse(ASTNode):
	names = ['sequence', 'target']

	def __repr__(self):
		return '{0}:{1}'.format(repr(self.sequence), repr(self.target))

	def draw(self, depth):
		return 'Pulse\n' + draw_thing(self.sequence, depth + 1) + draw_thing(self.target, depth + 1)


class PulseSequence(ASTNode):
	is_list = True

	def __repr__(self):
		return '({0})'.format(', '.join(repr(item) for item in self.items))


class Variable(ASTNode):
	names = ['name']

	def __repr__(self):
		return '{0}'.format(repr(self.name))

	def draw(self, depth):
		return 'Variable\n' + draw_thing(self.name, depth + 1)
