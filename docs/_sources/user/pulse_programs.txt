.. _pulse_programs:

##############
Pulse programs
##############

Pulse programs are an unambiguous way to describe the parameterizable shape of one or more parallel waveforms. Pulse programs allow for:

* **Adjustable time scales.** Waveforms can be on the order of nanoseconds, of seconds, or anything in between.
* **Arbitrary parameterization.** Delays, pulse amplitudes and length, and repetition counts can all be iterated over.
* **Arbitrary waveforms.** Any discretized waveform can be inserted.
* **External trigger.** An oscilloscope acquisition can be triggered at any point during the waveforms.
* **Nested looping.** Complex, repetitive waveforms can be created easily.

Variables
*********

In order to allow parameterization, any values which can be directly used (such as integers or delays) can alternatively be used with a variable. Some values (such as pulses and outputs) require the use of a variable.

Types
=====

Pulse programs can contain the following variable types:

   **Integer** (``int``)
      A single integer value, such as 12 or -5.

   **Delay** (``delay``)
      A single time quantity, such as 5.5 ns.

   **Pulse** (``pulse``)
      A collection of three values set using a dictionary or attributes:

      * **amplitude**: A voltage quantity, such as 250 mV.
      * **length**: A time quantity.
      * **shape**: A string containing a valid file name.

   **Output** (``output``)
      A special type which does not support assignment. Outputs are always configured when the pulse program is to be used.

Dictionaries
============

Any variables which are collections of values can have several of their values assigned via a dictionary. Dictionaries are of the form ``{<key>: <value>, ...}`` where the keys must correspond to the attribute names of the variable being assigned to. For example::

   # A valid dictionary assigned to a pulse:
   p1 = {amplitude: -0.5 V, length: 0.5 us, shape: 'square'}

   # Not all attributes need be present:
   p2 = {shape: 'non-square'}

.. _pulse_programs_attributes:

Attributes
==========

Any variables which are collections of values can have a single value assigned via an attribute. For example::

   # Assignment to a pulse attribute:
   p3.amplitude = -500 mV

Program syntax
**************

A pulse program consists of several statements separated by line breaks or semicolons (``;``). A statement is one of:

   **Assignment**
      An assignment sets the value of a variable or attribute. Any variable or attribute may only be assigned to once in a single program. For example::

         p1 = {shape: 'square', length: 1 ns, amplitude: 1 V}
         d1 = 100 ns
         loops = 5

   **Declaration**
      A declaration is an announcement of intent to use a variable; all used variables must be declared at some point in the program. A declaration consists of a type, followed by one or more identifiers; any identifier may also be part of an assignment within the declaration. For example::

         int bumps = 2
         delay bump_spacing = 20 ns, settle, end_delay

   **Command**
      A command is an instruction that dictates the shape of the resulting waveforms. There exist several kinds of commands:

      * **Delay**: A lone identifier or a single time value causes a delay in all output waveforms. For example::

           # Pause all waveforms for the length of delay d1:
           d1

           # Pause all waveforms for 100 ns:
           100 ns

      * **Pulse sequence**: Statements of the form ``([delay|pulse] [delay|pulse] ...):<output>`` are treated as waveform-generating command. If there is only a single delay or pulse, the parentheses may be omitted. If several pulse sequences are included in the same statement, they are executed in parallel; otherwise they are executed in series. For example::

           # Generate delay or pulse x on ouput f1:
           x:f1
           # Alternatively:
           (x):f1

           # Generate delay or pulse x, followed by a 10 ns delay, followed by
           # another instance of delay or pulse x, all in sequence on output f2:
           (x 10 ns x):f2

           # Generate identical simultaneous waveforms on outputs f1 and f2:
           (x d1 y):f1 (x d1 y):f2

           # Generate different simultaneous waveforms on outputs f1, f2, and f3:
           x:f1 (x y):f2 y:f3

           # Same output shapes as above, but the waveforms on the different outputs
           # follow one another in time:
           x:f1
           (x y):f2
           y:f3
           # Alternatively:
           x:f1 ; (x y):f2 ; y:f3

        .. note::
           All waveforms are synchronized before and after a pulse sequence. If any pulse sequence would be longer than the others, padding delays are automatically added to the end of the shorter sequences to ensure that all the lengths match.

      * **Acquisition trigger**: A statement of the form ``acquire`` signals that an oscilloscope acquisition trigger must occur on an output at that point. Such triggers are always created on output markers, rather than as part of the output waveform itself.

   **Loop**
      A loop is a section of the program which is to be executed several times. The contents of a loop block are constrained to delays, pulse sequences, and loops. Loops are of the form::

         times <integer> {
            <statement>
            ...
         }

Comments
========

Any text after (and including) a ``#`` character is ignored. For example::

   # This is a pulse sequence.
   (p1 d1 p1):f1 # (p2 d2 p2):f2

is identical to::

   (p1 d1 p1):f1

Parameterization
****************

Any values which are not assigned in the body of the pulse program must be filled in at a later time. For example::

   pulse p1 = {amplitude: 1 V, shape: 'square'}
   output f1

   p1:f1

is the entirety of valid pulse program, but **p1.length** is treated as an external parameter and must be known in order to generate the waveform for output **f1**.

It it possible to fill these values in dynamically as part of a sweep, given that the parameters are assigned resource labels.

.. seealso:: :ref:`pulse_program_configuration`

Examples
********

The following examples all use a sampling rate of 1 GHz.

Single waveform
===============

::

   delay d1 = 5 ns
   int bumps
   pulse p1 = {amplitude: 1 V, shape: 'square'}
   output f1

   p1.length = 10 ns

   3 ns
   p1:f1

   times bumps {
       d1
       (p1 1 ns p1):f1
   }

If the parameter **bumps** is filled in with the value **3**, the following waveform is generated:

.. figure:: pulse_programs_single.*
   :alt: Single waveform.

Multiple waveforms
==================

::

   pulse p1 = {amplitude: 0.5 V, length: 10 ns, shape: 'non-square'}
   pulse p2 = {amplitude: -1.5 V, length: 5 ns, shape: 'non-square'}
   output f1, f2

   1 ns
   p1:f1
   1 ns
   (p1 2 ns p1):f1 (p2 3 ns p2):f2
   5 ns
   p2:f2
   8 ns

If the file "non-square" contains the data "-0.1, 0.0, 0.1, 0.2, 0.4, 0.8, 1.6", the following pair of waveforms is generated:

.. figure:: pulse_programs_multiple_01.*
   :alt: One of multiple waveforms.

.. figure:: pulse_programs_multiple_02.*
   :alt: Another of multiple waveforms.

With acquisition
================

::

   pulse p1 = {amplitude: 0.25 V, length: 15 ns, shape: 'square'}
   output markered

   20 ns
   p1:markered
   acquire
   p1:markered
   20 ns

If the acquisition marker is set up to be marker **2** on output **markered**, the following output waveform and marker waveform are generated:

.. figure:: pulse_programs_acquisition.*
   :alt: A waveform with an acquisition trigger.
