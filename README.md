## Tests

### Unit

Simple unit tests can all be run with

    ./runtests

### Server

Tests which have external dependencies can be found with:

    find . -path '*/server_tests/test_*.py'

and run with, for example:

    ./runtests ./devices/tektronix/server_tests/test_awg5014b.py

## Miscellaneous

A formatted listing of all relevant files can be shown with:

    tree -C -I '*.pyc|__init__.py' --noreport -F
