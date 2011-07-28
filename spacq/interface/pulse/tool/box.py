import csv

from spacq.tool.box import flatten

"""
Pulse program helpers.
"""


def find_location(s, loc):
	"""
	Find where loc (linear index) in s.

	Returns:
		line number
		column number
		line itself

	Note: Tabs are not handled specially.
	"""

	if loc < 0 or loc > len(s):
		raise ValueError('Location given ({0}) is outside string'.format(loc))

	count = 0
	lines = s.splitlines()
	with_ends = s.splitlines(True)

	for i, (line, with_end) in enumerate(zip(lines, with_ends), 1):
		if count + len(line) < loc:
			count += len(with_end)
		else:
			col = loc - count + 1

			return i, col, line


def format_error(msg, row=None, col=None, line=None):
	"""
	Format the error for human consumption.
	"""

	if row is None or col is None or line is None:
		return 'error: {0}'.format(msg)
	else:
		return 'error: {0} at column {1} on line {2}:\n{3}{4}\n{5}^'.format(msg,
				col, row, ' ' * 2, line, ' ' * (col + 1))


def load_values(f):
	"""
	Load data points from a file.

	The values in the file must either be comma separated, line-wise, or a combination of the two.
	For example:
		1.0,2.0,3.0
		4.0,5.0
		6.0
	would be interpreted as [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
	"""

	reader = csv.reader(f)

	# Ignore blank lines.
	return [float(x) for x in flatten(reader) if not x.isspace()]
