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

.. TODO: Variable order.
   TODO: Smooth setting, transitions.
   TODO: Constant.

.. seealso:: :ref:`variable_config`

.. _general_concepts_input_variables:

Input variables
===============

Typically referred to as "measurements", input variables provide a way of gathering data from :ref:`resources <general_concepts_resources>`.
