# Spanish Acquisition

## Tests

### Unit

Simple unit tests can all be run with

    ./runtests

### Server

Tests which have external dependencies can be found with:

    find . -path '*/tests/server/test_*.py'

and run with, for example:

    ./runtests --no-skip ./spacq/devices/tektronix/tests/server/test_awg5014b.py
