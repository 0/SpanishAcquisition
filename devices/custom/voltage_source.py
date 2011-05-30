import logging
import string

from devices.abstract_device import AbstractDevice

"""
Custom voltage source

Control the output voltages on all the ports.
"""


log = logging.getLogger(__name__)


class Encoder(object):
	"""
	Utility methods for dealing with binary data encoded for the NI USB-8451.
	"""

	@staticmethod
	def encode(msg):
		"""
		Convert a string of hexadecimal digits to a byte string.
		"""

		log.debug('Encoding to byte string: {0}'.format(msg))

		# Discard non-hexadecimal characters.
		msg_filtered = [x for x in msg if x in string.hexdigits]
		# Grab pairs.
		idxs = xrange(0, len(msg_filtered), 2)
		msg_paired = [''.join(msg_filtered[i:i+2]) for i in idxs]
		# Convert to bytes.
		msg_encoded = ''.join([chr(int(x, 16)) for x in msg_paired])

		log.debug('Encoded to: {0}'.format(msg_encoded))

		return msg_encoded

	@staticmethod
	def decode(msg, pair_size=2, pair_up=True):
		"""
		Convert a byte string to a string of hexadecimal digits.
		"""

		log.debug('Decoding from byte string: {0}'.format(msg))

		# Get the hex string for each byte.
		msg_decoded = ['{0:02x}'.format(ord(x)) for x in msg]

		if pair_up:
			idxs = xrange(0, len(msg_decoded), pair_size)
			msg_formatted = [''.join(msg_decoded[i:i+pair_size]) for i in idxs]

			result = ' '.join(msg_formatted)
		else:
			result = ''.join(msg_decoded)

		log.debug('Decoded to: {0}'.format(result))

		return result

	@staticmethod
	def length(msg):
		"""
		Calculate the number of bytes an unencoded message takes up when encoded.
		"""

		log.debug('Finding encoded length: {0}'.format(msg))

		result = len(Encoder.encode(msg))

		log.debug('Found encoded length: {0}'.format(result))

		return result


class Port(object):
	"""
	An output port on the voltage source.
	"""

	@staticmethod
	def format_for_dac(msg):
		"""
		Perform some formatting to make the device happy:
			flip all the bits in the message
			pad messages until their length in bytes is a multiple of 4
		"""

		log.debug('Formatting for DAC: {0}'.format(msg))

		msg_encoded = Encoder.encode(msg)
		# Flip each byte separately.
		msg_flipped = [chr(~ord(x) & 0xff) for x in msg_encoded]

		missing_bytes = (4 - len(msg_encoded) % 4) % 4

		result = Encoder.decode(msg_flipped + ['\x00'] * missing_bytes)

		log.debug('Formatted for DAC (padded with {0} bytes): {1}'.format(missing_bytes, result))

		return result

	def __init__(self, device, num, resolution=20, adaptive_filtering=True,
			calibrate_connected=False, fast_settling=True, freq=100,
			*args, **kwargs):
		"""
		Initialize the output port.

		device: The VoltageSource to which this Port belongs.
		num: The index of this port.
		resolution: How many bits the output value contains.
		adaptive_filtering: Enable adaptive filtering.
		calibrate_connected: Do not disconnect output while calibrating.
		fast_settling: Enable fast settling.
		freq: Clock rate in kHz.
		"""

		if resolution not in [16, 20]:
			raise ValueError('Unsupported resolution: {0}'.format(resolution))

		self.device = device
		self.num = num
		self.resolution = resolution
		self.adaptive_filtering = adaptive_filtering
		self.calibrate_connected = calibrate_connected
		self.fast_settling = fast_settling
		self.freq = freq

	def calculate_voltage(self, voltage):
		"""
		Determine the value corresponding to the given voltage.
		"""

		try:
			if abs(voltage) > 10:
				raise ValueError('Voltage magnitude must be no greater than 10. Given: {0}'.format(voltage))
		except TypeError:
			raise ValueError('Voltage must be a number. Given: {0}'.format(voltage))

		max_val = (1 << self.resolution) - 1

		# Map [-10, 10] onto [0x0, 0xff...] depending on the resolution.
		# First negate the voltage, so that flipping the bits later will make it correct.
		return int(float(-voltage + 10) / 20 * max_val)

	def write_to_dac(self, message):
		"""
		Write a message to the DAC of the port.

		Voodoo programming follows, thanks to:
			NI's lack of support for anything non-Windows in this case
			my lack of time & desire to properly reverse engineer the ni845x DLL

		If the conversation does not go according to plan, bails out with an AssertionError!
		"""

		message_length = Encoder.length(message)

		if message_length > 4:
			raise ValueError('Message is longer than 4 bytes: {0}'.format(message))

		message_formatted = self.format_for_dac(message)

		# The reply always comes back with as many bits set to 1 as were sent.
		expected_reply = self.format_for_dac('00' * message_length)

		# Lots of assertions so we can bail ASAP to avoid crashing anything.
		self.device.ask_encoded('0000 000c 0008 0100 0000 0000',
				'0000 001c 0018 0100 0000 0002 0200 1000 0100 c001 0100 c000 0002 0000')
		self.device.ask_encoded('0000 0010 000c 0113 0280 0000 0000 ff01',
				'0000 000c 0008 0100 0000 0002')
		self.device.ask_encoded('0000 0010 000c 0112 0280 0000 00ff ff00',
				'0000 000c 0008 0100 0000 0002')
		self.device.ask_encoded('0000 0010 000c 0111 0280 0000 00ff {0:02x} 00'.format(self.num),
				'0000 000c 0008 0100 0000 0002')
		self.device.ask_encoded('0000 000c 0008 0100 0000 0000',
				'0000 001c 0018 0100 0000 0002 0200 1000 0100 c001 0100 c000 0002 0000')
		self.device.ask_encoded('0000 0014 0010 0110 0260 0000 0000 {0:04x} 0700 0000'.format(self.freq),
				'0000 000c 0008 0100 0000 0002')
		self.device.ask_encoded('0000 0014 0010 0111 0260 0000 0003 {0:02x} 00 {1}'.format(message_length,
				message_formatted),
				'0000 0014 0010 0100 0000 0002 {0:02x} 00 0000 {1}'.format(message_length, expected_reply))

	def calibrate(self):
		"""
		Calibrate the DAC on this port.

		Note: It is essential to wait after this method returns until the calibration is done.
		"""

		flags = ((not self.adaptive_filtering) << 15 |
				self.calibrate_connected << 14 |
				(not self.fast_settling) << 4)
		# Write 16 bits to the top of the DIR: 0010 0100 xx10 0000 101x 0001
		self.write_to_dac('24 {0:04x}'.format(0x20a1 | flags))

	def set_voltage(self, voltage):
		"""
		Set the voltage on this port.
		"""

		# Left-align the bits within the value:
		# 20-bit: VVVV VVVV VVVV VVVV VVVV xxxx
		# 16-bit: VVVV VVVV VVVV VVVV xxxx xxxx
		# where the 'x's are don't-cares, so we just set them to 0 by shifting.
		resulting_voltage = self.calculate_voltage(voltage) << (24 - self.resolution)

		# Write 24 bits to the top of the DIR: 0100 0000 xxxx xxxx xxxx xxxx xxxx xxxx
		self.write_to_dac('40 {0:06x}'.format(resulting_voltage))

	voltage = property(fset=set_voltage)


class VoltageSource(AbstractDevice):
	"""
	Interface for the custom voltage source.

	It uses several TI DAC1220 chips and an NI USB-8451 to interface with them over SPI.
	"""

	def setup(self, port_settings):
		self.ports = [Port(self, num, **port_settings) for num in xrange(16)]

	def __init__(self, port_settings=None, *args, **kwargs):
		"""
		Initialize the voltage source and all its ports.

		port_settings: A dictionary of values to give to each port upon creation.
		"""

		if port_settings is None:
			port_settings = {}

		AbstractDevice.__init__(self, *args, **kwargs)

		self.setup(port_settings)

	def ask_encoded(self, msg, assertion=None):
		"""
		Encode and write the message; then read and decode the answer.
		"""

		self.write(Encoder.encode(msg))
		result = Encoder.decode(self.read_raw())

		if assertion is not None:
			# Ensure that extra formatting doesn't trigger an assertion failure.
			formatted_assertion = Encoder.decode(Encoder.encode(assertion))

			assert result == formatted_assertion, (
					'Device in unknown state; expect general failure.'
					'Asserted: {0}; observed: {1}.'.format(assertion, result))

		return result


if __name__ == '__main__':
	import unittest

	import test_voltage_source as my_tests

	unittest.main(module=my_tests)
