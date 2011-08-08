import logging
log = logging.getLogger(__name__)

from ..abstract_device import AbstractDevice

"""
Mock hardware device.
"""


class MockAbstractDevice(AbstractDevice):
	"""
	A class for controlling fake devices.
	"""

	output = None

	@staticmethod
	def _split_message(message):
		"""
		Split a message into usable components.
		"""

		message = message.split(None, 1)
		try:
			cmd, args = message[0], message[1].strip()
		except IndexError:
			cmd, args = message[0], ''

		if cmd[-1] == '?':
			query = True
			cmd = cmd[:-1]
		else:
			query = False
		cmd = cmd.split(':')

		return cmd, args, query

	def __init__(self, autoconnect=True, *args, **kwargs):
		"""
		Create a device, always successfully.
		"""

		log.info('Creating mock device.')

		self.multi_command_responses = None
		self.mock_state = {}

		try:
			self._reset()
			self.mocking._setup(self)
		except AttributeError:
			# An instance of MockAbstractDevice itself.
			AbstractDevice._setup(self)

		if autoconnect:
			self.connect()

		log.info('Created mock device "{0}".'.format(self.name))

	def _reset(self):
		"""
		Reset to a known blank state.
		"""

		# Each mock device has its own mock_state to worry about.
		pass

	def connect(self):
		"""
		Pretend to connect.
		"""

		self._connected()

	def multi_command_start(self):
		"""
		Start buffering responses.
		"""

		self.multi_command_responses = []

	def multi_command_stop(self):
		"""
		Return buffered responses.
		"""

		responses = self.multi_command_responses
		self.multi_command_responses = None

		return responses

	def write(self, message, result=None, done=False):
		"""
		Act on what is being written.
		"""

		log.debug('Writing to device: {0!r}'.format(message))

		if not done:
			if message == '*idn?':
				result = self.name
				done = True
			elif message == '*opc?':
				result = 1
				done = True
			elif message in ['*rst', 'system:preset']:
				self._reset()
				done = True
			elif message == 'system:version?':
				result = '42'
				done = True

		if not done:
			raise NotImplementedError('Cannot understand message: {0!r}'.format(message))

		if result is None:
			self.output = None
		else:
			self.output = str(result) + '\n'

	def read_raw(self, **kwargs):
		"""
		Return the result of the last write operation.
		"""

		log.debug('Read from device: {0!r}'.format(self.output))

		return self.output

	def ask(self, *args, **kwargs):
		"""
		Ask, but possibly buffer the answer.
		"""

		result = AbstractDevice.ask(self, *args, **kwargs)

		if self.multi_command_responses is None:
			return result
		else:
			self.multi_command_responses.append(result)

	def close(self):
		"""
		Pretend to close the connection.
		"""

		log.debug('Closing device: {0}'.format(self.name))

	@property
	def idn(self):
		self.ask('*idn?')

	@property
	def opc(self):
		self.ask('*opc?')
