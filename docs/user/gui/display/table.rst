.. _tabular_display:

###############
Tabular display
###############

The tabular display panel is a read-only panel for arbitrary data.

.. TODO: Screenshot with all kinds of columns.

Column types
************

The panel is able to recognize certain data types: scalars, lists, and strings. Scalars are any real numbers; lists are number sequences with a particular syntax; and everything else is considered to be a string.

Lists are of the form::

   [(number, number), (number, number), ...]

This is the format used by the :ref:`data_capture` panel for export of list data. Therefore, the exported list data is identified as special by the tabular display panel.
