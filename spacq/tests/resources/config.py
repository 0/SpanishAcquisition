global config

# Addresses of devices with which to test.
config['devices'] = {}
config['devices']['AWG5014B.eth'] = {
	'address': {'ip_address': '192.168.0.10'},
	'implementation_path': 'spacq/devices/tektronix/awg5014b.py',
	'mock_implementation_path': 'spacq/devices/tektronix/mock/mock_awg5014b.py',
}
config['devices']['DM34410A.gpib'] = {
	'address': {'gpib_board': 0, 'gpib_pad': 21},
	'implementation_path': 'spacq/devices/agilent/dm34410a.py',
	'mock_implementation_path': 'spacq/devices/agilent/mock/mock_dm34410a.py',
}
config['devices']['VoltageSource.usb'] = {
	'address': {'usb_resource': 'USB0::0x3923::0x7166::01456739::RAW'},
	'implementation_path': 'spacq/devices/custom/voltage_source.py',
	'mock_implementation_path': 'spacq/devices/custom/mock/mock_voltage_source.py',
}
