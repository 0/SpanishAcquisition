import unittest

from ... import dpo7104
from .. import mock_dpo7104


# Don't lose the real device.
real_DPO7104 = dpo7104.DPO7104


def setup():
	# Run the tests with a fake device.
	dpo7104.DPO7104 = mock_dpo7104.MockDPO7104

# Run this test class.
from ...tests.server.test_dpo7104 import DPO7104Test

def teardown():
	# Restore the real device for any remaining tests.
	dpo7104.DPO7104 = real_DPO7104


if __name__ == '__main__':
	unittest.main()
