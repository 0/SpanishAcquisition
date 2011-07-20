from unittest import main

from ... import dm34410a
from .. import mock_dm34410a


# Don't lose the real device.
real_DM34410A = dm34410a.DM34410A


def setup():
	# Run the tests with a fake device.
	dm34410a.DM34410A = mock_dm34410a.MockDM34410A

# Run this test class.
from ...tests.server.test_dm34410a import DM34410ATest

def teardown():
	# Restore the real device for any remaining tests.
	dm34410a.DM34410A = real_DM34410A


if __name__ == '__main__':
	main()
