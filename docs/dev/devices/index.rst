*******
Devices
*******

Interfaces for various hardware devices.

Class hierarchy
===============

All device classes inherit from :class:`~spacq.devices.abstract_device.AbstractDevice`, with their subdevices inheriting from :class:`~spacq.devices.abstract_device.AbstractSubdevice`. Each device class has its own test class, as well as a mock implementation.

.. toctree::
   :maxdepth: 2

   abstract_device

Adding a device
===============

To add a device:

#. In its manufacturer directory [#manuf_dir]_ , add a Python file for its model, named ``model.py`` (eg. ``awg5014b.py``).

   * If no manufacturer directory exists for this manufacturer, create one.

#. In the ``mock`` subdirectory for the manufacturer, add a Python file for the mock implementation, named ``mock_model.py`` (eg. ``mock_awg5014b.py``).

#. Add the new model module and mock model module to the :data:`models` and :data:`mock_models` lists, respectively, in the manufacturer directory ``__init__.py``.

   * Ensure that both lists have the same length. ``None`` is an acceptable value in either list if that implementation is not available.

.. rubric:: Footnotes

.. [#manuf_dir] The manufacturer directories are located in ``spacq/devices/``.
