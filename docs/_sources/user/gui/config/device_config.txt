.. _device_config:

####################
Device configuration
####################

.. _device_config_list:

Device list
***********

The device list shows all the :ref:`devices <general_concepts_devices>` configured in an application.

.. figure:: device_config_list.*
   :alt: Device list.

   ..

   1. A unique label to identify the device.
   2. The connection status. Double-clicking in this column brings up the device configuration dialog for the device.
   3. Graphical configuration. If a device has this option, "Setup..." appears in this column; double-clicking it opens up the device-specific graphical configuration.
   4. The status of any long-running tasks.
   5. Clicking "Add" creates a blank device. Clicking "Remove" permanently removes all selected devices.

Device configuration dialog
***************************

The device configuration dialog is used to configure an individual :ref:`device <general_concepts_devices>` for use with an application.

.. _device_config_connection:

Device connection
=================

Connection and model setup.

.. figure:: device_config_connection.*
   :alt: Device connection configuration.

   ..

   1. Address configuration.

      * Ethernet: The IPv4 address (eg. ``1.2.3.4``).
      * GPIB: The board number, PAD, and SAD.
      * USB: The full USB resource (eg. ``USB::0x1234::0x5678::01234567::RAW``).

   2. Implementation configuration.

      * The manufacturer and model must be selected.
      * When "Mock" is selected, a :ref:`software mock implementation <general_concepts_mock_devices>` is used instead of connecting to a real device.

   3. Connection control.

      * Connect to or disconnect from the device.

   4. Saving settings.

      * All the settings controlled in this dialog (including resource *labels*, but with the exception of resource *values*) can be saved to and loaded from the disk.

.. note::
   Disconnecting from a device does not actually take place until the dialog is confirmed (by pressing "OK"). Thus, pressing "Disconnect" and then "Cancel" will retain the connection to the device.

.. _device_config_resources:

Device resources
================

Resource labels and values setup.

.. figure:: device_config_resources.*
   :alt: Device resource configuration.

   ..

   1. The internal name of the resource.
   2. R/W flags indicating the RO/WO/RW status of the resource.
   3. The units associated with the resource.
   4. The unique label used to identify the resource. The label can be changed by double-clicking the appropriate field.

      In this case, the channel 1 waveform has been given the label **osc1**.
   5. The value of the resource.

      * If the resource is readable, the latest received value is displayed. The exception to this is slow resources, which always have "[N/A]" displayed to avoid slowdowns caused by fetching the value.
      * If the resource is writable, the value can be changed by double-clicking the appropriate field.

   6. A subdevice with its own resources.
