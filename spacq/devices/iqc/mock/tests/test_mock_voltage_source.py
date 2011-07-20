from unittest import main

from ... import voltage_source
from .. import mock_voltage_source


# Don't lose the real device.
real_VoltageSource = voltage_source.VoltageSource


def setup():
	# Run the tests with a fake device.
	voltage_source.VoltageSource = mock_voltage_source.MockVoltageSource

# Run this test class.
from ...tests.server.test_voltage_source import VoltageSourceTest

def teardown():
	# Restore the real device for any remaining tests.
	voltage_source.VoltageSource = real_VoltageSource


if __name__ == '__main__':
	main()
