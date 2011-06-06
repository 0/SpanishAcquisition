global config

# Addresses of devices with which to test.
config['devices'] = {}
config['devices']['AWG5014B.eth'] = {'ip_address': '192.168.0.10'}
config['devices']['DM34410A.gpib'] = {'board': 0, 'pad': 21}
config['devices']['VoltageSource.usb'] = {'usb_resource': 'USB0::0x3923::0x7166::01456739::RAW'}
