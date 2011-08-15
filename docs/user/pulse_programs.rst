##############
Pulse programs
##############

Pulse programs are an unambiguous way to describe the parameterizable shape of one or more parallel waveforms. Pulse programs allow for:

* **Adjustable time scales.** On the order of nanoseconds, of seconds, or anything in between.
* **Arbitrary parameterization.** Delays, pulse amplitudes and length, and repetition counts can all be iterated over.
* **Arbitrary waveforms.** If it's discrete, it can be inserted.
* **External trigger.** To trigger an oscilloscope acquisition at any point during the waveforms.
* **Nested looping.** For complex, repetitive waveforms.

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

   # A valid dictionary to be assigned to a pulse:
   {amplitude: -0.5 V, length: 0.5 us, shape: 'square'}

   # Not all attributes must be present:
   {shape: 'non-square'}

Attributes
==========

Any variables which are collections of values can have a single value assigned via an attribute. For example::

   # Assignment to a pulse attribute:
   p1.amplitude = -500 mV

Program syntax
**************

A pulse program consists of several statements separated by line breaks or semicolons (``;``). Each statement can be one of:

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

      * **delay**: A lone identifier or a single time value causes a delay in all output waveforms. For example::

           # Pause all waveforms for the length of delay d1:
           d1

           # Pause all waveforms for 100 ns:
           100 ns

      * **pulse sequence**: Statements of the form ``([delay|pulse] [delay|pulse] ...):<output>`` are treated as waveform-generating command. If there is only a single delay or pulse, the parentheses may be omitted. If several pulse sequences are included in the same statement, they are executed in parallel; otherwise they are executed in series. For example::

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

      * **acquisition trigger**: A statement of the form ``acquire`` signals that an oscilloscope acquisition trigger must occur on an output at that point. Such triggers are always created on output markers, rather than as part of the output waveform itself.

   **Loop**
      A loop is a section of the program which is to be executed several times. The contents of a loop block are constrained to non-trigger commands and loops.

Comments
========

Any text after (and including) a ``#`` character is entirely ignored. For example::

   # This is a pulse sequence.
   (p1 d1 p1):f1 # (p2 d2 p2):f2

is completely identical to::

   (p1 d1 p1):f1

Examples
********

Single waveform
===============

.. TODO

Multiple waveforms
==================

.. TODO

With acquisition
================

.. TODO
