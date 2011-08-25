###################
General information
###################

The developer is assumed to have read through the :ref:`users_guide` before proceeding.

Testing
*******

All the non-GUI modules in this package have associated tests, found in the ``tests/`` subdirectory. These are split into unit tests (found directly in the subdirectory) and server tests (found in ``tests/server/``); server tests differ from unit tests by the addition of an external dependency, such as a hardware device.

.. note::
   Test failures can signify a missing :ref:`dependency <installation>`. While users can get by with only a subset, it is recommended that developers install *all* dependencies.

Unit tests
==========

The unit tests can all be run with::

   ./runtests

Server tests
============

Currently, only device tests exist in the form of server tests. Before running these, the devices should be connected to the computer and :ref:`configured <devices_testing>`.

Server tests can be found with::

  find ./spacq/ -path '*/tests/server/test_*.py'

and run with, for example::

  ./runtests --no-skip ./spacq/devices/tests/server/test_abstract_device.py

Documentation
*************

Style
=====

An attempt has been made to ensure that the reStructuredText source for this documentation is self-consistent. The following stylistic choices have been made:

* The headings *for each document* are as follows::

     ###
     One
     ###

     Two
     ***

     Three
     =====

     Four
     ----

  Headings nested deeper than this should not be used.

* A single blank line separates elements within a document. Multiple blank lines are not used.

Building
========

The documentation can be built using::

   make -C docs html

This places the result at ``docs/_build/html/index.html``.

Updating
========

It is crucial that all modifications which cause any changes to the user interface, whether they are changes in the GUI or changes in behaviour, are documented in the :ref:`users_guide` as they occur. All changes (especially internal ones not mentioned in the :ref:`users_guide`) should be documented in the :ref:`developers_guide`.

Example applications
********************

The example applications are provided to demonstrate the functionality that this package provides in the form of directly usable and useful applications. As this functionality changes, the example programs should follow suit.

Creating a release
******************

When a new version is ready for release, the version number must be updated in the following places:

* ``docs/conf.py``: ``version``, ``release``
* ``spacq/__init__.py``: ``VERSION``
* ``setup.py``: ``version``

The ``CHANGELOG.rst`` file must be updated with all the important changes from the previous version.

To create a source distribution, run::

   python setup.py sdist
