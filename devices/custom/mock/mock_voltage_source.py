import re

from devices.custom.voltage_source import Encoder, VoltageSource
from devices.mock.mock_abstract_device import MockAbstractDevice

"""
Mock Voltage Source

Control a fake voltage source.
"""


class MockPort(object):
	"""
	Mock port.
	"""

	def __init__(self):
		self._voltage = 0

	def set_voltage(self, voltage):
		self._voltage = voltage

	voltage = property(fset=set_voltage)


class MockVoltageSource(MockAbstractDevice, VoltageSource):
	"""
	Mock interface for Tektronix AWG5014B AWG.
	"""

	# Not sure what it means, but it comes up a lot.
	standard_reply = '0000 000c 0008 0100 0000 0002'

	def __reset(self):
		"""
		Reset to a known blank state.
		"""

		self.mock_state['ports'] = [MockPort() for _ in xrange(16)]

	def __init__(self, *args, **kwargs):
		"""
		Pretend to connect to the voltage source.
		"""

		MockAbstractDevice.__init__(self, *args, **kwargs)

		self.name = 'VoltageSource'

		VoltageSource.setup(self, {})

		self.__reset()

	def write(self, message, result=None, done=False):
		if done:
			MockAbstractDevice.write(self, message, result, done)

		message = Encoder.decode(message)

		# These all elicit the same response.
		uninteresting_messages = [
			'0000 0010 000c 0113 0280 0000 0000 ff01',
			'0000 0010 000c 0112 0280 0000 00ff ff00',
			'0000 0014 0010 0110 0260 0000 0000 0064 0700 0000',
		]

		if message in uninteresting_messages:
			self.output = self.standard_reply
		elif message == '0000 000c 0008 0100 0000 0000':
			self.output = '0000 001c 0018 0100 0000 0002 0200 1000 0100 c001 0100 c000 0002 000o'
		elif message.startswith('0000 0010 000c 0111 0280 0000 00ff '):
			m = re.match('0000 0010 000c 0111 0280 0000 00ff ([0-9a-f]{2})00', message)
			self.port = int(m.group(1), 16)

			self.output = self.standard_reply
		elif message.startswith('0000 0014 0010 0111 0260 0000 0003 '):
			m = re.match('0000 0014 0010 0111 0260 0000 0003 ([0-9a-f]{2})00 ([0-9a-f ]{9})', message)
			len = int(m.group(1), 16)
			cmd = m.group(2)

			# TODO: Act on the command.

			answer = 'ff' * len + '00' * (4 - len)
			self.output = '0000 0014 0010 0100 0000 0002 {0:02x}00 0000 {1}'.format(len, answer)
		else:
			self.output = None

		if self.output is not None:
			self.output = Encoder.encode(self.output)


if __name__ == '__main__':
	import unittest

	from tests import test_mock_voltage_source as my_tests

	unittest.main(module=my_tests)
