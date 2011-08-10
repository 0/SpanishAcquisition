from nose.tools import assert_raises, eq_
from unittest import main, TestCase

from .. import list_columns


class ListParserTest(TestCase):
	def testSmall(self):
		"""
		Try a small list.
		"""

		lp = list_columns.ListParser()

		eq_(lp('[(1.2, 3.4)]'), [(1.2, 3.4)])

	def testLarger(self):
		"""
		Try a larger (Python-generated) list.
		"""

		lst = [(float(x) / 3, float(y) / 5) for x in xrange(55) for y in xrange(25)]

		lp = list_columns.ListParser()

		eq_(lp(str(lst)), lst)

	def testInvalid(self):
		"""
		These aren't lists!
		"""

		lsts = [
			'',
			'[]',
			'(1,2),(3,4)',
			'[(1,2),',
			'[(1,2,3),(4,5,6)]',
		]

		lp = list_columns.ListParser()

		for lst in lsts:
			assert_raises(ValueError, lp, lst)


if __name__ == '__main__':
	main()
