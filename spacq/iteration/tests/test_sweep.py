from functools import partial
from nose.tools import eq_
from os import path
from threading import Thread
from time import sleep, time
from unittest import main, TestCase

from spacq.devices.config import DeviceConfig
from spacq.interface.pulse.program import Program
from spacq.interface.resources import Resource
from spacq.interface.units import Quantity
from spacq.tool.box import flatten

from ..variables import sort_variables, InputVariable, OutputVariable, LinSpaceConfig

from .. import sweep


resource_dir = path.join(path.dirname(__file__), 'resources')


class SweepControllerTest(TestCase):
	def testSingle(self):
		"""
		Iterate over a single thing without any measurements.
		"""

		res_buf = []

		def setter(value):
			res_buf.append(value)

		res = Resource(setter=setter)
		var = OutputVariable(name='Var', order=1, enabled=True, const=-1.0)
		var.config = LinSpaceConfig(1.0, 4.0, 4)
		var.smooth_steps = 3
		var.smooth_from, var.smooth_to = [True] * 2

		vars, num_items = sort_variables([var])
		ctrl = sweep.SweepController([(('Res', res),)], vars, num_items, [], [])

		# Callback verification buffers.
		actual_values = []
		actual_measurement_values = []
		actual_writes = []
		actual_reads = []
		closed = [0]

		# Callbacks.
		def data_callback(cur_time, values, measurement_values):
			actual_values.append(values)
			actual_measurement_values.append(measurement_values)
		ctrl.data_callback = data_callback

		def close_callback():
			closed[0] += 1
		ctrl.close_callback = close_callback

		def write_callback(pos, i, value):
			actual_writes.append((pos, i, value))
		ctrl.write_callback = write_callback

		def read_callback(i, value):
			actual_reads.append((i, value))
		ctrl.read_callback = read_callback

		# Let it run.
		ctrl.run()

		eq_(res_buf, [-1.0, 0.0, 1.0, 1.0, 2.0, 3.0, 4.0, 4.0, 1.5, -1.0])
		eq_(actual_values, [(1.0,), (2.0,), (3.0,), (4.0,)])
		eq_(actual_measurement_values, [()] * 4)
		eq_(actual_writes, [(0, 0, x) for x in [1.0, 2.0, 3.0, 4.0]])
		eq_(actual_reads, [])
		eq_(closed, [1])

	def testProper(self):
		"""
		Testing everything that there is to test along the happy path:
			nested and parallel variables
			measurements
			dwell time
		"""

		res_bufs = [[], [], [], []]
		measurement_counts = [0] * 2

		def setter(i, value):
			res_bufs[i].append(value)

		def getter(i):
			measurement_counts[i] += (-1) ** i

			return measurement_counts[i]

		dwell_time = Quantity(50, 'ms')

		# Output.
		res0 = Resource(setter=partial(setter, 0))
		res0.units = 'cm-1'
		res1 = Resource(setter=partial(setter, 1))
		res2 = Resource(setter=partial(setter, 2))
		res3 = Resource(setter=partial(setter, 3))

		var0 = OutputVariable(name='Var 0', order=2, enabled=True, const=0.0)
		var0.config = LinSpaceConfig(-1.0, -2.0, 2)
		var0.smooth_steps = 2
		var0.smooth_from, var0.smooth_to, var0.smooth_transition = [True] * 3
		var0.type = 'quantity'
		var0.units = 'cm-1'

		var1 = OutputVariable(name='Var 1', order=1, enabled=True, const=-1.0)
		var1.config = LinSpaceConfig(1.0, 4.0, 4)
		var1.smooth_steps = 3
		var1.smooth_from, var1.smooth_to, var1.smooth_transition = [True] * 3

		var2 = OutputVariable(name='Var 2', order=1, enabled=True, const=1.23, use_const=True)

		var3 = OutputVariable(name='Var 3', order=1, enabled=True, const=-9.0, wait=str(dwell_time))
		var3.config = LinSpaceConfig(-1.0, 2.0, 4)
		var3.smooth_steps = 2
		var3.smooth_from, var3.smooth_to, var3.smooth_transition = True, True, False

		var4 = OutputVariable(name='Var 4', order=3, enabled=True, const=-20.0)
		var4.config = LinSpaceConfig(-10.0, 20, 1)
		var4.smooth_steps = 2
		var4.smooth_from = True

		# Input.
		meas_res0 = Resource(getter=partial(getter, 0))
		meas_res1 = Resource(getter=partial(getter, 1))

		meas0 = InputVariable(name='Meas 0')
		meas1 = InputVariable(name='Meas 1')

		vars, num_items = sort_variables([var0, var1, var2, var3, var4])
		ctrl = sweep.SweepController([(('Res 2', res2),), (('Something', None),), (('Res 0', res0),),
				(('Res 1', res1), ('Res 3', res3))], vars, num_items,
				[('Meas res 0', meas_res0), ('Meas res 1', meas_res1)], [meas0, meas1])

		# Callback verification buffers.
		actual_values = []
		actual_measurement_values = []
		actual_writes = []
		actual_reads = []
		closed = [0]

		# Callbacks.
		def data_callback(cur_time, values, measurement_values):
			actual_values.append(values)
			actual_measurement_values.append(measurement_values)
		ctrl.data_callback = data_callback

		def close_callback():
			closed[0] += 1
		ctrl.close_callback = close_callback

		def write_callback(pos, i, value):
			actual_writes.append((pos, i, value))
		ctrl.write_callback = write_callback

		def read_callback(i, value):
			actual_reads.append((i, value))
		ctrl.read_callback = read_callback

		# Let it run.
		start_time = time()
		ctrl.run()
		elapsed_time = time() - start_time

		expected_time = num_items * dwell_time.value
		assert expected_time < elapsed_time, 'Took {0} s, expected at least {1} s.'.format(elapsed_time, expected_time)

		expected_res1 = [1.0, 2.0, 3.0, 4.0]
		expected_res2 = [-1.0, 0.0, 1.0, 2.0]

		expected_inner_writes = list(flatten(((3, 0, x), (3, 1, x - 2.0)) for x in [1.0, 2.0, 3.0, 4.0]))
		expected_writes = [(0, 0, 1.23), (1, 0, -10.0)] + list(flatten([(2, 0, x)] + expected_inner_writes
				for x in [Quantity(x, 'cm-1') for x in [-1.0, -2.0]]))

		eq_(res_bufs, [
			[Quantity(x, 'cm-1') for x in [0.0, -1.0, -1.0, -2.0, -2.0, 0.0]],
			[-1.0, 0.0, 1.0] + expected_res1 + [4.0, 2.5, 1.0] + expected_res1 + [4.0, 1.5, -1.0],
			[1.23],
			[-9.0, -1.0] + expected_res2 + expected_res2 + [2.0, -9.0],
		])
		eq_(measurement_counts, [8, -8])
		eq_(actual_values, [(1.23, -10.0, x, y, y - 2.0)
				for x in [Quantity(x, 'cm-1') for x in [-1.0, -2.0]]
				for y in [1.0, 2.0, 3.0, 4.0]])
		eq_(actual_measurement_values, [(x, -x) for x in xrange(1, 9)])
		eq_(actual_writes, expected_writes)
		eq_(actual_reads, list(flatten(((0, x), (1, -x)) for x in xrange(1, 9))))
		eq_(closed, [1])

	def testContinuous(self):
		"""
		Keep going, and then eventually stop.
		"""

		res_buf = []

		def setter(value):
			res_buf.append(value)

		res = Resource(setter=setter)
		var = OutputVariable(name='Var', order=1, enabled=True)
		var.config = LinSpaceConfig(1.0, 4.0, 4)

		vars, num_items = sort_variables([var])
		ctrl = sweep.SweepController([(('Res', res),)], vars, num_items, [], [], continuous=True)

		thr = Thread(target=ctrl.run)
		thr.daemon = True
		thr.start()

		sleep(0.5)
		ctrl.pause()
		sleep(0.5)
		ctrl.unpause()
		sleep(0.5)

		ctrl.last_continuous = True
		thr.join()

		expected_buf = [1.0, 2.0, 3.0, 4.0]

		eq_(res_buf[:len(expected_buf) * 50], expected_buf * 50)

	def testWriteException(self):
		"""
		Fail to read.
		"""

		exceptions = []
		e = ValueError()

		def setter(value):
			raise e

		res = Resource(setter=setter)
		var = OutputVariable(name='Var', order=1, enabled=True, const=0.0)
		var.config = LinSpaceConfig(1.0, 4.0, 4)

		vars, num_items = sort_variables([var])
		ctrl = sweep.SweepController([(('Res', res),)], vars, num_items, [], [])

		def resource_exception_handler(name, e, write):
			exceptions.append((name, e))
			ctrl.abort(fatal=True)
			assert write
		ctrl.resource_exception_handler = resource_exception_handler

		ctrl.run()

		eq_(exceptions, [('Res', e)])

	def testReadException(self):
		"""
		Fail to write.
		"""

		exceptions = []
		e = ValueError()

		def getter():
			raise e

		res = Resource(setter=lambda x: x)
		var = OutputVariable(name='Var', order=1, enabled=True)
		var.config = LinSpaceConfig(1.0, 4.0, 4)

		meas_res = Resource(getter=getter)
		meas_var = InputVariable(name='Meas var')

		vars, num_items = sort_variables([var])
		ctrl = sweep.SweepController([(('Res', res),)], vars, num_items, [('Meas res', meas_res)], [meas_var])

		def resource_exception_handler(name, e, write):
			exceptions.append((name, e))
			assert not write
		ctrl.resource_exception_handler = resource_exception_handler

		ctrl.run()

		eq_(exceptions, [('Meas res', e)] * 4)

	def testPulseProgram(self):
		"""
		Iterate with a pulse program.
		"""

		res_buf = []

		def setter(value):
			res_buf.append(value)

		res = Resource(setter=setter)
		var1 = OutputVariable(name='Var 1', order=1, enabled=True)
		var1.config = LinSpaceConfig(1.0, 4.0, 4)

		p = Program.from_file(path.join(resource_dir, '01.pulse'))
		p.frequency = Quantity(1, 'GHz')
		p.set_value(('_acq_marker', 'marker_num'), 1)
		p.set_value(('_acq_marker', 'output'), 'f1')

		eq_(p.all_values, set([('_acq_marker', 'marker_num'), ('_acq_marker', 'output'), ('d',), ('i',),
				('p', 'amplitude'), ('p', 'length'), ('p', 'shape')]))

		parameters = [('i',), ('d',), ('p', 'amplitude'), ('p', 'length')]
		for parameter in parameters:
			p.resource_labels[parameter] = 'res_' + '.'.join(parameter)
			p.resources[parameter] = Resource()

		var2 = OutputVariable(name='Var 2', order=1, enabled=True)
		var2.config = LinSpaceConfig(1, 4, 4)
		var2.type = 'integer'

		awg_cfg = DeviceConfig('awg')
		awg_cfg.address_mode = awg_cfg.address_modes.gpib
		awg_cfg.manufacturer, awg_cfg.model = 'Tektronix', 'AWG5014B'
		awg_cfg.mock = True
		awg_cfg.connect()

		osc_cfg = DeviceConfig('osc')
		osc_cfg.address_mode = awg_cfg.address_modes.gpib
		osc_cfg.manufacturer, osc_cfg.model = 'Tektronix', 'DPO7104'
		osc_cfg.mock = True
		osc_cfg.connect()

		pulse_config = sweep.PulseConfiguration(p.with_resources, {'f1': 1}, awg_cfg.device, osc_cfg.device)

		vars, num_items = sort_variables([var1, var2])
		ress = [(('Res 1', res), ('Res 2', p.resources[('i',)]))]
		ctrl = sweep.SweepController(ress, vars, num_items, [], [], pulse_config)

		ctrl.run()

		eq_(res_buf, [1.0, 2.0, 3.0, 4.0])


if __name__ == '__main__':
	main()
