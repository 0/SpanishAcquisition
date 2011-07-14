# Spanish Acquisition

## Tests

### Unit

Simple unit tests can all be run with

    ./runtests

### Server

Tests which have external dependencies can be found with:

    find . -path '*/tests/server/test_*.py'

and run with, for example:

    ./runtests ./devices/tektronix/tests/server/test_awg5014b.py

## Miscellaneous

A formatted listing of all relevant files can be shown with:

    tree -I '*.pyc|__init__.py' --noreport -F --dirsfirst -C

And only the directories with:

    tree --noreport -F --dirsfirst -C -d
