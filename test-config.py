global config

# Addresses of devices with which to test.
config['devices'] = {}
config['devices']['AWG5014B.eth'] = {
	'address': {'ip_address': '192.0.2.123'},
	'manufacturer': 'Tektronix',
	'model': 'AWG5014B',
	'has_mock': True,
}
config['devices']['DM34410A.gpib'] = {
	'address': {'gpib_board': 0, 'gpib_pad': 1},
	'manufacturer': 'Agilent',
	'model': '34410A',
}
config['devices']['VoltageSource.usb'] = {
	'address': {'usb_resource': 'USB::0x1234::0x5678::01234567::RAW'},
	'manufacturer': 'Custom',
	'model': 'Voltage source',
}
