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

	def testMultiCommand(self):
		"""
		Send a multi-command message.
		"""

		# Use any device.
		for name, device in config['devices'].items():
			if not (name.endswith('.eth') or name.endswith('.gpib')):
				continue

			try:
				dev = abstract_device.AbstractDevice(**device)
			except:
				continue

			# Some values to check against.
			id = dev.ask('*idn?')
			ver = dev.ask('system:version?')

			expected = [ver, ver, id]

			dev.multi_command_start()
			dev.ask('system:version?')
			dev.write('*rst')
			dev.write('system:preset')
			dev.ask('system:version?')
			dev.ask('*idn?')
			responses = dev.multi_command_stop()

			eq_(responses, expected)

			return

		raise SkipTest('Could not connect to any device.')


if __name__ == '__main__':
	unittest.main()
