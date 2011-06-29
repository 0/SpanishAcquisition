from nose.plugins.skip import SkipTest
from nose.tools import eq_
import unittest

from testconfig import config as tc

from ... import abstract_device


class AbstractDeviceTest(unittest.TestCase):
	def testAskRaw(self):
		"""
		Converse briefly with real devices.
		"""

		found_any = False

		# Try all devices to which a connection can be established.
		for name, device in tc['devices'].items():
			if not (name.endswith('.eth') or name.endswith('.gpib')):
				continue
			if not 'address' in device:
				continue

			try:
				dev = abstract_device.AbstractDevice(**device['address'])
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
		for name, device in tc['devices'].items():
			if not (name.endswith('.eth') or name.endswith('.gpib')):
				continue
			if not 'address' in device:
				continue

			try:
				dev = abstract_device.AbstractDevice(**device['address'])
			except:
				continue

			# Some values to check against.
			id = dev.idn
			ver = dev.ask('system:version?')

			expected = [ver, ver, id]

			dev.multi_command_start()
			dev.ask('system:version?')
			dev.write('*opc')
			dev.ask('system:version?')
			dev.ask('*idn?')
			responses = dev.multi_command_stop()

			eq_(responses, expected)

			return

		raise SkipTest('Could not connect to any device.')


if __name__ == '__main__':
	unittest.main()
