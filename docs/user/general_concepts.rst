****************
General concepts
****************

Everything tangible (devices, variables) in this package is tied together via resources.

Devices
=======

A device typically refers to a physical piece of hardware, but can be, for example, a piece of software pretending to be hardware. 

Resources
=========

Resources provide a way of interacting with devices in a generic way. They can be read-only (RO), write-only (WO), or read-write (RW).

In the typical case, a device (eg. a multimeter) will provide several resources; there may be some RW resources (eg. integration time, auto-zero setting), and some RO ones (eg. measurement reading). WO resources are possible, but atypical.

These provided resources can be given arbitrary labels, and these labels are used elsewhere to identify the resources. For example, given two RW resources with labels "reading" and "gate", one can set up a variable which writes to the resource labelled "gate" and a measurement which reads from the resource labelled "reading".

.. note::

   Resources linked to variables must be of the correct type: output variables can only be used with WO and RW resources; input variables can only be used with RO and RW resources.

Variables
=========

Variables are how sweeping acquisition experiments are described.

Output variables
----------------

Output variables provide a way to sweep over a range of values on a resource. An output variable will have a customizable range of values over which it iterates.

.. note::

   The unqualified term "variable" typically refers to output variables.

Input variables
---------------

Typically referred to as "measurements", input variables provide a way of gathering data from resources.
