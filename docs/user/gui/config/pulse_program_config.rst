.. _pulse_program_configuration:

###########################
Pulse program configuration
###########################

The pulse program configuration panel is used to set up the :ref:`pulse program <pulse_programs>` for an application.

If a pulse program is loaded (via ``File -> Open...`` or Ctrl+O), the sweep performed by the :ref:`data_capture_dialog` will include a stage involving the pulse program. If it is later closed (via ``File -> Close`` or Ctrl+W) or if one was not opened, the corresponding sweep stage is skipped.

.. note::
   To run a pulse program, it is necessary to have configured both an AWG (to emit the waveforms) and an oscilloscope (to take measurements).

Resources
*********

Most parameterizable values of a pulse program may be given :ref:`resource labels <general_concepts_resources>`. These resource labels behave the same way as device resources, and so may be iterated over by a variable during a sweep.

Setup
*****

.. tip::
   Each setup tab is present only if the pulse program requires it. For example, the Acquisition tab appears only if the command ``acquire`` is in the program.

Acquisition
===========

Configuration for the acquisition trigger.

.. figure:: pulse_program_config_acquisition.*
   :alt: Pulse program configuration: acquisition.

* marker_num: The number of the marker of the AWG channel output used for the trigger.
* output: The waveform output name.
* Times to average: If this item is set to a value greater than 1, the oscilloscope is placed into "average" mode for the given number of waveforms, and the AWG is triggered that many times.
* Post-trigger delay: How long to wait after triggering the AWG. This delay occurs between individual waveforms when averaging.

Delays, Integers, Pulses
========================

Configuration for the pulse program variables.

.. figure:: pulse_program_config_delays.*
   :alt: Pulse program configuration: delays.

Delays, integers, and pulses are all configured in approximately the same manner, and most of their aspects can be parameterized.

All items (for delays and integers, the variables themselves; for pulses, the variable :ref:`attributes <pulse_programs_attributes>`) appear exactly as they are named in the pulse program. Each must have a default value, and may also have an optional resource label.

The default value is used when displaying the output waveform in the Outputs tab, and when sending the waveform to the AWG given that either no resource label is provided or no value is written to the resource during the sweep.

Outputs
=======

Configuration for the waveform outputs.

.. figure:: pulse_program_config_outputs.*
   :alt: Pulse program configuration: outputs.

* Outputs: All the output waveforms in the program are listed, and can be viewed by clicking the "View" button. If a channel number is specified, the waveform generated is output on that channel of the AWG.
* Sampling rate: The waveforms are generated with this sampling rate. The AWG automatically has its output frequency set to this value.
* Devices: The device label (as specified in the :ref:`device_config_list`) must be provided for each device.

.. warning::
   Setting the sampling rate too low will produce waveforms which are not faithful to the pulse program, since there is not enough resolution to create the desired shapes. On the other hand, setting the sampling rate too high will produce waveforms that have very many points, causing severe slowdowns.

   A good rule of thumb is to keep the waveforms to within one million points. This provides a maximum total duration of 1 ms per waveform at a resolution of 1 GHz.
