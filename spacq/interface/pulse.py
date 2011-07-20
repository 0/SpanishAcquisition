import logging
log = logging.getLogger(__name__)

import re

from units import Quantity

"""
A parser to parse programs of the form:

# Zero the value.
set 0.0
# Leave the value for 500 nanoseconds.
delay 500 ns
# Sweep up to 1.0 over sweep_time.
sweep 0.0, 1.0, sweep_time # sweep_time is a parameter
"""


class Parameter(object):
	"""
	A named parameter, possibly with a set value.
	"""

	def __init__(self, name, value=None):
		self.name = name
		self.value = value

	def __repr__(self):
		if self.value is not None:
			return 'Parameter({0}, {1})'.format(repr(self.name), repr(self.value))
		else:
			return 'Parameter({0})'.format(repr(self.name))

	def __str__(self):
		if self.value is not None:
			return '{0}{{{1}}}'.format(self.name, self.value)
		else:
			return '{0}'.format(self.name)

	def __eq__(self, other):
		return self.name == other.name and (self.value is None and other.value is None
				or self.value == other.value)


class Command(object):
	"""
	A command and some arguments.
	"""

	def __init__(self, command, arguments):
		self.command = command
		self.arguments = arguments

	def __repr__(self):
		return "Command({0}, {1})".format(repr(self.command), repr(self.arguments))

	def __str__(self):
		if self.arguments:
			return '{0} {1}'.format(self.command, ', '.join(str(x) for x in self.arguments))
		else:
			return '{0}'.format(self.command)

	def __eq__(self, other):
		return self.command == other.command and self.arguments == other.arguments


class Parser(object):
	"""
	Simple parser for pulse programs.
	"""

	# Valid parameters are of this form.
	parameter_re = re.compile('^[a-z][a-z0-9_]*$', flags=re.IGNORECASE)

	def _parse_symbol(self, symbol):
		"""
		Extract the contents of a colon-prefixed symbol.
		"""

		if len(symbol) >= 2 and symbol[0] == ':':
			return symbol[1:]
		else:
			raise ValueError(symbol)

	def _parse_string(self, string):
		"""
		Extract the contents of a quote-delimited string.
		"""

		if len(string) >= 2 and string[0] == string[-1] and string[0] in ['"', "'"]:
			return string[1:-1]
		else:
			raise ValueError(string)

	def _parse_parameter(self, parameter):
		"""
		Use the value as a parameter if it matches.
		"""

		if self.parameter_re.match(parameter):
			return Parameter(parameter)

		raise ValueError(parameter)

	def _parse_arg(self, arg):
		"""
		Try to make sense of the argument.
		"""

		for f in self.parse_functions:
			try:
				return f(arg)
			except ValueError:
				pass

		raise ValueError(arg)

	def _parse_line(self, line):
		"""
		Parse a single line.

		Returns None if there is nothing of substance; otherwise a command/args pair.
		"""

		log.debug('Parsing line: {0}'.format(line))

		# Remove the comment, if any.
		line = line.split('#', 1)[0]

		# Trim whitespace from the ends.
		line = line.strip()

		# Ignore blank or comment lines.
		if line == '':
			return None

		# Extract the arguments.
		try:
			# Split on the first whitespace.
			cmd, arg_str = line.split(None, 1)
		except ValueError:
			# No arguments.
			cmd = line
			args = []
		else:
			# Separate and trim the arguments.
			args = arg_str.split(',')
			args = [arg.strip() for arg in args]

			log.debug('Found arguments: {0}'.format(', '.join(args)))

			# Parse the arguments as appropriate.
			args = [self._parse_arg(arg) for arg in args]

		return Command(cmd, args)

	def __init__(self):
		self.parse_functions = [int, float, self._parse_symbol, self._parse_string, Quantity, self._parse_parameter]

	def parse_program(self, prog):
		"""
		Convert a multi-line program to a corresponding list of pulse commands.
		"""

		commands = [self._parse_line(line) for line in prog.splitlines()]

		return [cmd for cmd in commands if cmd is not None]


class Program(object):
	"""
	A list of commands, possibly with parameters.
	"""

	def __init__(self, commands):
		"""
		Create a list of commands and collect all the matching parameters.
		"""

		if isinstance(commands, basestring):
			parser = Parser()
			commands = parser.parse_program(commands)

		self.commands = []
		self.parameters = {}

		for cmd in commands:
			new_cmd = Command(cmd.command, cmd.arguments[:])

			for i, arg in enumerate(new_cmd.arguments):
				if not isinstance(arg, Parameter):
					continue

				try:
					# Check if we already know a parameter by this name.
					param = self.parameters[arg.name]
				except KeyError:
					# No, it's a new parameter.
					self.parameters[arg.name] = arg
				else:
					# Yes, so alias the Parameter object in the command to the existing one.
					new_cmd.arguments[i] = param

			self.commands.append(new_cmd)

	def set_parameter(self, name, value=None):
		"""
		Set the value of a parameter.
		"""

		self.parameters[name].value = value

	@property
	def all_parameters(self):
		"""
		The names of all parameters.
		"""

		return set(self.parameters.keys())

	@property
	def unset_parameters(self):
		"""
		The names of all parameters which lack a value.
		"""

		return set(name for name, param in self.parameters.iteritems() if param.value is None)

	@property
	def evaluated(self):
		"""
		Return the commands with the parameters evaluated.
		"""

		if self.unset_parameters:
			raise ValueError('Some parameters are unset.')

		result = []

		for cmd in self.commands:
			evaluated_args = []

			for arg in cmd.arguments:
				if isinstance(arg, Parameter):
					evaluated_args.append(arg.value)
				else:
					evaluated_args.append(arg)

			result.append(Command(cmd.command, evaluated_args))

		return Program(result)

	def __repr__(self):
		return 'Program({0})'.format(repr(self.commands))

	def __str__(self):
		return '\n'.join([str(cmd) for cmd in self.commands])

	def __eq__(self, other):
		return self.commands == other.commands
