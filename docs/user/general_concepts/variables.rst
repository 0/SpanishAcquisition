.. _general_concepts_variables:

#########
Variables
#########

Variables are how sweeping acquisition experiments are described.

.. _general_concepts_output_variables:

Output variables
****************

Output variables provide a way to sweep over a range of values on a :ref:`resource <general_concepts_resources>`. An output variable will have a customizable range of values over which it iterates.

.. tip::
   The unqualified term "variable" typically refers to output variables.

.. _general_concepts_output_variables_type:

Type
====

An output variable has an associated type. It must be one of:

   Float
      Each produced value is a floating point value, with an integral portion and a decimal portion.

      For example, "-5.5".

   Integer
      Each produced value is an integer value. If any of the generated values contain a decimal portion, it is truncated.

      For example, "5".

   Quantity
      Each produced value is a floating point value with a corresponding unit.

      For example, "12.3 GHz".

Constant value
==============

Each variable is assigned a constant value. By default, this value is ignored; however, there are several options which make use of this value.

For example, if the variable is set to be a "constant variable", then its value is never iterated; instead, its value is set to the constant value at the beginning of a sweep and then left there for the entire duration.

.. note::
   The constant value of a variable always incorporates the :ref:`type and units <general_concepts_output_variables_type>` of the variable.

.. seealso:: :ref:`general_concepts_output_variables_smooth`

Order
=====

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
==============

During a sweep, it is sometimes beneficial to avoid abruptly setting variables to values, since this can correspond to large jumps in current or potential difference in configured devices. To get around this, the variables can optionally be "smoothly set" at various times:

   Smooth setting **from constant** value
      At the start of a sweep, the variable is set to the constant value, and then (over the desired number of steps) swept towards its inital value at the start of the sweep.

   Smooth setting **to constant** value
      At the end of a sweep (even if the sweep is prematurely aborted), the variable is smoothly swept from its final value to its constant value.

   Smooth **transition** between loop iterations
      At the end of a single iteration of an order, if that order was not the slowest-stepping outer loop order, the variable is smoothly swept back to its initial value so that it can be stepped over again.

.. note::
   Each smooth setting step is always 100 ms in duration.

.. seealso:: :ref:`variable_config`

.. _general_concepts_input_variables:

Input variables
***************

Typically referred to as "measurements", input variables provide a way of gathering data from :ref:`resources <general_concepts_resources>`.

There exist two types of measurements: scalar and list. Scalar measurements correspond to the acquisition of single values over time (eg. an amplitude or a frequency); list measurements correspond to the acquisition of a list of values over time (eg. a waveform captured by an oscilloscope). Naturally, if the measurements are done several times, scalar measurements produce one-dimensional data, while list measurements produce two-dimensional data.

.. seealso:: :ref:`measurement_config`
