#########
Iteration
#########

Tools for iterating; the core of the logic behind sweeping.

File structure
**************

The package consists of only two modules: :mod:`spacq.iteration.sweep` which contains :class:`~spacq.iteration.sweep.SweepController`, and :mod:`spacq.iteration.variables` which defines input and output variables. Together, these modules can be used to provide iteration over a set of variables.

Sweeping
********

:class:`spacq.iteration.sweep.SweepController` goes through a process of several stages, as crudely drawn in its docstring::

   init -> next -> transition -> write -> dwell -> pulse -> read -> ramp_down -> end
   ^       ^                                  |_____________^  |            |
   |       |___________________________________________________|            |
   |________________________________________________________________________|

The ordering is approximately linear, but with some loops and skips:

* If no pulse program is defined, the ``pulse`` stage is skipped.
* If more items remain to be iterated over, ``read`` heads to ``next``.
* If the sweep is continuous, ``ramp_down`` restarts it instead of finishing it.

Those steps which deal with accessing resources (``transition``, ``write``, ``read``, ``ramp_down``) do so in parallel, using as many concurrent :class:`threading.Thread` objects as necessary.

The sweeping process can be interrupted at any time for many reasons; some of these include: user error, device error, and the user pressing the "Cancel" button. In the case that it is interrupted, the sweep simply proceeds to either the ``ramp_down`` or the ``end`` stage, depending on whether is interruption is fatal. The distinction between a fatal and a non-fatal interruption is that in the case of a fatal one, the ``ramp_down`` stage cannot be expected to succeed; for example, if writing to a resource failed.
