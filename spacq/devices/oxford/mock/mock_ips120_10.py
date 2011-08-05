from ...mock.mock_abstract_device import MockAbstractDevice
from ..ips120_10 import IPS120_10

"""
Mock Sample IPS120_10
"""


class MockIPS120_10(MockAbstractDevice, IPS120_10):
	"""
	Mock interface for the Sample IPS120_10.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = IPS120_10

		self.heater_delay = 0

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['heater_on'] = False
		self.mock_state['activity'] = 4
		self.mock_state['mode'] = 0

		self.mock_state['output_field'] = 0.0
		self.mock_state['set_point'] = 0.0
		self.mock_state['sweep_rate'] = 1.0
		self.mock_state['persistent_field'] = 0.0

	def _split_message(self, message):
		if message[0] == '$':
			query = False
			message = message[1:]
		else:
			query = True

		cmd = message[0]
		args = message[1:]

		return (cmd, args, query)

	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)

			if cmd in ['C', 'M', 'Q']:
				done = True
			elif cmd == 'A' and not query:
				self.mock_state['activity'] = int(args)
				if self.mock_state['activity'] == 0:
					done = True
				elif self.mock_state['activity'] == 1:
					self.mock_state['output_field'] = self.mock_state['set_point']
					done = True
			elif cmd == 'H' and not query:
				self.mock_state['heater_on'] = (args == '1')
				if not self.mock_state['heater_on']:
					self.mock_state['persistent_field'] = self.mock_state['output_field']
				done = True
			elif cmd == 'J' and not query:
				self.mock_state['set_point'] = float(args)
				done = True
			elif cmd == 'R':
				if query:
					result = 'R'
					if args == '7':
						result += str(self.mock_state['output_field'])
					if args == '8':
						result += str(self.mock_state['set_point'])
					if args == '9':
						result += str(self.mock_state['sweep_rate'])
					elif args == '18':
						result += str(self.mock_state['persistent_field'])
				done = True
			elif cmd == 'T' and not query:
				self.mock_state['sweep_rate'] = float(args)
				done = True
			elif cmd == 'X':
				if query:
					# 9 is used for the don't-cares
					result = 'X00A{0}C9H{1}M9{2}'.format(self.mock_state['activity'],
							str(int(self.mock_state['heater_on'])), self.mock_state['mode'])
				done = True


		MockAbstractDevice.write(self, message, result, done)


name = 'IPS120-10'
implementation = MockIPS120_10
