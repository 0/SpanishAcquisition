###
GUI
###

Tools for providing applications with a graphical user interface.

Class hierarchy
***************

.. toctree::
   :maxdepth: 2

   global_store
   tool_box

The entire GUI framework is built on wxPython, so all widget classes ultimately inherit from a wxPython class, such as :class:`wx.Frame`, :class:`wx.Panel`, or :class:`wx.Dialog`.

The :ref:`global store <gui_global_store>` provides a container for the :mod:`spacq`-related global state for an entire application. It includes separate namespaces for devices, resources, and variables, as well as a single slot for a pulse program.

The :ref:`GUI toolbox <gui_tool_box>` provides several GUI primitives which appear frequently, such as a :class:`~spacq.gui.tool.box.MessageDialog` and functions for saving and loading Python-pickled and CSV files with a graphical dialog. It is recommended to use :class:`~spacq.gui.tool.box.Dialog` rather than :class:`wx.Dialog` directly, in order to simplify disposal.
