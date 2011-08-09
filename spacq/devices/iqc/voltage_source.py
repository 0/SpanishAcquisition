import logging
log = logging.getLogger(__name__)

import numpy
import time

from spacq.interface.resources import Resource
from spacq.interface.units import Quantity
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice, AbstractSubdevice
from ..tools import quantity_unwrapped, BinaryEncoder

"""
Custom voltage source

Control the output voltages on all the ports.
"""


class Port(AbstractSubdevice):
	"""
	An output port on the voltage source.
	"""

	# Since there is no way to determine whether calibration has completed,
	# wait this long and hope for the best.
	calibration_delay = 2 # s

	@staticmethod
	def format_for_dac(msg):
		"""
		Perform some formatting to make the device happy:
			flip all the bits in the message
			pad messages until their length in bytes is a multiple of 4
		"""

		log.debug('Formatting for DAC: {0}'.format(msg))

		msg_encoded = BinaryEncoder.encode(msg)
		# Flip each byte separately.
		msg_flipped = [chr(~ord(x) & 0xff) for x in msg_encoded]

		missing_bytes = (4 - len(msg_encoded) % 4) % 4

		result = BinaryEncoder.decode(msg_flipped + ['\x00'] * missing_bytes)

		log.debug('Formatted for DAC (padded with {0} bytes): {1}'.format(missing_bytes, result))

		return result

	def _setup(self):
		AbstractSubdevice._setup(self)

		# These values are used to tune the input values according to empirical error.
		self.gain = 1.0
		self.offset = 0.0

		# Resources.
		write_only = ['voltage']
		for name in write_only:
			self.resources[name] = Resource(self, None, name)

		self.resources['voltage'].units = 'V'

	@Synchronized()
	def _connected(self):
		AbstractSubdevice._connected(self)

		if self.do_apply_settings:
			self.apply_settings(calibrate=False)

	def __init__(self, device, num, resolution=20, apply_settings=True, min_value=-10,
			max_value=+10, adaptive_filtering=True, calibrate_connected=False,
			fast_settling=True,	freq=100, *args, **kwargs):
		"""
		Initialize the output port.

		device: The VoltageSource to which this Port belongs.
		num: The index of this port.
		resolution: How many bits the output value contains.
		apply_settings: Whether to automatically apply all the settings.
		min_value: Smallest value the port can produce.
		max_value: Largest value the port can produce.
		adaptive_filtering: Enable adaptive filtering.
		calibrate_connected: Do not disconnect output while calibrating.
		fast_settling: Enable fast settling.
		freq: Clock rate in kHz.
		"""

		AbstractSubdevice.__init__(self, device, *args, **kwargs)

		if resolution not in [16, 20]:
			raise ValueError('Unsupported resolution: {0}'.format(resolution))

		self.num = num
		self.resolution = resolution
		self.do_apply_settings = apply_settings
		self.min_value = min_value
		self.max_value = max_value
		self.adaptive_filtering = adaptive_filtering
		self.calibrate_connected = calibrate_connected
		self.fast_settling = fast_settling
		self.freq = freq

	def calculate_voltage(self, voltage):
		"""
		Determine the value corresponding to the given voltage.
		"""

		try:
			voltage_adjusted = voltage * self.gain + self.offset
		except TypeError:
			raise ValueError('Voltage must be a number. Given: {0}'.format(voltage))

		if voltage_adjusted < self.min_value or voltage_adjusted > self.max_value:
			raise ValueError('Adjusted voltage must be within [{0}, {1}]. '
					'Given: {2}; adjusted to: {3}.'.format(self.min_value,
					self.max_value, voltage, voltage_adjusted))

		max_converted = (1 << self.resolution) - 1
		value_span = self.max_value - self.min_value

		# Map [-min_value, max_value] onto [0x0, 0xff...] depending on the resolution.
		# First negate the voltage, so that flipping the bits later will make it correct.
		return int(float(-voltage_adjusted + self.max_value) / value_span * max_converted)

	@Synchronized()
	def write_to_dac(self, message):
		"""
		Write a message to the DAC of the port.

		Voodoo programming follows, thanks to:
			NI's lack of support for anything non-Windows in this case
			my lack of time & desire to properly reverse engineer the ni845x DLL

		If the conversation does not go according to plan, bails out with an AssertionError!
		"""

		message_length = BinaryEncoder.length(message)

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

	def apply_settings(self, calibrate=False):
		"""
		Apply the settings for the DAC on this port.

		calibrate: Run self-calibration on this port as well.

		Note: If self-calibrating, it is essential to wait the calibration_delay after this method returns.
		"""

		flags = ((not self.adaptive_filtering) << 15 |
				self.calibrate_connected << 14 |
				(not self.fast_settling) << 4)

		if calibrate:
			flags |= 0b01

		# Write 16 bits to the top of the DIR: 0010 0100 xx10 0000 101x 00xx
		self.write_to_dac('24 {0:04x}'.format(0x20a0 | flags))

	@quantity_unwrapped('V')
	def set_voltage(self, voltage):
		"""
		Set the voltage on this port, as a quantity in V.
		"""

		# Left-align the bits within the value:
		# 20-bit: VVVV VVVV VVVV VVVV VVVV xxxx
		# 16-bit: VVVV VVVV VVVV VVVV xxxx xxxx
		# where the 'x's are don't-cares, so we just set them to 0 by shifting.
		resulting_voltage = self.calculate_voltage(voltage) << (24 - self.resolution)

		# Write 24 bits to the top of the DIR: 0100 0000 xxxx xxxx xxxx xxxx xxxx xxxx
		self.write_to_dac('40 {0:06x}'.format(resulting_voltage))

	voltage = property(fset=set_voltage)

	@Synchronized()
	def autotune(self, voltage_resource, min_value=None, max_value=None, final_value=0, set_result=True):
		"""
		Take some measured data and solve for the gain and offset.

		voltage_resource: A resource which provides the realtime measured data for this port.
		min_value: Smallest value to take into account.
		max_value: Largest value to take into account.
		final_value: Value to set port to after all measurements are taken.
		set_result: Whether to apply the resulting gain and offset.
		"""

		self.device.status.append('Autotuning port {0}'.format(self.num))

		try:
			if min_value is None:
				min_value = self.min_value
			if max_value is None:
				max_value = self.max_value

			# Test with raw values.
			old_gain, old_offset = self.gain, self.offset
			self.gain, self.offset = 1, 0

			if max_value < min_value:
				raise ValueError('{0} > {1}'.format(min_value, max_value))
			elif max_value == min_value:
				num_points = 1
			else:
				num_points = 21

			# Obtain data.
			real = numpy.linspace(min_value, max_value, num_points)
			measured = []

			for x in real:
				self.voltage = Quantity(x, 'V')
				time.sleep(0.2)
				measured.append(voltage_resource.value.value)

			# Solve.
			A = numpy.vstack([measured, numpy.ones(len(measured))]).T
			gain, offset = numpy.linalg.lstsq(A, real)[0]

			if set_result:
				self.gain, self.offset = gain, offset
			else:
				self.gain, self.offset = old_gain, old_offset

			# Set the voltage after the gain and offset, so that it is potentially more correct.
			self.voltage = Quantity(final_value, 'V')

			return (gain, offset)
		finally:
			self.device.status.pop()


class VoltageSource(AbstractDevice):
	"""
	Interface for the custom voltage source.

	It uses several TI DAC1220 chips and an NI USB-8451 to interface with them over SPI.
	"""

	@property
	def _gui_setup(self):
		try:
			from .gui.voltage_source import VoltageSourceSettingsDialog

			return VoltageSourceSettingsDialog
		except ImportError as e:
			log.debug('Could not load GUI setup for device "{0}": {1}'.format(self.name, str(e)))

			return None

	def _setup(self):
		AbstractDevice._setup(self)

		self.ports = []
		for num in xrange(16):
			port = Port(self, num, **self.port_settings)
			self.ports.append(port)
			self.subdevices['port{0:02}'.format(num)] = port

	def __init__(self, port_settings=None, *args, **kwargs):
		"""
		Initialize the voltage source and all its ports.

		port_settings: A dictionary of values to give to each port upon creation.
		"""

		if port_settings is None:
			self.port_settings = {}
		else:
			self.port_settings = port_settings

		AbstractDevice.__init__(self, *args, **kwargs)

	@Synchronized()
	def ask_encoded(self, msg, assertion=None):
		"""
		Encode and write the message; then read and decode the answer.
		"""

		self.write(BinaryEncoder.encode(msg))
		result = BinaryEncoder.decode(self.read_raw())

		if assertion is not None:
			# Ensure that extra formatting doesn't trigger an assertion failure.
			formatted_assertion = BinaryEncoder.decode(BinaryEncoder.encode(assertion))

			assert result == formatted_assertion, (
					'Device in unknown state; expect general failure. '
					'Asserted: {0}; observed: {1}.'.format(assertion, result))

		return result


name = 'Voltage source'
implementation = VoltageSource
