from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from testconfig import config

from devices import abstract_device


class AbstractDeviceTest(unittest.TestCase):
	def testAskRaw(self):
		"""
		Converse briefly with real devices.
		"""

		found_any = False

		# Try all devices to which a connection can be established.
		for name, device in config['devices'].items():
			if not (name.endswith('.eth') or name.endswith('.gpib')):
				continue

			try:
				dev = abstract_device.AbstractDevice(**device)
			except:
				continue

			msg = dev.ask_raw('*idn?')
			eq_(msg[-1], '\n')

			found_any = True

		if not found_any:
			raise SkipTest('Could not connect to any device.')


if __name__ == '__main__':
	unittest.main()
