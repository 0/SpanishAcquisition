from nose.tools import eq_
import unittest

from devices.custom import voltage_source


class TestEncoder(unittest.TestCase):
	def testEncodeDecode(self):
		"""
		Routine conversions.
		"""

		data = [
			('', '', {}, ''),
			('hex', '\x0e', {}, '0e'),
			('1234', '\x12\x34', {}, '1234'),
			('1234 5678 9 0 a b', '\x12\x34\x56\x78\x90\xab', {}, '1234 5678 90ab'),
			('  ABCDEF   FEDCBA   ', '\xab\xcd\xef\xfe\xdc\xba', {}, 'abcd effe dcba'),
			('0001 0203', '\x00\x01\x02\x03', {}, '0001 0203'),
			('00 010203', '\x00\x01\x02\x03', {'pair_size': 3}, '000102 03'),
			('00 01 02 03', '\x00\x01\x02\x03', {'pair_up': False}, '00010203'),
		]

		for u, e, args, d in data:
			eq_(voltage_source.Encoder.encode(u), e)
			eq_(voltage_source.Encoder.decode(e, **args), d)

	def testLength(self):
		"""
		Routine calculations.
		"""

		data = [
			('', 0),
			('nothing', 0),
			('0000', 2),
			('001', 2),
			('data 0101 234', 5),
			('data 0101 2345', 6),
			('data 0101 2345 6', 6),
		]

		for d, l in data:
			eq_(voltage_source.Encoder.length(d), l)


class TestPort(unittest.TestCase):
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


if __name__ == '__main__':
	unittest.main()
