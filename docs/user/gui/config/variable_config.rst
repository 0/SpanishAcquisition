.. _variable_config:

######################
Variable configuration
######################

Variable configuration panel
****************************

The variable configuration panel is used to set up :ref:`output variables <general_concepts_output_variables>` for an application.

.. _variable_config_figure:

.. figure:: variable_config.*
   :alt: Variable configuration.

   ..

   1. The "enabled" checkbox. Variables which do not have this checked (such as **gate 3**) effectively do not exist; this is useful for temporarily disabling variables.
   2. A unique label to identify the variable. This name appears, for example, as a column heading when capturing data.
   3. The order number of variables is used to group them during the sweep. **gate 1** and **gate 4** have the same order, so would be stepped together in the inner loop [#inner_loop_order]_ ; **magnetic field** has a higher order number, and so will be stepped alone in the outer loop.
   4. The resource label for the resource to which to write the values. All the resources provided must be writable. If a resource is not provided (such as with **gate 4**), the variable is still stepped in the usual fashion, but its values are discarded.
   5. The values over which the variable will be stepped. If there are too many values, some are omitted from the display. The symbols on either side of the values specify whether that side is set smoothly: "(" and ")" if smoothly (as for **gate 1**); "[" and "]" if not (as for the other variables).

      If there are any units associated with a variable, they are displayed after the values.
   6. For each step of a variable, after writing the value to the resource, there is a delay of at least the wait time. In each order, the delay for all variables is the longest of the wait times in that order. The effective wait time for **gate 4** is 200 ms.
   7. The "const" checkbox. Variables which have this checked (such as **gate 2**) are considered *constant* and are subject to special consideration in some scenarios.
   8. The const value of a variable is that which it is assumed to take on at rest. The value does nothing on its own, but is used in conjunction with other settings and actions.

      The units associated with a variable apply to the const value as well.
   9. Clicking "Add" creates a blank variables. Clicking "Remove" permanently removes all selected variables.
   10. The variable settings can be saved to and loaded from the disk. All the configured variables (both enabled and not) are saved at the same time, and existing variables are overwritten by any loaded variables.

To select a variable, click on its row. To select multiple variables, hold down the "ctrl" key while clicking. When several variables are selected, some actions (such as clicking "Remove" or pressing the space bar) act on all of them.

Variable sweep example
======================

The configuration shown :ref:`above <variable_config_figure>` would result in the following actions during a sweep:

#. Resource **v1** is smoothly stepped from -2.5 V to -5 V.
#. The values are set (with each being written to the appropriate resource, if any):

   ==============  ========  ======  ======  ========
      Order 2                    Order 1
   --------------  ----------------------------------
   magnetic field   gate 1   gate 2  gate 3   gate 4
   ==============  ========  ======  ======  ========
   0.001 T         -5.0 V    5.6 V   \       -5.0 V
   \               -4.375 V  \       \       -3.75 V
   \               -3.75 V   \       \       -2.5 V
   ...
   --------------------------------------------------
   \               -0.625 V  \       \       3.75 V
   \               0.0 V     \       \       5.0 V
   0.002 T         -5.0 V    \       \       -5.0 V
   \               -4.375 V  \       \       -3.75 V
   \               -3.75 V   \       \       -2.5 V
   ...
   --------------------------------------------------
   \               -0.625 V  \       \       3.75 V
   \               0.0 V     \       \       5.0 V
   0.005 T         -5.0 V    \       \       -5.0 V
   \               -4.375 V  \       \       -3.75 V
   \               -3.75 V   \       \       -2.5 V
   \               -3.125 V  \       \       -1.25 V
   \               -2.5 V    \       \       0.0 V
   \               -1.875 V  \       \       1.25 V
   \               -1.25 V   \       \       2.5 V
   \               -0.625 V  \       \       3.75 V
   \               0.0 V     \       \       5.0 V
   ==============  ========  ======  ======  ========

   Between steps of variables in order 2, if **gate 1** set to smoothly transition, resource **v1** is smoothly stepped from 0.0 V to -5.0 V.

#. Resource **v1** is smoothly stepped from 0 V to -2.5 V.

Variable editor dialog
**********************

The variable editor dialog is used to configure the values over which a variable is stepped. It is opened by double-clicking in the "Values" column of the variable.

.. TODO

.. rubric:: Footnotes

.. [#inner_loop_order] The user interface is organized so that **gate 2** and **gate 3** are still displayed alongside the other variables with order number 1. However, **gate 2** is set to const, and so will be in a separate virtual order, and **gate 3** is disabled, so will not participate at all.
