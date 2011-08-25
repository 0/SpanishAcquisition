#######################
Pulse program execution
#######################

This section describes the execution of pulse programs on the AWG and oscilloscope.

.. seealso:: :ref:`interface_pulse_programs`

Device initialization
*********************

When a sweep begins, the method :meth:`spacq.iteration.sweep.SweepController.init` is run, which performs several steps, one of which is device initialization. At this point, if a pulse program has been configured, the AWG is disabled and placed into "triggered" mode, and its sampling rate is set to that of the pulse program.

Device utilization
******************

If a pulse program is configured, the method :meth:`spacq.iteration.sweep.SweepController.pulse` is called by :meth:`~spacq.iteration.sweep.SweepController.dwell`. If no output channels have been configured for the AWG (ie. no waveform outputs have been mapped to AWG channels), this stage does nothing. Otherwise, the following sequence of events occurs:

#. The waveforms are generated using the latest values written to the pulse program resources.
#. The AWG is configured:

   #. It is disabled, and its channels are cleared of waveforms.
   #. Each output channel has its waveform loaded.
   #. All used channels are enabled.
   #. The AWG itself is enabled.

#. The oscilloscope is configured:

   #. It is disabled.
   #. If averaging has been requested, it is placed into :ref:`"FastFrame" mode <device_specific_dpo7104_fastframe>` with an average summary frame. Otherwise, "FastFrame" mode is disabled.
   #. It is put into single sequence mode.

#. Execution pauses until the AWG and oscilloscope have both completed carrying out the above steps.
#. The oscilloscope is enabled and a delay of 1 s occurs to allow the oscilloscope trigger to ready.

   .. note::
      The oscilloscope cannot be enabled as part of the above configuration process because the setup procedure of the AWG may trigger the acquisition of an invalid waveform.

#. The trigger loop is executed the specified number of times ("times to average"):

   #. The AWG is triggered.
   #. Execution pauses until the trigger event has executed.
   #. The "post-trigger delay" is waited.

#. Execution pauses until the oscilloscope has finished capturing. This includes performing the averaging if in "FastFrame" mode.
#. The number of acquired frames is verified.
