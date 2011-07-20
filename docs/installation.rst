############
Installation
############

Dependencies
============

These are all the dependencies in use by the package.

If only using a subset of the package, it suffices to use what the subset requires. For example, all the GUI-related dependencies are not necessary if only the device-related code is to be used, and vice versa.

Device drivers
--------------

* `NI-VISA <http://www.ni.com/visa/>`_ for Ethernet (and GPIB on Windows) device support.

  * `PyVISA <http://pyvisa.sourceforge.net/>`_

* `Linux GPIB <http://linux-gpib.sourceforge.net/>`_ (with Python bindings) for GPIB device support.

Python modules
--------------

* `Chaco <http://code.enthought.com/chaco/>`_
* `Enable <http://code.enthought.com/projects/enable/>`_
* `matplotlib <http://matplotlib.sourceforge.net/>`_
* `numpy <http://numpy.scipy.org/>`_
* `ObjectListView <http://objectlistview.sourceforge.net/python/>`_
* `PyPubSub <http://pubsub.sourceforge.net/>`_ >= 3.1
* `quantities <http://packages.python.org/quantities/>`_
* `scipy <http://www.scipy.org/>`_
* `wxPython <http://www.wxpython.org/>`_

Python testing modules
----------------------

* `nose <http://somethingaboutorange.com/mrl/projects/nose/>`_
* `nose-testconfig <http://pypi.python.org/pypi/nose-testconfig/>`_