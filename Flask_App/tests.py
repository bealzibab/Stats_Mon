import postgresManagement
import influxHandler as ih 
import json

#postgresManagement.createBaseTables()
#postgresManagement.addUser('Marcus', 'marcus@lightspeedwireless.co.za', '', 'admin')
#postgresManagement.editUser('Marcus', usergroup='user')
#postgresManagement.removeUser('Marcus')
#postgresManagement.addUser('Luca', 'luca@lightspeedwireless.co.za', '', 'user')
#postgresManagement.checkUserLogin('Marcus')
#postgresManagement.removeUser('Marcus')
#postgresManagement.addPowerDevice('Uitkyk', '192.168.100.3', 'NPM-X')
#postgresManagement.addPowerDevice('GVB', '192.168.96.200', 'Solar Monitor-SNMP')

#postgresManagement.editPowerDevice('Uitkyk', newName='Uitkyk Power')
#postgresManagement.removePowerDevice('Uitkyk Power')
#postgresManagement.addNetworkDevice('CCR1036', '192.168.100.1', 'Marcus', '')
#postgresManagement.addNetworkDevice('EQU 4011', '192.168.106.1', 'Marcus', '')
#postgresManagement.addNetworkDevice('GVB 4011', '192.168.96.1', 'Marcus', '')
#postgresManagement.addNetworkDevice('CCR1016', '192.168.98.1', 'Marcus', '')
#postgresManagement.editNetworkDevice('CCR1036', newName='Uitkyk CCR1036')
#postgresManagement.removeNetworkDevice('Uitkyk CCR1036')
#postgresManagement.addPingTarget('Google', '8.8.8.8', 1)
#postgresManagement.editPingTarget('Google', time=5)
#postgresManagement.removePingTarget('Google')
#postgresManagement.addHTTPSTarget('Lightspeed Website', 'lightspeedwireless.co.za', 5, '200', 'Networking')
#postgresManagement.editHTTPSTarget('Lightspeed Website', time=30)
#postgresManagement.removeHTTPSTarget('Lightspeed Website')

menu_data = {
    "1": "home",
    "2": "user_dashboard"
}

#postgresManagement.addMenuLayout('Gavin Menu', 'user', json.dumps(menu_data))
#postgresManagement.getMenuLayout('user')
#postgresManagement.removeMenuLayout('User Menu')
#postgresManagement.getAllUsers()
#postgresManagement.getAllPowerDevices()
#postgresManagement.getAllNetworkDevices()
#postgresManagement.getAllPingTargets()
#postgresManagement.getAllHTTPSTargets()
#postgresManagement.addOIDReference('Test', voltageOID='1.3.6.1.4.1.45501.1.3.3.0', loadCurrentOID='1.3.6.1.4.1.45501.1.3.5.0', chargeCurrentOID='1.3.6.1.4.1.45501.1.3.12.0')
#postgresManagement.addUserConfig('Marcus', )


#postgresManagement.addOIDReference('Solar Monitor SNMP (Old)', voltageOID='1.3.6.1.4.1.45501.1.3.3.0', loadCurrentOID='1.3.6.1.4.1.45501.1.3.5.0', chargeCurrentOID='1.3.6.1.4.1.45501.1.3.12.0', temperatureOID='1.3.6.1.4.1.45501.1.3.7.0')
#postgresManagement.addOIDReference('Mikrotik', voltageOID='.1.3.6.1.4.1.14988.1.1.3.8.0', loadCurrentOID='.1.3.6.1.4.1.14988.1.1.3.8.0', chargeCurrentOID='.1.3.6.1.4.1.14988.1.1.3.8.0', temperatureOID='.1.3.6.1.4.1.14988.1.1.3.10.0')


postgresManagement.addPowerDevice('HNK', '192.168.95.201', 'Solar Monitor SNMP (Old)')
postgresManagement.addPowerDevice('Rusty Gate', '192.168.96.201', 'Solar Monitor SNMP (Old)')