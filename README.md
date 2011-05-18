## Tests

### Automated

Automated tests can all be run with `nosetests`.

### Manual

Manual tests can be found with:

    git grep -A1 '@nottest' | grep -v '@nottest'

and run with, for example:

    python -m devices.tektronix.tests.test_awg5014b
