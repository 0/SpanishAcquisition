#############
Data Explorer
#############

The Data Explorer is an application that allows the user to view arbitrary CSV files, with the option to display some values in graphical form.

.. figure:: data_explorer_menu.*
   :alt: Data explorer with plot menu.

The data explorer is composed of a :ref:`tabular_display` panel, along with a menu to load and plot data. It supports :ref:`data filters <tabular_display_data_filters>`, which can be accessed via ``File -> Filters...``.

Plotting options
****************

Combinations of scalar columns can be plotted in two or three dimensions, with the "Curve...", "Colormapped...", and "Surface..." menu options. These correspond to the :ref:`two_dimensional_plot`, :ref:`colormapped_plot`, and :ref:`surface_plot`.

List columns can be plotted in three dimensions with the "Waveforms..." menu option, which corresponds to the :ref:`surface_plot` in :ref:`surface_plot_waveform`.
