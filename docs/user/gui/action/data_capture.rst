.. _data_capture:

############
Data capture
############

Data capture panel
******************

The data capture panel controls the verification of the setup, as well as the export of the acquired data.

.. figure:: data_capture_panel.*
   :alt: Data capture panel.

   ..

   1. Begin the sweep as defined in the rest of the application. If there are any setup errors, pressing this button will generate messages about the errors rather than begging the sweep.
   2. If the "Continuous" checkbox is enabled, the sweep will restart from the beginning as soon as it gets to the end.
   3. If the "Export" checkbox is enabled, the sweep values (of both input and output variables) will be exported; otherwise, they will be discarded.
   4. The location of the directory to which the values *should be* exported.
   5. The location of the file to which the last set of values *was* exported.

.. _data_capture_dialog:

Data capture dialog
*******************

The data capture dialog controls the sweep itself.

.. figure:: data_capture_sweep.*
   :alt: Data capture dialog in continuous mode.

   ..

   1. The overall progress of the sweep.
   2. The currently executing stage of the sweep.
   3. The last values set to the output variables.
   4. The last values obtained from the measurements.
   5. The total elapsed time for the sweep. In non-continuous mode, this is accompanied by a rough estimate for the remaining time.
   6. Checkbox controlling the termination of a sweep in continuous mode. At the end of a sweep in continuous mode, if this checkbox is enabled, the sweep terminates; otherwise, it restarts.
   7. Prematurely terminate a sweep.

      .. tip::
         To avoid leaving the system in an inconsistent state, pressing the "Cancel" button first allows whichever stage is currently running to finish running gracefully. Then, if any variables were configured to be set smoothly from their final values to their constant values, they are set smoothly from wherever the sweep was ended. Thus, it is safe to cancel the sweep at any time.

Export format
*************

The export is done to a regular comma-separated values (CSV) file. The first row contains the column headings (potentially with units) as gathered from the variable and measurement names. The first column is always titled "Time (s)" and contains the approximate time of acquisition for each row, relative to the first row of values.

For example, an exported file may begin thusly::

   Time (s),field (mT),port out (V),Pulses (V),port in (V)
   0,1.0,-5.0,"[(0.0, -0.078469520103761514), ...]",-0.0100000004
   0.25141787529,1.0,-4.375,"[(0.0, -0.11684596017395288), ...]",-0.0100000008

Note that the "Pulses" column contains list data and most of it has been omitted here for clarity.
