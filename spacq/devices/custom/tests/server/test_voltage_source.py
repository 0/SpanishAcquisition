import logging
log = logging.getLogger(__name__)

import unittest

from spacq.tests.tool.box import DeviceServerTestCase

from ... import voltage_source


class VoltageSourceTest(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, voltage_source.VoltageSource, 'VoltageSource')

	def testCalibrate(self):
		"""
		Self-calibrate all the ports.
		"""

		vsrc = self.obtain_device()

		for port in vsrc.ports:
			port.apply_settings(calibrate=True)

	def testSetVoltages(self):
		"""
		Set voltages on all the ports.

		Note: Verification should also be done manually based on the voltage source output.
		"""

		vsrc = self.obtain_device()

		test_voltages = list(xrange(-10, 10 + 1, 2)) + list(xrange(5, 0, -1))

		for port, voltage in zip(xrange(16), test_voltages):
			vsrc.ports[port].voltage = voltage


if __name__ == '__main__':
	unittest.main()
