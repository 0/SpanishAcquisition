from unittest import main

from ... import abc1234
from .. import mock_abc1234


# Don't lose the real device.
real_ABC1234 = abc1234.ABC1234


def setup():
	# Run the tests with a fake device.
	abc1234.ABC1234 = mock_abc1234.MockABC1234

# Run this test class.
from ...tests.server.test_abc1234 import ABC1234Test

def teardown():
	# Restore the real device for any remaining tests.
	abc1234.ABC1234 = real_ABC1234


if __name__ == '__main__':
	main()
