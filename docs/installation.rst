.. _installation:

############
Installation
############

Installation procedure
**********************

The `latest version available on PyPI`_ can be installed using either::

   sudo pip install SpanishAcquisition

or::

   sudo easy_install SpanishAcquisition

Alternatively, this package can be installed from source in the usual way::

   sudo python setup.py install

.. _`latest version available on PyPI`: http://pypi.python.org/pypi/SpanishAcquisition/

Dependencies
************

These are all the dependencies in use by the package.

If only using a subset of the package, it suffices to use what the subset requires. For example, all the GUI-related dependencies are not necessary if only the device-related code is to be used, and vice versa. However, everything is written in (and so requires) Python 2:

* `Python <http://www.python.org/>`_ ``>=2.6 && <3``

Device drivers
==============

* `NI-VISA <http://www.ni.com/visa/>`_ for Ethernet (and GPIB on Windows) device support.
* `Linux GPIB <http://linux-gpib.sourceforge.net/>`_ (with Python bindings) for GPIB device support.

Python packages
===============

* `Chaco <http://code.enthought.com/chaco/>`_
* `Enable <http://code.enthought.com/projects/enable/>`_
* `matplotlib <http://matplotlib.sourceforge.net/>`_
* `numpy <http://numpy.scipy.org/>`_
* `ObjectListView <http://objectlistview.sourceforge.net/python/>`_
* `pyparsing <http://pyparsing.wikispaces.com/>`_
* `PyPubSub <http://pubsub.sourceforge.net/>`_ ``>= 3.1``
* `PyVISA <http://pyvisa.sourceforge.net/>`_
* `quantities <http://packages.python.org/quantities/>`_
* `scipy <http://www.scipy.org/>`_
* `wxPython <http://www.wxpython.org/>`_

Documentation
-------------

* `Sphinx <http://sphinx.pocoo.org/>`_ ``>= 1.0``

Testing
-------

* `nose <http://somethingaboutorange.com/mrl/projects/nose/>`_
* `nose-testconfig <http://pypi.python.org/pypi/nose-testconfig/>`_
