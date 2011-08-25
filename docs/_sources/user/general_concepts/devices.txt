.. _general_concepts_devices:

#######
Devices
#######

A device typically refers to a physical piece of hardware, but can be, for example, a piece of software pretending to be hardware.

Devices can offer any number of arbitrary :ref:`resources <general_concepts_resources>`. They may be organized in an hierarchical fashion through :ref:`subdevices <general_concepts_subdevices>`. 

.. tip::
   A device resource will typically correspond to a setting on the device, but it is not required to do so. Other types of resources include measurement readings, and virtual (implementation-specific) settings.

.. _general_concepts_subdevices:

Subdevices
**********

A device which has several versions of the same resources will typically have these resources organized into a tree of subdevices.

For example, an oscilloscope may have multiple input channels, with each having the same set of settings (eg. vertical scaling and offset). These channels may then be viewed as subdevices, and each will have its own values for all its settings.

.. seealso:: :ref:`device_config_resources`

.. _general_concepts_mock_devices:

Mock
****

Mock devices are software simulations of hardware devices. They are typically created at the same time as the device interface and support the same functionality. Most of the time, they are used for testing or as a virtual device.
