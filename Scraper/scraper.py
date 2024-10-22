import sys
import os
import ros_api
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import asyncio
from puresnmp import Client, V2C, PyWrapper
import time
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Flask_App.postgresManagement import getAllNetworkDevices, getAllPowerDevices, getAllReferenceOID

token = "as24n9iG03a-ML9awVOEfpCimF241rTdt1XgWDKkVTWLhOCG1GMN5_7Y9248yyCEzX_WvXgHvv1Mwvj7-fgDIw=="
org = "Lightspeed Wireless"
url = "http://localhost:8086"
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
bucket = "networkData"
power_bucket = "powerData"

def loginiser(ipAddress, user, password, port):
    router = ros_api.Api(ipAddress, user=user, password=password, port=port)
    return router

def phyInterfaceStats(router):
    usageStats = router.talk('/interface/ethernet/print stats')
    interfaceInfo = router.talk('/interface/ethernet/print detail')

    # Process usageStats to replace '<>' with ' to '
    for interface in usageStats:
        for key, value in interface.items():
            if isinstance(value, str):
                interface[key] = value.replace('<>', ' to ')

    # Process interfaceInfo to replace '<>' with ' to '
    for interface in interfaceInfo:
        for key, value in interface.items():
            if isinstance(value, str):
                interface[key] = value.replace('<>', ' to ')

    data = {'interfaceInfo': interfaceInfo, 'usageStats': usageStats}
    return data

def queueStats(router):
    # Fetch the queue stats from the router
    queueStats = router.talk('/queue/simple/print details')

    # Iterate over each queue and remove '<' and '>' from any part of the details
    for queue in queueStats:
        for key, value in queue.items():
            if isinstance(value, str):  # Ensure we are working with strings
                queue[key] = value.replace('<', '').replace('>', '')

    # Return the cleaned data
    data = {'queueStats': queueStats}
    return data

def systemStats(router):
    systemHealth = router.talk('/system/health/print')
    systemStatistics = router.talk('/system/resource/print')
    loggedInUsers = router.talk('/user/active/print')
    data = {'systemHealth': systemHealth, 'systemStats': systemStatistics, 'loggedInUsers': loggedInUsers}
    return data

def systemInfo(router):
    routerBOARD = router.talk('/system/routerboard/print')
    data = {'routerboard': routerBOARD}
    return data

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def networkScraper(device, refreshTime=1):
    try:
        router = loginiser(device[1], device[2], device[3], device[4])
        write_api = client.write_api(write_options=SYNCHRONOUS)

        system_info = systemInfo(router)
        if system_info['routerboard']:
            systemInfoPoint = Point('router_info') \
                .tag('router_name', device[0]) \
                .field('board_name', system_info['routerboard'][0].get('board-name')) \
                .field('model', system_info['routerboard'][0].get('model')) \
                .field('serial_number', system_info['routerboard'][0].get('serial-number')) \
                .field('factory_firmware', system_info['routerboard'][0].get('factory-firmware')) \
                .field('current_firmware', system_info['routerboard'][0].get('current-firmware')) \
                .field('upgrade_firmware', system_info['routerboard'][0].get('upgrade-firmware')) \
                .time(time.time_ns(), WritePrecision.NS)
            write_api.write(bucket=bucket, org=org, record=systemInfoPoint)

        # Store previous values for bandwidth calculation
        prev_interface_stats = {}

        while True:
            stats = systemStats(router)
            phyInterfaces = phyInterfaceStats(router)
            queueData = queueStats(router)

            current_time = time.time_ns()

            if stats['systemStats']:
                print('Getting System Stats')
                # Ensure systemHealth has enough entries to avoid IndexError
                voltage = safe_float(stats['systemHealth'][0].get('value')) if len(stats['systemHealth']) > 0 else 0.0
                temperature = safe_float(stats['systemHealth'][1].get('value')) if len(stats['systemHealth']) > 1 else 0.0

                systemStatsPoint = Point("router_stats") \
                    .tag("router_name", device[0]) \
                    .field("cpu_load", safe_float(stats['systemStats'][0].get('cpu-load'))) \
                    .field("free_memory", safe_float(stats['systemStats'][0].get('free-memory')) / 1000000) \
                    .field("total_memory", safe_float(stats['systemStats'][0].get('total-memory')) / 1000000) \
                    .field("used_memory", (safe_float(stats['systemStats'][0].get('total-memory')) - safe_float(stats['systemStats'][0].get('free-memory'))) / 1000000) \
                    .field("uptime", stats['systemStats'][0].get('uptime', '0s')) \
                    .field("voltage", voltage) \
                    .field("temperature", temperature) \
                    .time(current_time, WritePrecision.NS)
                write_api.write(bucket=bucket, org=org, record=systemStatsPoint)

            if stats['loggedInUsers']:
                print('Getting System Users')
                for line in stats['loggedInUsers']:
                    loggedInUsersPoint = Point("logged_in_users") \
                        .tag("name", line.get('name')) \
                        .field('router', device[0]) \
                        .field('ip_address', line.get('address')) \
                        .field('method', line.get('via')) \
                        .field('login_time', line.get('when')) \
                        .time(current_time, WritePrecision.NS)
                    write_api.write(bucket=bucket, org=org, record=loggedInUsersPoint)

            if phyInterfaces['interfaceInfo']:
                print('Getting System Interface Info')
                for line in phyInterfaces['usageStats']:
                    interface_name = line.get('name')
                    tx_bytes = safe_float(line.get('tx-bytes'))
                    rx_bytes = safe_float(line.get('rx-bytes'))

                    # Calculate bandwidth if previous stats are available
                    if interface_name in prev_interface_stats:
                        prev_tx_bytes = prev_interface_stats[interface_name]['tx_bytes']
                        prev_rx_bytes = prev_interface_stats[interface_name]['rx_bytes']
                        prev_time = prev_interface_stats[interface_name]['timestamp']

                        # Time difference in seconds
                        time_diff = (current_time - prev_time) / 1_000_000_000  # Convert ns to seconds

                        tx_bandwidth = (tx_bytes - prev_tx_bytes) * 8 / time_diff  # Bits per second
                        rx_bandwidth = (rx_bytes - prev_rx_bytes) * 8 / time_diff  # Bits per second
                    else:
                        tx_bandwidth = 0
                        rx_bandwidth = 0

                    # Log interface stats along with bandwidth
                    interfacePoint = Point("interface_stats") \
                        .tag("name", interface_name) \
                        .tag('router', device[0]) \
                        .field('default_name', line.get('default-name', '')) \
                        .field('mac_address', line.get('mac-address', '')) \
                        .field('advertised_rate', line.get('advertise', '')) \
                        .field('tx_bytes', tx_bytes) \
                        .field('rx_bytes', rx_bytes) \
                        .field('tx_bandwidth', -int(tx_bandwidth)) \
                        .field('rx_bandwidth', int(rx_bandwidth)) \
                        .field('status', line.get('running', '')) \
                        .field('disabled', line.get('disabled', '')) \
                        .time(current_time, WritePrecision.NS)
                    write_api.write(bucket=bucket, org=org, record=interfacePoint)

                    # Update previous stats for bandwidth calculation in the next iteration
                    prev_interface_stats[interface_name] = {'tx_bytes': tx_bytes, 'rx_bytes': rx_bytes, 'timestamp': current_time}

            if queueData['queueStats']:
                print('Getting System Queue Data')
                for line in queueData['queueStats']:
                    max_limit = line.get('max-limit', '0/0').split('/')
                    rate = line.get('rate', '0/0').split('/')

                    tx_limit = -safe_float(max_limit[0]) if len(max_limit) > 0 else 0.0
                    rx_limit = safe_float(max_limit[1]) if len(max_limit) > 1 else 0.0
                    tx_usage = -safe_float(rate[0]) if len(rate) > 0 else 0.0
                    rx_usage = safe_float(rate[1]) if len(rate) > 1 else 0.0

                    queuePoint = Point('queue_stats') \
                        .tag('name', line.get('name')) \
                        .field('router', device[0]) \
                        .field('targets', line.get('target', '')) \
                        .field('tx_limit', tx_limit) \
                        .field('rx_limit', rx_limit) \
                        .field('tx_usage', tx_usage) \
                        .field('rx_usage', rx_usage) \
                        .time(current_time, WritePrecision.NS)
                    write_api.write(bucket=bucket, org=org, record=queuePoint)

            time.sleep(refreshTime)

    except Exception as e:
        print(f"An error occurred: {e}")

async def getOID(hostIP, OID):
    client = PyWrapper(Client(hostIP, V2C('public')))
    output = await client.get(OID)
    return output

def powerScraper(deviceData, client=client, power_bucket=power_bucket, org=org):
    write_api = client.write_api(write_options=SYNCHRONOUS)

    async def monitorPowerData():
        while True:
            device_name = deviceData[0]
            try:
                voltageOID = None
                temperatureOID = None
                loadCurrentOID = None
                chargeCurrentOID = None

                for referenceOID in getAllReferenceOID():
                    if deviceData[2] == referenceOID[0]:
                        voltageOID = referenceOID[1]
                        temperatureOID = referenceOID[2]
                        loadCurrentOID = referenceOID[3]
                        chargeCurrentOID = referenceOID[4]
                        break  # Assuming only one match is needed

                voltage = safe_float(await getOID(deviceData[1], voltageOID)) if voltageOID else 0.0
                temperature = safe_float(await getOID(deviceData[1], temperatureOID)) if temperatureOID else 0.0
                loadCurrent = safe_float(await getOID(deviceData[1], loadCurrentOID)) if loadCurrentOID else 0.0
                chargeCurrent = safe_float(await getOID(deviceData[1], chargeCurrentOID)) if chargeCurrentOID else 0.0

                # Create a point for InfluxDB
                power_point = Point("power_stats") \
                    .tag("device_name", device_name) \
                    .field("voltage", voltage) \
                    .field("temperature", temperature) \
                    .field("load_current", loadCurrent) \
                    .field("charge_current", chargeCurrent) \
                    .time(time.time_ns(), WritePrecision.NS)

                # Write power data to InfluxDB
                write_api.write(bucket=power_bucket, org=org, record=power_point)

            except Exception as e:
                print(f"Error scraping power data from {device_name}: {e}")
            await asyncio.sleep(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitorPowerData())

def run_network_scrapers():
    network_devices = getAllNetworkDevices()
    threads = []
    for device in network_devices:
        thread = threading.Thread(target=networkScraper, args=(device,))
        threads.append(thread)
        thread.start()

def run_power_scrapers():
    power_devices = getAllPowerDevices()
    print(power_devices)
    threads = []
    for device in power_devices:
        thread = threading.Thread(target=powerScraper, args=(device,))
        threads.append(thread)
        thread.start()

run_power_scrapers()
run_network_scrapers()
