from unittest import main

from ... import voltage_source
from .. import mock_voltage_source

from ...tests.server.test_voltage_source import VoltageSourceTest


# Don't lose the real device.
real_VoltageSource = voltage_source.VoltageSource
is_mock = VoltageSourceTest.mock


def setup():
	# Run the tests with a fake device.
	voltage_source.VoltageSource = mock_voltage_source.MockVoltageSource
	VoltageSourceTest.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	voltage_source.VoltageSource = real_VoltageSource
	VoltageSourceTest.mock = is_mock


if __name__ == '__main__':
	main()
