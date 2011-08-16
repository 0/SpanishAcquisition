from unittest import main

from ... import dpo7104
from .. import mock_dpo7104

from ...tests.server.test_dpo7104 import DPO7104Test


# Don't lose the real device.
real_DPO7104 = dpo7104.DPO7104
is_mock = DPO7104Test.mock


def setup():
	# Run the tests with a fake device.
	dpo7104.DPO7104 = mock_dpo7104.MockDPO7104
	DPO7104Test.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	dpo7104.DPO7104 = real_DPO7104
	DPO7104Test.mock = is_mock


if __name__ == '__main__':
	main()
