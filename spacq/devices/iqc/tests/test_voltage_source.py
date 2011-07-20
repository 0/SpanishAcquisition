from nose.tools import eq_
from unittest import main, TestCase

from .. import voltage_source


class PortTest(TestCase):
	def testCalculateVoltage(self):
		"""
		Trivial conversion.
		"""

		port = voltage_source.Port(None, None, apply_settings=False, resolution=20)

		data = [
			(-10, 0xfffff),
			(-5, 0xbffff),
			(0, 0x7ffff),
			(5, 0x3ffff),
			(10, 0x00000),
		]

		for v, r in data:
			eq_(port.calculate_voltage(v), r)

	def testResolution(self):
		"""
		Trivial conversion at another resolution.
		"""

		port = voltage_source.Port(None, None, apply_settings=False, resolution=16)

		data = [
			(-10, 0xffff),
			(-5, 0xbfff),
			(0, 0x7fff),
			(5, 0x3fff),
			(10, 0x0000),
		]

		for v, r in data:
			eq_(port.calculate_voltage(v), r)

	def testVoltageBounds(self):
		"""
		Trivial conversion gone wrong.
		"""

		port = voltage_source.Port(None, None, apply_settings=False)

		data = ['x', -10.1, 10.1, None, 42]

		for v in data:
			try:
				port.calculate_voltage(v)
			except ValueError:
				pass
			else:
				assert False, 'Expected ValueError'

	def testFormatForDAC(self):
		"""
		Make the messages more palatable.
		"""

		data = [
			('', ''),
			('0', 'ff00 0000'),
			('00', 'ff00 0000'),
			('0000 0000', 'ffff ffff'),
			('ffff', '0000 0000'),
			('123456', 'edcb a900'),
		]

		for m, f in data:
			eq_(voltage_source.Port.format_for_dac(m), f)


	def testCustomBounds(self):
		"""
		Try conversions with custom minimum and maximum values.
		"""

		port = voltage_source.Port(None, None, apply_settings=False, min_value=-100, max_value=-30)

		data = [
			(-100, 0xfffff),
			(-65, 0x7ffff),
			(-30.00007, 0x00001),
			(-30, 0x00000),
		]

		for v, r in data:
			eq_(port.calculate_voltage(v), r)


if __name__ == '__main__':
	main()
