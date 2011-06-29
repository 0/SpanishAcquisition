import re

from ...mock.mock_abstract_device import MockAbstractDevice
from ...tools import BinaryEncoder
from ..voltage_source import VoltageSource

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

	def __init__(self, *args, **kwargs):
		"""
		Pretend to connect to the voltage source.
		"""

		self.port_settings = {}

		self.mocking = VoltageSource

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['ports'] = [MockPort() for _ in xrange(16)]

	def write(self, message, result=None, done=False):
		if done:
			MockAbstractDevice.write(self, message, result, done)

		message = BinaryEncoder.decode(message)

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
			self.mock_state['port'] = int(m.group(1), 16)

			self.output = self.standard_reply
		elif message.startswith('0000 0014 0010 0111 0260 0000 0003 '):
			m = re.match('0000 0014 0010 0111 0260 0000 0003 ([0-9a-f]{2})00 ([0-9a-f ]{9})', message)
			len = int(m.group(1), 16)
			cmd = ''.join(['{0:08b}'.format(~ord(x) & 0xff) for x in BinaryEncoder.encode(m.group(2))[:len]])

			# Destructure the command.
			read = bool(int(cmd[0])) # Read on True, write on False.
			num_bytes = 1 + int(cmd[1:3], 2)
			register = int(cmd[4:8], 2)
			value = int(cmd[8:8+8*num_bytes], 2)

			if not read:
				if register >= 0 and register <= 2:
					# Data input register.
					value = ~value & (2 ** (8 * num_bytes) - 1)
					# Assuming here that it's OK to overwrite the lower bits with 0.
					value <<= 8 * (3 - register - num_bytes)

					self.mock_state['ports'][self.mock_state['port']].voltage = value
				elif register >= 4 and register <= 5:
					# Command register.
					# Assuming here that it's OK to overwrite the lower bits with 0.
					value <<= 8 * (6 - register - num_bytes)
					value = '{0:016b}'.format(value)

					# Destructure the CMR values.
					resolution = 20 if int(value[9]) else 16 # RES
					self.mock_state['ports'][self.mock_state['port']].resolution = resolution
					if int(value[10]): # CLR
						self.mock_state['ports'][self.mock_state['port']].voltage = 0

			# Reading never works.
			answer = 'ff' * len + '00' * (4 - len)
			self.output = '0000 0014 0010 0100 0000 0002 {0:02x}00 0000 {1}'.format(len, answer)
		else:
			self.output = None

		if self.output is not None:
			self.output = BinaryEncoder.encode(self.output)


name = 'Voltage source'
implementation = MockVoltageSource
