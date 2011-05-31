from nose.plugins.skip import SkipTest
import unittest

from testconfig import config

from devices.custom import voltage_source


class VoltageSourceTest(unittest.TestCase):
	def __obtain_device(self):
		"""
		Try to get a handle for a physical device.
		"""

		all_devices = config['devices'].items()
		potential_addresses = [a for (n, a) in all_devices if n.startswith('VoltageSource.')]

		for address in potential_addresses:
			try:
				return voltage_source.VoltageSource(**address)
			except Exception:
				pass

		raise SkipTest('Could not connect to device.')

	def testCalibrate(self):
		"""
		Self-calibrate all the ports.
		"""

		vsrc = self.__obtain_device()

		for port in vsrc.ports:
			port.apply_settings(calibrate=True)

	def testSetVoltages(self):
		"""
		Set voltages on all the ports.

		Note: Verification should also be done manually based on the voltage source output.
		"""

		vsrc = self.__obtain_device()

		test_voltages = list(xrange(-10, 10 + 1, 2)) + list(xrange(5, 0, -1))

		for port, voltage in zip(xrange(16), test_voltages):
			vsrc.ports[port].voltage = voltage


if __name__ == '__main__':
	unittest.main()
