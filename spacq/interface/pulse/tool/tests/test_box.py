from nose.tools import assert_raises, eq_
from StringIO import StringIO
from unittest import main, TestCase

from .. import box


class FindLocationTest(TestCase):
	multiline = [
		'',
		'This is some text.',
		'',
		'It has blank lines, and no tabs.\r',
		'It also has Windows-style line endings.',
		'Sometimes.'
	]

	def testOneLine(self):
		s = 'Test string. Do not read.'

		data = [
			(0, 1, 1),
			(5, 1, 6),
			(25, 1, 26),
		]

		for loc, row, col in data:
			eq_(box.find_location(s, loc), (row, col, s))

	def testMultiline(self):
		s = '\n'.join(self.multiline)
		
		data = [
			(0, 1, 1),
			(40, 4, 20),
			(105, 6, 11),
		]

		for loc, row, col in data:
			eq_(box.find_location(s, loc), (row, col, self.multiline[row - 1].rstrip()))

	def testInvalid(self):
		s = '\n'.join(self.multiline)

		data = [-10, -1, 106]

		for loc in data:
			assert_raises(ValueError, box.find_location, s, loc)


class FormatErrorTest(TestCase):
	def testWithoutPosition(self):
		data = ['', 'test', 'This is a message!']

		for msg in data:
			eq_(box.format_error(msg), 'error: ' + msg)

	def testWithPosition(self):
		result = box.format_error('Test', 1, 2, 'line')

		eq_(result, 'error: Test at column 2 on line 1:\n  line\n   ^')


class LoadValuesTest(TestCase):
	def testEmpty(self):
		f = StringIO()
		result = box.load_values(f)

		eq_(result, [])

	def testOneLine(self):
		f = StringIO('1.0, 2.0, 3.0,4.0')
		result = box.load_values(f)

		eq_(result, [1.0, 2.0, 3.0, 4.0])

	def testOneColumn(self):
		f = StringIO('1.0\n2.0\n3.0\n4.0')
		result = box.load_values(f)

		eq_(result, [1.0, 2.0, 3.0, 4.0])

	def testShaped(self):
		f = StringIO("""
			1.0  ,2.0,3.0

			4.0,	5.0
			6.0

		""")

		result = box.load_values(f)

		eq_(result, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])


if __name__ == '__main__':
	main()
