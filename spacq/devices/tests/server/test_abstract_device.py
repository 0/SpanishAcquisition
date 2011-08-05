from nose.plugins.skip import SkipTest
from nose.tools import assert_raises, eq_
from unittest import main, TestCase

from testconfig import config as tc

from ... import abstract_device


class AbstractDeviceTest(TestCase):
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

			# Value to check against.
			id = dev.idn

			expected = ['1'] * 3 + [id]

			assert_raises(ValueError, dev.multi_command_stop)

			# Don't actually send anything.
			dev.multi_command_start()
			responses = dev.multi_command_stop()

			eq_(responses, [])

			# Expect a response.
			dev.multi_command_start()
			dev.opc
			dev.opc
			dev.opc
			dev.idn
			responses = dev.multi_command_stop()

			eq_(responses, expected)

			return

		raise SkipTest('Could not connect to any device.')

	def testClose(self):
		"""
		Close the device.
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

			dev.idn
			dev.opc

			dev.close()

			return

		raise SkipTest('Could not connect to any device.')


if __name__ == '__main__':
	main()
