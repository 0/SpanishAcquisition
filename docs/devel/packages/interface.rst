#########
Interface
#########

The interface package contains code for both user-interface and code-interface purposes.

.. _interface_pulse_programs:

Pulse programs
**************

The code for dealing with pulse programs is composed of:

* a parser (:class:`spacq.interface.pulse.parser.Parser`),
* an AST (:class:`spacq.interface.pulse.tree.ASTNode`),
* an environment (:class:`spacq.interface.pulse.tree.Environment`), and
* a presentation wrapper (:class:`spacq.interface.pulse.program.Program`).

The details of pulse program handling are hidden behind the :class:`~spacq.interface.pulse.program.Program` interface, which handles every step of a pulse program's life cycle from parsing to execution.

When presented with the textual representation of a pulse program, the parser does its best to tranform it into an abstract syntax tree; if it cannot do so, it raises a :exc:`spacq.interface.pulse.paser.PulseSyntaxError`.

Once an AST is obtained, an empty :class:`~spacq.interface.pulse.tree.Environment` is created. The nodes of the AST are then visited with the :class:`~spacq.interface.pulse.tree.Environment` over several stages. These stages are:

#. **declarations**:

   * Populate the environment with the variable declarations.
   * Verify that the declarations make sense.

#. **values**:

   * Populate the environment with the value assignments.
   * Verify that the assigned values match the declared variables.

#. **commands**:

   * Verify that all the commands make sense given the collected declarations and values.

#. **waveforms**:

   * Based on all the collected information, generate the output waveforms.

.. warning::
   The order of the stages must be preserved, since each stage makes the assumption that previous stages have been executed.

Resources
*********

Resource
========

:class:`spacq.interface.resources.Resource` is a generic resource with a getter and a setter, each of which can perform arbitrary code in order to get or set a value.

If a resource has units, all operations dealing with the value of the resource should use matching units. In particular, setting the value of a resource with a value whose units do not match those of the resource will raise a :exc:`TypeError`. The display units of a resource, however, have no impact on its values; the display units only affect the value displayed alongside the resource.

If a converter is supplied for a resource, the converter is used to transform user input (textual strings) into the valid type for the resource. Typical converters include :obj:`float` and :obj:`spacq.devices.tools.str_to_bool`. If a resource has units, the user input is automatically converted into a :class:`spacq.interface.units.Quantity`; supplying a converter overrides this behaviour.

A resource may be wrapped with arbitrarily many wrappers. Wrapping and unwrapping are both non-destructive: the original resource is always unmodified, and a new :class:`~spacq.interface.resources.Resource` instance is created. For both getting and setting values, the getter and setter filters are applied in the same order they were added, excluding those which have been removed.

Acquisition Thread
==================

:class:`spacq.interface.resources.AcquisitionThread` is a threaded wrapper around a resource that allows the value of the resource to be fetched at regular intervals. This is particularly useful for live plots which show historical data.

In order to pause the acquisition, :attr:`running_lock` should be acquired from another thread (if no running lock is passed to :obj:`__init__`, pausing is disallowed); to resume, :attr:`running_lock` should be released. In order to stop the thread, :attr:`done` should be set to ``True``.

Units
*****

SIValues
========

:class:`spacq.interface.units.SIValues` is a container for all SI prefixes (from 10\ :sup:`-24` to 10\ :sup:`24`), all SI base units, and a selection of SI derived units.

Quantity
========

:class:`spacq.interface.units.Quantity` is a wrapper around the Python package "quantities". It is used internally (to communicate quantities between objects) and externally (allowing the user to enter arbitrary quantities).

.. note::
   Rather than exposing the :class:`quantities.Quantity` interface, :class:`spacq.interface.units.Quantity` defines its own interface and uses a subset of the :class:`quantities.Quantity` interface internally. Thus, :class:`spacq.interface.units.Quantity` is *not* a drop-in substitude for :class:`quantities.Quantity`.

Waveform generation
*******************

:class:`spacq.interface.waveform.Generator` provides a mechanism for generating :class:`spacq.interface.waveform.Waveform` objects. Each :class:`~spacq.interface.waveform.Generator` will generate a single waveform as its methods are called; after the waveform is complete, it can be obtained via the :attr:`waveform` attribute.

.. note::
   All values should be normalized to the interval [-1.0, 1.0].
