#######
Devices
#######

Interfaces for various hardware devices.

Class hierarchy
***************

All device classes inherit from :class:`spacq.devices.abstract_device.AbstractDevice`, which provides all the functionality necessary to make connections to physical devices. Subdevices inherit from :class:`spacq.devices.abstract_device.AbstractSubdevice`. Each device class has its own test class, as well as a mock implementation.

:class:`spacq.devices.config.DeviceConfig` and :func:`spacq.devices.config.device_tree` provide a way to find existing devices and connect to them.

.. _devices_testing:

Testing
*******

All the device interfaces can be tested against real hardware as long as the hardware is present and configured.

Configuration of external resources should be done by copying and editing the example file::

   cp test-config.py ~/.spacq-test-config.py

File structure
**************

Each manufacturer has its own directory in ``spacq/devices/`` (eg. ``agilent`` for Agilent, ``tektronix`` for Tektronix, etc), and each of these directories may contain any number of devices. There should be at least four files [#four_files]_ per device:

#. The device interface (eg. ``dm34410a.py``).
#. Tests for the device interface (eg. ``test_dm34410a.py``).
#. A mock implementation of the device (eg. ``mock_dm34410a.py``).
#. A wrapper to run the device tests against the mock (eg. ``test_mock_dm34410a.py``).

.. rubric:: Footnotes

.. [#four_files] Most devices will have four files, but, for example, the IQC voltage source (``iqc/voltage_source.py``) includes a non-server test file (``iqc/tests/test_voltage_source.py``) as a fifth file, and a :ref:`graphical configuration panel <devices_graphical_configuration>` (``iqc/gui/voltage_source.py``) as a sixth file.

Adding a manufacturer
=====================

To add a manufacturer:

#. Copy the sample manufacturer directory (``spacq/devices/sample/``) to a new directory in ``spacq/devices/`` corresponding to the manufacturer. The name of this directory will be the *package name*; it should include only lowercase letters, but starting with the second character may also include digits and underscores.
#. In the ``spacq/devices/<manufacturer>/__init__.py`` file, replace the name with the name of the manufacturer as you would like it to appear in the user interface.
#. Add the new package name to both lines of ``spacq/devices/__init__.py``.

For example, to add Oxford Instruments as a manufacturer::

   cp -r spacq/devices/sample spacq/devices/oxford
   vim spacq/devices/oxford/__init__.py # Change the name to "Oxford Instruments".
   vim spacq/devices/__init__.py # Add "oxford".

Adding a device
===============

The sample manufacturer comes with a sample device in the form of files ending in ``abc1234.py``. If the manufacturer is newly added, you should modify this sample device; otherwise, copy the four sample device files over from ``spacq/devices/sample/``.

#. Rename all the ``abc1234.py`` files to something suitable for the device. The chosen name (excluding the ``.py`` extension) will be the *module name*; it should include only lowercase letters, but can also include digits and underscores starting with the second character.

   .. note::
      Due to the constraint that the initial character of the module name may not be a digit, some model names cannot be used directly either in the module name or in the class name. For example, in the case of the Agilent 34410A, the module name is ``dm34410a`` and the class name is ``DM34410A`` where the letters "DM" are arbitrarily chosen and stand for "digital multimeter".

#. Add the configuration details for the physical device to your :ref:`test configuration <devices_testing>`.
#. Edit the mock tests (``spacq/devices/<manufacturer>/mock/tests/test_mock_<model>.py``) to refer to the correct tests.
#. Edit the server [#server_tests]_ tests (``spacq/devices/<manufacturer>/tests/server/test_<model>.py``) to use *all* the functionality the interface will include.
#. Edit the device interface (``spacq/devices/<manufacturer>/<model>.py``) until all the server tests pass.
#. Edit the mock implementation (``spacq/devices/<manufacturer>/<model>.py``) until all the mock tests pass.
#. Add the new model module and mock model module to the :data:`models` and :data:`mock_models` lists, respectively, in the manufacturer directory ``__init__.py``, as well as to the import lines.

   .. warning::
      Ensure that both lists have the same length. ``None`` is an acceptable value in either list if that implementation is not available.

.. rubric:: Footnotes

.. [#server_tests] They are referred to as "server" tests because they have an external dependency (the hardware device) which acts roughly as a server to which the tests connect.

.. _devices_graphical_configuration:

Synchronization
***************

To allow for consistent state while performing device commands, each device contains a re-entrant lock. Every read and write operation acquires this lock; thus, multiple reads and writes are mutually excluded. In order to provide a similar mechanism for user-defined methods, the :class:`spacq.tool.box.Synchronized` decorator can be used. This decorator will acquire the device lock, ensuring that other concurrently-executing threads cannot do the same, and that the atomicity of the decorated method is guaranteed for a given device instance.

Graphical configuration
***********************

In the case that a device requires a graphical configuration panel, one can be added in the form of a non-modal wxPython dialog (inherited from :class:`~spacq.gui.tool.box.Dialog`). The dialog should reside in ``spacq/devices/<manufacturer>/gui/<model>.py``, and its constructor must take the following arguments, in order:

#. The parent window.
#. The global store.
#. The device name as used in the global store.

The latter two values allow the dialog to find a reference to the device object itself.

In order to announce that a GUI configuration panel is available, the device class (child of :class:`~spacq.devices.abstract_device.AbstractDevice`) must have a ``_gui_setup`` property which follows the following template::

   @property
   def _gui_setup(self):
       try:
           from .gui.model import ModelSettingsDialog

           return ModelSettingsDialog
       except ImportError as e:
           log.debug('Could not load GUI setup for device "{0}": {1}'.format(self.name, str(e)))

           return None
