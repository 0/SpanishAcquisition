global config

# Addresses of devices with which to test.
config['devices'] = {}
config['devices']['AWG5014B.eth'] = {
	'address': {'ip_address': '192.168.0.10'},
	'manufacturer': 'Tektronix',
	'model': 'AWG5014B',
	'has_mock': True,
}
config['devices']['DM34410A.gpib'] = {
	'address': {'gpib_board': 0, 'gpib_pad': 21},
	'manufacturer': 'Agilent',
	'model': '34410A',
	'has_mock': True,
}
config['devices']['DPO7104.eth'] = {
	'address': {'ip_address': '192.168.0.2'},
	'manufacturer': 'Tektronix',
	'model': 'DPO7104',
	'has_mock': True,
}
config['devices']['VoltageSource.usb'] = {
	'address': {'usb_resource': 'USB0::0x3923::0x7166::01456739::RAW'},
	'manufacturer': 'Custom',
	'model': 'Voltage source',
	'has_mock': True,
}
