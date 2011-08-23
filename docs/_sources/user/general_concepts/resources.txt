.. _general_concepts_resources:

#########
Resources
#########

Resources provide a way of interacting with :ref:`devices <general_concepts_devices>` and :ref:`pulse programs <pulse_programs>` in a generic way. They can be read-only (RO), write-only (WO), or read-write (RW). RO and RW resources are considered *readable*; WO and RW resources are considered *writable*.

In the typical case, a device (eg. a multimeter) will provide several resources; there may be some RW resources (eg. integration time, auto-zero setting), and some RO ones (eg. measurement reading). WO resources are possible (and are commonly found as pulse program resources), but are atypical among devices.

These provided resources may be given arbitrary labels, and these labels are used elsewhere to identify the resources. For example, given two RW resources with labels "reading" and "gate", one can set up a variable which writes to the resource labelled "gate" and a measurement which reads from the resource labelled "reading".

.. note::
   Resources linked to variables must be of the correct type: :ref:`output variables <general_concepts_output_variables>` shall only be used with writable resources; :ref:`input variables <general_concepts_input_variables>` shall only be used with readable resources.

Resources may also have associated units, in which case the value read from or written to that resource must be a quantity with a matching dimensionality. That is, a resource which requires acceleration in meters per second squared (specified as ``m.s-2``) will accept millimeters per second squared (``mm.s-2``) and joules per newton per second squared (``J.N-1.s-2``), but not joules per newton (``J.N-1``) or joules per second squared (``J.s-2``).
