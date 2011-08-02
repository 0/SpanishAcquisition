####################
Device configuration
####################

The device configuration dialog is used to configure :ref:`devices <general_concepts_devices>` for use with an application.

.. _device_config_connection:

Device connection
*****************

.. figure:: device_config_01.*
   :alt: Device configuration.

   ..

   1. Address configuration.

      * Ethernet: The IPv4 address (eg. ``1.2.3.4``).
      * GPIB: The board number, PAD, and SAD.
      * USB: The full USB resource (eg. ``USB::0x1234::0x5678::01234567::RAW``).

   2. Implementation configuration.

      * The manufacturer and model must be selected.
      * Mock: When selected, a software mock implementation is used instead of connecting to a real device.

   3. Connection control.

      * Connect to or disconnect from the device.

   4. Saving settings.

      * All the settings controlled in this dialog (including resource *labels*, but with the exception of resource *values*) can be saved to and loaded from the disk.

.. note::

   Disconnecting from a device does not actually take place until the dialog is confirmed (by pressing "OK"). Thus, pressing "Disconnect" and then "Cancel" will retain the connection to the device.


.. _device_config_resources:

Device resources
****************

.. figure:: device_config_02.*
   :alt: Resource configuration.

   ..

   1. The internal name of the resource.
   2. R/W flags indicating the RO/WO/RW status of the resource.
   3. The unique label used to identify the resource. The label can be changed by double-clicking the appropriate field.
   4. The value of the resource.

      * If the resource is readable, the latest received value is displayed.
      * If the resource is writable, the value can be changed by double-clicking the appropriate field.

   5. A subdevice with resources.
