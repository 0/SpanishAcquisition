from unittest import main

from ... import awg5014b
from .. import mock_awg5014b

from ...tests.server.test_awg5014b import AWG5014BTest


# Don't lose the real device.
real_AWG5014B = awg5014b.AWG5014B
is_mock = AWG5014BTest.mock


def setup():
	# Run the tests with a fake device.
	awg5014b.AWG5014B = mock_awg5014b.MockAWG5014B
	AWG5014BTest.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	awg5014b.AWG5014B = real_AWG5014B
	AWG5014BTest.mock = is_mock


if __name__ == '__main__':
	main()
