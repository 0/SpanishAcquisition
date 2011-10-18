###
GUI
###

Tools for providing applications with a graphical user interface.

Class hierarchy
***************

The entire GUI framework is built on wxPython, so all widget classes ultimately inherit from a wxPython class, such as :class:`wx.Frame`, :class:`wx.Panel`, or :class:`wx.Dialog`.

The global store provides :class:`spacq.gui.global_store.GlobalStore`, a container for the :mod:`spacq`-related global state for an entire application. It includes separate namespaces for devices, resources, and variables, as well as a single slot for a pulse program.

The GUI toolbox provides several GUI primitives which appear frequently, such as a :class:`spacq.gui.tool.box.MessageDialog` and functions for saving and loading Python-pickled and CSV files with a graphical dialog.

File structure
**************

The files are laid out in the same fashion as shown in the :ref:`user_gui` section of the :ref:`users_guide`: they are first sorted based on the fundamental type of widget described in the file. Within that, some widgets may be classified futher to restrict them to their own namespace. For example, the plots are found in ``spacq/gui/display/plot/`` rather than just in ``spacq/gui/display/``.

An attempt has been made to keep as much logic as possible out of the GUI code. For example, :class:`spacq.gui.action.data_capture.DataCaptureDialog` only handles the progress widget, user interaction, and error messages; however, it inherits from :class:`spacq.iteration.sweep.SweepController`, which handles all the sweep logic. The former is not easily testable, but the latter is tested in :class:`spacq.iteration.tests.test_sweep.SweepControllerTest`.

Conventions
***********

Dialogs
=======

It is recommended to use :class:`spacq.gui.tool.box.Dialog` rather than :class:`wx.Dialog` directly, in order to simplify disposal. An explanation for the behaviour of :class:`wx.Dialog` exists in the `wxWidgets documentation`_ under "Window deletion overview".

.. _`wxWidgets documentation`: http://docs.wxwidgets.org/2.8/wx_windowdeletionoverview.html

All dialogs should be *modeless* in order to allow the user to interact with several parts of an application simultaneously. It is often necessary to leave a dialog open and switch contexts to another part of the program; that is impossible to achieve with modal dialogs.

Messaging
=========

Due to GUI programming's asynchronous, event-driven nature, it may be difficult to ensure that different parts of a GUI application can communicate with each other in a timely manner. Two methods are utilized for messaging: callbacks and a pub-sub framework.

Callbacks
---------

For uni-directional, ad-hoc communication, callbacks are a simple and obvious choice. Thus, they are used extensively in the GUI code.

For example, let us examine the common case that a dialog is launched and an action is required when the user clicks the OK button. The dialog needs to provide the usual setup for the OK button event handling::

   def __init__(self, parent, ..., *args, **kwargs):
       ...
       self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
       ...

However, the :obj:`OnOk` method cannot contain any logic of its own, since the dialog does not know in which context it was called. All that needs to happen in the event handler is a call to the callback::

   def OnOk(self, evt=None):
       if self.ok_callback(self):
           self.Destroy()

where the :obj:`ok_callback` attribute is either set by :obj:`__init__` or afterwards by the caller. This structure allows the dialog to know whether to exit (depending on the result of the callback), but does not require it to know what happens when the button is pressed.

The event handler logic comes from whoever creates the dialog. For example::

   def OnAction(self, evt=None):
       var = ...

       def ok_callback(dlg):
           try:
               values = dlg.GetValue()
           except ValueError as e:
               MessageDialog(self, str(e), 'Invalid value').Show()
               return False

           var.a, var.b = values

           return True

       dlg = SomeDialog(self, ok_callback)
       dlg.SetValue(var.a, var.b)
       dlg.Show()

.. tip::
   As in the above example, most callbacks make use of the lexical closures that Python provides for nested functions, reducing the number of arguments that need to be passed between GUI objects.

Pub-sub
-------

A publish-subscribe framework is used for events which must be broadcast to multiple listeners.

For example, the :ref:`data_capture` panel and dialog send out ``data_capture.start``, ``data_capture.data``, and ``data_capture.stop`` messages to the global publisher to indicate to anybody who may be listening (there may be zero or more listeners) that certain resources are being acquired. The :ref:`measurement_config` frames listen to whichever resource they are configured, and act accordingly when messages are received.

Subscriptions are made with a call to :obj:`subscribe`::

   pub.subscribe(self.msg_data_capture_start, 'data_capture.start')

Messages are sent with a call to :obj:`sendMessage`::

   pub.sendMessage('data_capture.start', name=name)

.. warning::
   Since the methods associated with the subsciptions for the given topic are run in the same thread as the call to :obj:`sendMessage`, it is necessary to ensure :ref:`thread safety <devel_gui_threads>` when the subscriber may perform GUI actions.

The handler must therefore have parameters which match the message being sent::

   def msg_data_capture_start(self, name):
       ...

.. _devel_gui_threads:

Thread safety
*************

When performing an action which affects the GUI in another thread, it is crucial to use :obj:`wx.CallAfter`. Peforming the action directly, as in::

   self.display_label.SetValue('value')

will cause the GUI event loop to break non-deterministically; depending on the frequency of such calls, the app may freeze or crash within a short time, or may not do so at all. To avoid this, the above example would be rewritten as::

   wx.CallAfter(self.display_label.SetValue, 'value')
