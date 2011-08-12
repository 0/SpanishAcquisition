################
General concepts
################

Everything tangible (:ref:`devices <general_concepts_devices>`, :ref:`variables<general_concepts_variables>`) in this package is tied together via :ref:`resources <general_concepts_resources>`.

.. _general_concepts_devices:

Devices
*******

A device typically refers to a physical piece of hardware, but can be, for example, a piece of software pretending to be hardware.

Devices can offer any number of arbitrary :ref:`resources <general_concepts_resources>`. They may be organized in an hierarchical fashion through :ref:`subdevices <general_concepts_subdevices>`. 

.. note::

   A device resource will typically correspond to a setting on the device, but it is not required to do so. Other types of resources include measurement readings, and virtual (implementation-specific) settings.

.. _general_concepts_subdevices:

Subdevices
==========

A device which has several versions of the same :ref:`resources <general_concepts_resources>` can organize these resources into a tree of subdevices.

For example, an oscilloscope may have multiple channels, with each having the same set of settings. These channels may then be viewed as subdevices, each having its own settings.

.. seealso:: :ref:`device_config_resources`

.. _general_concepts_resources:

Resources
*********

Resources provide a way of interacting with :ref:`devices <general_concepts_devices>` in a generic way. They can be read-only (RO), write-only (WO), or read-write (RW). RO and RW resources are considered *readable*; WO and RW resources are considered *writable*.

In the typical case, a :ref:`device <general_concepts_devices>` (eg. a multimeter) will provide several resources; there may be some RW resources (eg. integration time, auto-zero setting), and some RO ones (eg. measurement reading). WO resources are possible, but atypical.

These provided resources can be given arbitrary labels, and these labels are used elsewhere to identify the resources. For example, given two RW resources with labels "reading" and "gate", one can set up a variable which writes to the resource labelled "gate" and a measurement which reads from the resource labelled "reading".

.. note::

   Resources linked to variables must be of the correct type: :ref:`output variables <general_concepts_output_variables>` can only be used with writable resources; :ref:`input variables <general_concepts_input_variables>` can only be used with readable resources.

Resources may also have units associated with them, in which case the value read from or written to that resource must be a quantity with a matching dimensionality. That is, a resource which requires acceleration in meters per second squared (specified as ``m.s-2``) will accept millimeters per second squared (``mm.s-2``) and joules per newton per second squared (``J.N-1.s-2``), but not joules per newton (``J.N-1``) or joules per second squared (``J.s-2``).

.. _general_concepts_variables:

Variables
*********

Variables are how sweeping acquisition experiments are described.

.. _general_concepts_output_variables:

Output variables
================

Output variables provide a way to sweep over a range of values on a :ref:`resource <general_concepts_resources>`. An output variable will have a customizable range of values over which it iterates.

.. note::

   The unqualified term "variable" typically refers to output variables.

Constant value
--------------

Each variable is assigned a constant value. By default, this value is ignored; however, there are several options which make use of this value.

For example, if the variable is set to be a "constant variable", then its value is never iterated; instead, its value is set to the constant value at the beginning of a sweep and then left there for the entire duration.

.. seealso:: :ref:`general_concepts_output_variables_smooth`

Order
-----

Each output variable has an order to which it belongs, defined by an integer value (either negative, zero, or positive). This order is used to determine the looping sequence for variable iteration and has no bearing on the values of the variable.

Variables which share the same order value are stepped together. Variables which have a greater order value are stepped more slowly (ie. they are on an outer loop of the iteration) relative to those which have a lesser order value.

.. warning::

   In a single order, whichever variable has fewest values dictates how many values the other variables will have. Any excess values for the longer variables are silently truncated.

For example, if variables ``A``, ``B``, ``C``, and ``D`` have orders of -5, 1, 1, and 10, respectively, then:

* ``D`` will iterate most slowly
* ``B`` and ``C`` will iterate in lockstep, between ``D`` and ``A``
* ``A`` will iterate most quickly

Note that since constant variables by definition do not iterate, they are all put into a separate virtual order, and so are ignored from the point of view of the ordering discussion.

.. _general_concepts_output_variables_smooth:

Smooth setting
--------------

During a sweep, it is sometimes beneficial to avoid abruptly setting variables to values, since this can correspond to large jumps in current or potential difference in configured devices. To get around this, the variables can optionally be "smoothly set" at various times:

* Smooth setting **from constant** value:

  At the start of a sweep, the variable is set to the constant value, and then (over the desired number of steps) swept towards its inital value at the start of the sweep.

* Smooth setting **to constant** value:

  At the end of a sweep (even if the sweep is prematurely aborted), the variable is smoothly swept from its final value to its constant value.

* Smooth **transition** between loop iterations:

  At the end of a single iteration of an order, if that order was not the slowest-stepping outer loop order, the variable is smoothly swept back to its initial value so that it can be stepped over again.

.. note::

   Each smooth setting step is always 100 ms in duration.

.. seealso:: :ref:`variable_config`

.. _general_concepts_input_variables:

Input variables
===============

Typically referred to as "measurements", input variables provide a way of gathering data from :ref:`resources <general_concepts_resources>`.

There exist two types of measurements: scalar and list. Scalar measurements correspond to the acquisition of single values over time (eg. an amplitude or a frequency); list measurements correspond to the acquisition of a list of values over time (eg. a waveform captured by an oscilloscope). Naturally, if the measurements are done several times, scalar measurements produce one-dimensional data, while list measurements produce two-dimensional data.

.. seealso:: :ref:`measurement_config`
