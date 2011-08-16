from unittest import main

from ... import ips120_10
from .. import mock_ips120_10

from ...tests.server.test_ips120_10 import IPS120_10Test


# Don't lose the real device.
real_IPS120_10 = ips120_10.IPS120_10
is_mock = IPS120_10Test.mock


def setup():
	# Run the tests with a fake device.
	ips120_10.IPS120_10 = mock_ips120_10.MockIPS120_10
	IPS120_10Test.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	ips120_10.IPS120_10 = real_IPS120_10
	IPS120_10Test.mock = is_mock


if __name__ == '__main__':
	main()
