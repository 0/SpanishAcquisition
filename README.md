# Spanish Acquisition

## Dependencies

### Drivers

* [NI-VISA](http://www.ni.com/visa/)
** For Ethernet device support.
* [Linux GPIB](http://linux-gpib.sourceforge.net/)
** For GPIB device support.

#### Python bindings

* [PyVISA](http://pyvisa.sourceforge.net/)
** `visa` for NI-VISA drivers.
* [Linux GPIB](http://linux-gpib.sourceforge.net/) Python bindings
** `Gpib`, `gpib` for Linux GPIB drivers.

### Python modules

* [numpy](http://numpy.scipy.org/)
* [PyPubSub](http://pubsub.sourceforge.net/) >= 3.1
* [scipy](http://www.scipy.org/)
* [wxPython](http://www.wxpython.org/)

#### Testing

* [nose](http://somethingaboutorange.com/mrl/projects/nose/1.0.0/)
* [nose-testconfig](http://pypi.python.org/pypi/nose-testconfig/)

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
