from unittest import main

from ... import smf100a
from .. import mock_smf100a


# Don't lose the real device.
real_SMF100A = smf100a.SMF100A


def setup():
	# Run the tests with a fake device.
	smf100a.SMF100A = mock_smf100a.MockSMF100A

# Run this test class.
from ...tests.server.test_smf100a import SMF100ATest

def teardown():
	# Restore the real device for any remaining tests.
	smf100a.SMF100A = real_SMF100A


if __name__ == '__main__':
	main()
