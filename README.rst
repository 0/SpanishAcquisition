*******************
Spanish Acquisition
*******************

Spanish Acquisition is a Python package for interfacing with test & measurement devices (primarily SCPI over Ethernet and GPIB) and building user interfaces for running experiments.

It is released under the FreeBSD (2-clause BSD) license. See the ``LICENSE`` file for details.

Tests
=====

Unit
----

The unit tests can all be run with::

   ./runtests

Server
------

Tests which have external dependencies can be found with::

   find . -path '*/tests/server/test_*.py'

and run with, for example::

   ./runtests --no-skip ./spacq/devices/tektronix/tests/server/test_awg5014b.py
