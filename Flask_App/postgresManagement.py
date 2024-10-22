import psycopg2
import bcrypt
import re
import ros_api

conn = psycopg2.connect(
	dbname="statsMon",
	user="lightspeed",
	password="L1ght$p33d!@#",
	host="localhost",
	port="5432"
)


def createBaseTables(conn=conn):
	cur = conn.cursor()
	cur.execute(f'''
		CREATE TABLE users (
			username VARCHAR(32) UNIQUE,
			email VARCHAR(128) UNIQUE,
			password VARCHAR(255),
			usergroup VARCHAR(32)
		);
		CREATE TABLE usergroups (
			usergroup VARCHAR(32) UNIQUE
		);
		CREATE TABLE user_config (
			username VARCHAR(32) UNIQUE,
			dashboardConfig JSONB,
			cssConfig JSONB
		);
		CREATE TABLE menus (
			name VARCHAR(32) UNIQUE,
			layout JSONB,
			userGroup VARCHAR(32)
		);
		CREATE TABLE shared_dashboards (
			name VARCHAR(32) UNIQUE,
			layout JSONB,
			userGroups text ARRAY
		);
		CREATE TABLE power_devices (
			name VARCHAR(32) UNIQUE,
			ipAddress VARCHAR(15),
			deviceModel VARCHAR(32)
		);
		CREATE TABLE refference_oids (
			name VARCHAR(32) UNIQUE,
			voltage VARCHAR(128),
			chargeCurrent VARCHAR(128),
			loadCurrent VARCHAR(128),
			temperature VARCHAR(128)
		);
		CREATE TABLE network_devices (
			name VARCHAR(32) UNIQUE,
			ipAddress VARCHAR(15),
			username VARCHAR(64),
			password VARCHAR(64),
			port INTEGER
		);
		CREATE TABLE ping_targets (
			name VARCHAR(32) UNIQUE,
			hostname VARCHAR(64) UNIQUE,
			time INTEGER
		);
		CREATE TABLE https_targets (
			name VARCHAR(32) UNIQUE,
			hostname VARCHAR(64),
			httpCode INTEGER,
			keyword VARCHAR(255),
			time INTEGER
		);
		CREATE TABLE oid_reference (
			model VARCHAR(32) UNIQUE,
			voltageOID VARCHAR(255),
			temperatureOID VARCHAR(255),
			loadCurrentOID VARCHAR(255),
			chargeCurrentOID VARCHAR(255)
		);

	''')
	conn.commit()

def addUser(username, email, password, usergroup, conn=conn):
	cur = conn.cursor()
	errorMessage = None
	salt = bcrypt.gensalt()
	hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
	
	# Ensure that the password is stored as a string in the database
	hashed_password_str = hashed_password.decode('utf-8')
	
	cur.execute('''
		INSERT INTO users (username, email, password, usergroup)
		VALUES (%s, %s, %s, %s)
	''', (username, email, hashed_password_str, usergroup))
	conn.commit()

#createBaseTables()
#addUser('Marcus', 'marcus@lightspeedwireless.co.za', 'L1ght$p33d!@#', 'admin')
#addUser('UserToEdit', 'deez@nuts.co.za', 'L1ght$p33d!@#', 'admin')

def editUser(username, email=None, password=None, usergroup=None, conn=conn):
	cur = conn.cursor()
	
	if password is not None:
		salt = bcrypt.gensalt()
		hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
		cur.execute('''
			UPDATE users SET password=%s
			WHERE username=%s;
		''', (hashed_password, username))  # Pass parameters as a tuple
	
	if usergroup is not None:
		cur.execute('''
			UPDATE users SET usergroup=%s
			WHERE username=%s;
		''', (usergroup, username))  # Pass parameters as a tuple
	
	if email is not None:
		cur.execute('''
			UPDATE users SET email=%s
			WHERE username=%s;
		''', (email, username))  # Pass parameters as a tuple
	
	conn.commit()

#editUser('UserToEdit', usergroup='correctedEmail@email.com')

def removeUser(username, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE FROM users
		WHERE username=%s
	''', (username,))
	conn.commit()

#removeUser('UserToEdit')

def checkUserLogin(username):
	cur = conn.cursor()
	
	# Fetch user data based on username or email
	cur.execute('''
		SELECT username, password, email, usergroup FROM users 
		WHERE username = %s OR email = %s
	''', (username, username))
	
	user = cur.fetchone()
	
	if user:
		# Unpack the user tuple
		username, storedHash, email, usergroup = user
		return {
			"username": username,
			"password": storedHash,
			"email": email,
			"usergroup": usergroup
		}
	else:
		return None


#user_data = checkUserLogin('Marcus')
#if user_data:
#    print("User found:", user_data)
#else:
#    print("User not found")


def addPowerDevice(name, IP, deviceModel, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO power_devices (name, ipAddress, deviceModel)
		VALUES (%s, %s, %s)
	''', (name, IP, deviceModel))
	conn.commit()

#addPowerDevice('testDevice', '1.1.1.1', 'test')

def editPowerDevice(name, newName=None, IP=None, deviceModel=None, conn=conn):
	cur = conn.cursor()
	if IP != None:
		cur.execute('''
			UPDATE power_devices SET ipAddress=%s
			WHERE name=%s
		''', (IP, name))
	if deviceModel != None:
		cur.execute('''
			UPDATE power_devices SET deviceModel=%s
			WHERE name=%s
		''', (deviceModel, name))
	if newName != None:
		cur.execute('''
			UPDATE power_devices SET name=%s
			WHERE name=%s
		''', (newName, name))
	conn.commit()

#editPowerDevice('pleaseWork', newName='eish', IP='2.2.2.2')

def removePowerDevice(name, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE FROM power_devices
		WHERE name=%s
	''', (name,))
	conn.commit()

#removePowerDevice('eish')

def addNetworkDevice(name, IP, username, password, port=8728, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO network_devices (name, ipAddress, username, password, port)
		VALUES (%s, %s, %s, %s, %s)
	''', (name, IP, username, password, port))
	conn.commit()

#addNetworkDevice('testDevice', '1.1.1.1', 'user1', 'MyVerySecureKeyHere')

def editNetworkDevice(name, newName=None, IP=None, username=None, password=None, port=None, conn=conn):
	cur = conn.cursor()
	if IP != None:
		cur.execute('''
			UPDATE power_devices SET ipAddress=%s
			WHERE name=%s
		''', (IP, name))
	if username != None:
		cur.execute('''
			UPDATE power_devices SET username=%s
			WHERE name=%s
		''', (username, name))
	if password != None:
		cur.execute('''
			UPDATE power_devices SET password=%s
			WHERE name=%s
		''', (password, name))
	if port != None:
		cur.execute('''
			UPDATE power_devices SET port=%s
			WHERE name=%s
		''', (port, name))
	if newName != None:
		cur.execute('''
			UPDATE power_devices SET name=%s
			WHERE name=%s
		''', (newName, name))
	conn.commit()

def removeNetworkDevice(name, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE FROM power_devices
		WHERE name=%s
	''', (name,))
	conn.commit()

def addPingTarget(name, IP, time, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO ping_targets (name, hostname, time)
		VALUES (%s, %s, %s)
	''', (name, IP, int(time)))
	conn.commit()

def editPingTarget(name, newName=None, IP=None, time=None, conn=conn):
	cur = conn.cursor()
	if IP !=None:
		cur.execute('''
			UPDATE ping_targets SET hostname=%s
			WHERE name=%s
		''', (IP, name))
	if time != None:
		cur.execute('''
			UPDATE ping_targets SET time=%s
			WHERE name=%s
		''', (int(time), name))
	if newName != None:
		cur.execute('''
			UPDATE ping_targets SET name=%s
			WHERE name=%s
		''', (newName, name))
	conn.commit()

def removePingTarget(name, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE FROM ping_targets
		WHERE name=%s
	''', (name,))
	conn.commit()

def addHTTPSTarget(name, hostname, time, code, keyword, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO https_targets (name, hostname, keyword, time)
		VALUES (%s, %s, %s, %s)
	''', (name, hostname, keyword, int(time)))
	conn.commit()

def editHTTPSTarget(name, newName=None, hostname=None, time=None, code=None, keyword=None, conn=conn):
	cur = conn.cursor()
	if hostname != None:
		cur.execute('''
			UPDATE https_targets SET hostname=%s
			WHERE name=%s
		''', (hostname, name))
	if time != None:
		cur.execute('''
			UPDATE https_targets SET time=%s
			WHERE name=%s
		''', (int(time), name))
	if code != None:
		cur.execute('''
			UPDATE https_targets SET code=%s
			WHERE name=%s
		''', (code, name))
	if keyword != None:
		cur.execute('''
			UPDATE https_targets SET keyword=%s
			WHERE name=%s
		''', (keyword, name))
	if newName != None:
		cur.execute('''
			UPDATE https_targets SET name=%s
			WHERE name=%s
		''', (newName, name))
	conn.commit()

def removeHTTPSTarget(name, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE FROM https_targets
		WHERE name=%s
	''', (name,))
	conn.commit()

def addMenuLayout(name, usergroup, menuJSONB, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO menus (name, layout, usergroup)
		VALUES (%s, %s, %s)
	''', (name, menuJSONB, usergroup))
	conn.commit()

def removeMenuLayout(name, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE FROM menus
		WHERE name=%s
	''', (name,))
	conn.commit()

def getMenuLayout(usergroup, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		SELECT layout
		FROM menus
		WHERE usergroup = %s
	''', (usergroup,))
	jsonLayout = cur.fetchone()
	cur.close()

	print(f"Raw menu layout fetched from DB for usergroup '{usergroup}': {jsonLayout}")

	# If no result is found, return an empty dictionary
	if jsonLayout is None:
		print("No menu found for usergroup:", usergroup)
		return {}

	# Since jsonLayout is already a dict, just return it as is
	return jsonLayout[0]  # No need to parse it again


def createSharedDashboard(name, usergroups, dashboardJSONB, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO shared_dashboards (name, layout, usergroups)
		VALUES (%s, %s, %s)
	''', (name, dashboardJSONB, usergroups))
	conn.commit()

def editSharedDashboard(name, newName=None, usergroups=None, layout=None, conn=conn):
	cur = conn.cursor()
	if layout is not None:
		cur.execute('''
			UPDATE shared_dashboards SET layout=%s
			WHERE name=%s
		''', (layout, name))
	if usergroups is not None:
		cur.execute('''
			UPDATE shared_dashboards SET usergroups=%s
			WHERE name=%s
		''', (usergroups, name))
	if newName is not None:
		cur.execute('''
			UPDATE shared_dashboards SET name=%s
			WHERE name=%s
		''', (newName, name))
	conn.commit()
	cur.close()

def removeSharedDashboard(name, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE FROM shared_dashboards
		WHERE name=%s
	''', (name,))
	conn.commit()
	cur.close()

def getAllUsers(conn=conn):
	cur = conn.cursor()
	cur.execute('SELECT * FROM users')
	users = cur.fetchall()
	cur.close()
	return users

def getAllPowerDevices(conn=conn):
	cur = conn.cursor()
	cur.execute('SELECT * FROM power_devices')
	power_devices = cur.fetchall()
	cur.close()
	return power_devices

def getAllNetworkDevices(conn=conn):
	cur = conn.cursor()
	cur.execute('SELECT * FROM network_devices')
	network_devices = cur.fetchall()
	cur.close()
	return network_devices

def getAllPingTargets(conn=conn):
	cur = conn.cursor()
	cur.execute('SELECT * FROM ping_targets')
	ping_targets = cur.fetchall()
	cur.close()
	return ping_targets

def getAllHTTPSTargets(conn=conn):
	cur = conn.cursor()
	cur.execute('SELECT * FROM https_targets')
	https_targets = cur.fetchall()
	cur.close()
	return https_targets

def addOIDReference(model, voltageOID=None, temperatureOID=None, loadCurrentOID=None, chargeCurrentOID=None, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO oid_reference (model, voltageOID, temperatureOID, loadCurrentOID, chargeCurrentOID)
		VALUES (%s, %s, %s, %s, %s)
	''', (model, voltageOID, temperatureOID, loadCurrentOID, chargeCurrentOID))
	conn.commit()

def deleteOIDreference(model, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		DELETE from oid_reference
		WHERE model=%s
	''', (model,))
	conn.commit()

def getAllReferenceOID(conn=conn):
	cur = conn.cursor()
	cur.execute('SELECT * FROM oid_reference')
	referenceOID = cur.fetchall()
	cur.close()
	return referenceOID

def addUserConfig(username, dashboardConfig=None, cssConfig=None, conn=conn):
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO user_config (username, dashboardConfig, cssConfig)
		VALUES (%s, %s, %s)
	''', (username, dashboardConfig, cssConfig))
	conn.commit()

def editUserConfig(username, newName=None, dashboardConfig=None, cssConfig=None, conn=conn):
	cur = conn.cursor()
	if dashboardConfig != None:
		cur.execute('''
			UPDATE user_config SET dashboardConfig=%s
			WHERE username=%s
		''',(dashboardConfig, username))
	if cssConfig != None:
		cur.execute('''
			UPDATE user_config SET cssConfig=%s
			WHERE username=%s
		''', (cssConfig, username))
	if newName != None:
		cur.execute('''
			UPDATE user_config SET username=%s
			WHERE username=%s
		''', (newName, username))
	conn.commit()

def resetUserConfig(username, conn=conn):
	cur = conn.cursor()
	cur.execute('''
			UPDATE user_config SET dashboardConfig=None, cssConfig=None
			WHERE username=%s
		''', (username,))
	conn.commit()

def getUserDashboard(username, conn=conn):
	cur = conn.cursor()
	cur.execute('''
			SELECT dashboardConfig FROM user_config
			WHERE username=%s
		''', (username,))
	userDashboard = cur.fetchone()
	cur.close()
	return userDashboard

def getUserCSS(username, conn=conn):
	cur = conn.cursor()
	cur.execute('''
			SELECT cssConfig FROM user_config
			WHERE username=%s
		''', (username,))
	userCSS = cur.fetchone()
	cur.close()
	return userCSS

def saveUserDashboard(username, dashboardJSONB, conn=conn):
	cur = conn.cursor()

	# Use INSERT with ON CONFLICT to perform upsert (insert or update)
	cur.execute('''
		INSERT INTO user_config (username, dashboardConfig)
		VALUES (%s, %s)
		ON CONFLICT (username)
		DO UPDATE SET dashboardConfig = EXCLUDED.dashboardConfig
	''', (username, dashboardJSONB))

	# Commit the transaction to save changes
	conn.commit()
	cur.close()

def getAllRouterNames(conn=conn):
	cur = conn.cursor()
	cur.execute('''
			SELECT name FROM network_devices
		''')
	routers = cur.fetchall()
	cur.close()
	return routers

def getQueues(router, conn=conn):
	cur = conn.cursor()
	cur.execute('''
			SELECT name FROM queues
			WHERE router=%s
		''', (router,))
	queues = cur.fetchall()
	cur.close()
	return queues 

def getInterfaces(router, conn=conn):
	cur = conn.cursor()
	cur.execute('''
			SELECT name FROM interfaces
			WHERE router=%s
		''', (router,))
	interfaces = cur.fetchall()
	return interfaces


def getQueuesFromRouter(routerLogin, routerName):
	router = ros_api.Api(routerLogin[0], user=routerLogin[2], password=routerLogin[3], port=routerLogin[1])
	interfaceStats = router.talk('/queue/simple/print details')
	interfaceList = []
	for line in interfaceStats:
		interfaceList.append(line['name'])
	return interfaceList

def getInterfacesFromRouter(routerLogin, routerName):
	router = ros_api.Api(routerLogin[0], user=routerLogin[2], password=routerLogin[3], port=routerLogin[1])
	interfaceStats = router.talk('/interface/ethernet/print')
	interfaceList = []
	for line in interfaceStats:
		interfaceList.append(line['name'])
	return interfaceList

def updateInterfaces(router, conn=conn):
	cur = conn.cursor()
	
	# Get login details for the specified router
	cur.execute('''
		SELECT ipAddress, port, username, password 
		FROM network_devices
		WHERE name=%s
	''', (router,))
	loginDetails = cur.fetchone()
	
	# Iterate through each interface name retrieved from the router
	for interfaceName in getInterfacesFromRouter(loginDetails, router):
		
		# Replace the exact combination of '<>' with the word 'to'
		cleanInterfaceName = interfaceName.replace('<>', ' to ')
		
		# Check if an interface with this name already exists for the router
		cur.execute('''
			SELECT COUNT(*) FROM interfaces 
			WHERE name=%s AND router=%s
		''', (cleanInterfaceName, router))
		
		# If no matching interface is found, insert the new interface
		if cur.fetchone()[0] == 0:
			cur.execute('''
				INSERT INTO interfaces (name, router)
				VALUES (%s, %s)
			''', (cleanInterfaceName, router))
			conn.commit()



def updateQueues(router, conn=conn):
	cur = conn.cursor()
	
	# Get login details for the specified router
	cur.execute('''
		SELECT ipAddress, port, username, password 
		FROM network_devices
		WHERE name=%s
	''', (router,))
	loginDetails = cur.fetchone()
	
	# Iterate through each queue name retrieved from the router
	for queueName in getQueuesFromRouter(loginDetails, router):
		
		# Strip the '<' and '>' characters from the queueName
		cleanQueueName = queueName.replace('<', '').replace('>', '')
		
		# Check if the queue with this name already exists for the router
		cur.execute('''
			SELECT COUNT(*) FROM queues 
			WHERE name=%s AND router=%s
		''', (cleanQueueName, router))
		
		# If no matching queue is found, insert the new queue
		if cur.fetchone()[0] == 0:
			cur.execute('''
				INSERT INTO queues (name, router)
				VALUES (%s, %s)
			''', (cleanQueueName, router))
			conn.commit()

def createInterfaceTable(conn=conn):
	cur = conn.cursor()
	cur.execute('''
		CREATE TABLE interfaces (
			name VARCHAR(128),
			router VARCHAR(128)
			)

		''')
	conn.commit()

def createBlankConfigForAllUsers(conn=conn):
	print('User Config Reset')
	cur = conn.cursor()

	# Fetch all usernames from the users table
	cur.execute('SELECT username FROM users')
	usernames = cur.fetchall()

	# Prepare a blank config (could be a JSONB or a default value)
	blank_dashboard_config = '{}'

	# Insert or update each user with a blank dashboard config
	for (username,) in usernames:
		cur.execute('''
			INSERT INTO user_config (username, dashboardConfig)
			VALUES (%s, %s)
			ON CONFLICT (username)
			DO UPDATE SET dashboardConfig = EXCLUDED.dashboardConfig
		''', (username, blank_dashboard_config))

	# Commit the transaction to save changes
	conn.commit()
	cur.close()