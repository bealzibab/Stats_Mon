from influxdb_client import InfluxDBClient

token = "2CA6hWdT47mgouWFTw6u9W-nclmwlHJWcXyhu9irxmEcrDnlWEPIuO54fs6F0oTfFN9QeJUHuVoXIZmEjBwzzA=="
org = "Lightspeed Wireless"
url = "http://localhost:8086"
client = InfluxDBClient(url=url, token=token, org=org)
bucket = "networkData"
power_bucket = "powerData"

def getWindowPeriod(totalDuration):
    if totalDuration.endswith('d'):
        totalDuration = int(totalDuration.strip('d'))
        totalDuration = totalDuration * 86400
    elif totalDuration.endswith('h'):
        totalDuration = int(totalDuration.strip('h'))
        totalDuration = totalDuration * 3600
    elif totalDuration.endswith('m'):
        totalDuration = int(totalDuration.strip('m'))
        totalDuration = totalDuration * 60
    elif totalDuration.endswith('s'):
        totalDuration = int(totalDuration.strip('s'))
    windowPeriod = (totalDuration / 90)
    if windowPeriod < 1:
        return 1
    else:
        return int(windowPeriod)

def calculateWindowPeriod(totalDuration):
    if totalDuration.endswith('d'):
        totalDuration = int(totalDuration.strip('d'))
        totalDuration = totalDuration * 86400
    elif totalDuration.endswith('h'):
        totalDuration = int(totalDuration.strip('h'))
        totalDuration = totalDuration * 3600
    elif totalDuration.endswith('m'):
        totalDuration = int(totalDuration.strip('m'))
        totalDuration = totalDuration * 60
    elif totalDuration.endswith('s'):
        totalDuration = int(totalDuration.strip('s'))
    windowPeriod = (totalDuration / 90)
    if windowPeriod < 1:
        return '1s'
    else:
        return str(int(windowPeriod)) + 's'

def fluxToJson(fluxTables):
    results = []
    for table in fluxTables:
        for record in table.records:
            results.append(record.values)
    return results

def getRouterStats(router, duration, client=client):
    windowPeriod = calculateWindowPeriod(duration)    
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -{duration}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "router_stats")
        |> filter(fn: (r) => r["_field"] == "voltage" or r["_field"] == "cpu_load" or r["_field"] == "free_memory" or r["_field"] == "used_memory" or r["_field"] == "total_memory" or r["_field"] == "logged_in_users" or r["_field"] == "temperature" or r["_field"] == "total_memory" or r["_field"] == "uptime")
        |> filter(fn: (r) => r["router_name"] == "{router}")
        |> aggregateWindow(every: {windowPeriod}, fn: last, createEmpty: false)
        |> yield(name: "last")
    '''
    queryApi = client.query_api()
    result = queryApi.query(query)
    resultJson = fluxToJson(result)
    return (result_json)

def getQueueStats(router, queueName, duration, client=client):
    # Define the bucket name
    bucket = "networkData"
    
    # Calculate the window period based on the duration
    windowPeriod = calculateWindowPeriod(duration)
    
    # InfluxDB query to fetch queue stats for the specific router, queue name, and duration
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -{duration}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "queue_stats")
        |> filter(fn: (r) => r["name"] == "{queueName}")
        |> filter(fn: (r) => r["_field"] == "rx_limit" or r["_field"] == "rx_usage" or r["_field"] == "tx_limit" or r["_field"] == "tx_usage" or r["_field"] == "router")
        |> aggregateWindow(every: {windowPeriod}, fn: last, createEmpty: false)
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> filter(fn: (r) => r["router"] == "{router}")
        |> yield(name: "last")
    '''
        
    # Execute the query using InfluxDB client
    queryApi = client.query_api()
    result = queryApi.query(query)
    
    # Convert the result to JSON format
    resultJson = fluxToJson(result)
    
    # Print and return the result
    return resultJson



def getInterfaceStats(router, interfaceName, duration, client=client):
    bucket = "networkData"
    windowPeriod = calculateWindowPeriod(duration)

    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -{duration})
        |> filter(fn: (r) => r["_measurement"] == "interface_stats")
        |> filter(fn: (r) => r["router"] == "{router}")
        |> filter(fn: (r) => r["name"] == "{interfaceName}")
        |> filter(fn: (r) => r["_field"] == "tx_bytes" or r["_field"] == "rx_bytes" or r["_field"] == "tx_bandwidth" or r["_field"] == "rx_bandwidth" or r["_field"] == "mac_address" or r["_field"] == "status" or r["_field"] == "advertised_rate" or r["_field"] == "default_name" or r["_field"] == "disabled")
        |> aggregateWindow(every: {windowPeriod}, fn: last, createEmpty: false)
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"])
    '''

    queryApi = client.query_api()
    result = queryApi.query(query)

    resultJson = fluxToJson(result)

    interfaceInfo = []
    usageStats = []
    for record in resultJson:
        usageStats.append({
            'name': record.get('name'),
            'default-name': record.get('default_name'),
            'mac-address': record.get('mac_address'),
            'advertise': record.get('advertised_rate'),
            'tx-bytes': record.get('tx_bytes'),
            'rx-bytes': record.get('rx_bytes'),
            'tx_bandwidth': record.get('tx_bandwidth'),
            'rx_bandwidth': record.get('rx_bandwidth'),
            'running': record.get('status'),
            'disabled': record.get('disabled'),
            '_time': record.get('_time'),
        })
        interfaceInfo.append({
            'name': record.get('name'),
            'default-name': record.get('default_name'),
        })

    return {'interfaceInfo': interfaceInfo, 'usageStats': usageStats}




def getSystemStats(router, duration, client=client):
    windowPeriod = calculateWindowPeriod(duration)
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -{duration}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "interface_stats")
        |> filter(fn: (r) => r["_field"] == "tx_bandwidth_bps" or r["_field"] == "rx_bandwidth_bps" or r["_field"] == "tx_bandwidth_mbps" or r["_field"] == "rx_bandwidth_mbps" or r["_field"] == "tx_bytes" or r["_field"] == "rx_bytes")
        |> filter(fn: (r) => r["router_name"] == "{router}")
        |> aggregateWindow(every: {windowPeriod}, fn: last, createEmpty: false)
        |> yield(name: "last")
    '''
    queryApi = client.query_api()
    result = queryApi.query(query)
    resultJson = fluxToJson(result)
    return resultJson


def getRouterInfo(router, client=client):
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -1d, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "router_info")
        |> filter(fn: (r) => r["router_name"] == "{router}")
        |> filter(fn: (r) => r["_field"] == "current_firmware" or r["_field"] == "factory_firmware" or r["_field"] == "model" or r["_field"] == "serial_number" or r["_field"] == "upgrade_firmware")
        |> group(columns: ["_measurement", "_field"])
        |> last()
        |> yield(name: "last")
    '''
    queryApi = client.query_api()
    result = queryApi.query(query)
    resultJson = fluxToJson(result)
    return resultJson

def getUniqueQueueNames(routerName, client=client):
    try:
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -30d, stop: now())  // Adjust range if needed
            |> filter(fn: (r) => r["_measurement"] == "queue_stats")
            |> filter(fn: (r) => r["router"] == "{routerName}")
            |> distinct(column: "name")  // Get distinct values of the "name" tag
            |> keep(columns: ["name"])  // Only keep the "name" column
        '''
        queryApi = client.query_api()
        result = queryApi.query(query)

        # Check if the result is empty
        if not result:
            print("No data found for the given query.")
            return []

        # Convert to JSON
        resultJson = fluxToJson(result)
        if not resultJson:
            print("No data in JSON format.")
            return []

        # Extract the queue names
        queueNames = [record['name'] for record in resultJson if 'name' in record]
        if not queueNames:
            print("No queue names found.")
        return queueNames

    except Exception as e:
        print(f"Error occurred: {e}")
        return []

def getUniqueInterfaceNames(routerName, client=client):
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -30d, stop: now())  // Adjust the time range as needed
        |> filter(fn: (r) => r["_measurement"] == "interface_stats")
        |> filter(fn: (r) => r["router"] == "{routerName}")
        |> distinct(column: "name")  // Get distinct values of the "name" tag (interface names)
        |> keep(columns: ["name"])  // Only keep the "name" column
    '''
    queryApi = client.query_api()
    result = queryApi.query(query)
    resultJson = fluxToJson(result)
    interfaceNames = [record['name'] for record in resultJson]
    return (interfaceNames)


def getVoltageStats(device_name, duration, bucket="powerData", client=client):
    # Define the Flux query using f-string for dynamic values
    windowPeriod = calculateWindowPeriod(duration)
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -{duration}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "power_stats")
        |> filter(fn: (r) => r["_field"] == "voltage")
        |> filter(fn: (r) => r["device_name"] == "{device_name}")
        |> aggregateWindow(every: {windowPeriod}, fn: last, createEmpty: false)
        |> yield(name: "mean")
    '''
    
    try:
        # Execute the query using the InfluxDB client's query API
        query_api = client.query_api()
        result = query_api.query(query)
        
        # Convert the Flux result to JSON format
        result_json = fluxToJson(result)
        
        # Extract voltage data and timestamps from the JSON result
        voltage_data = [
            {"time": record["_time"], "voltage": record["_value"]}
            for record in result_json
        ]
        
        return voltage_data

    except Exception as e:
        print(f"Error fetching voltage stats for device {device_name}: {e}")
        return []

def getCurrentStats(device_name, duration, bucket="powerData", client=client):
    # Define the Flux query using f-string for dynamic values
    windowPeriod = calculateWindowPeriod(duration)
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -{duration}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "power_stats")
        |> filter(fn: (r) => r["_field"] == "charge_current" or r["_field"] == "load_current")
        |> filter(fn: (r) => r["device_name"] == "{device_name}")
        |> aggregateWindow(every: {windowPeriod}, fn: last, createEmpty: false)
        |> yield(name: "last")
    '''
    
    try:
        # Execute the query using the InfluxDB client's query API
        query_api = client.query_api()
        result = query_api.query(query)
        
        # Convert the Flux result to JSON format
        result_json = fluxToJson(result)
        
        # Extract charge_current and load_current data with timestamps
        current_data = [
            {
                "time": record["_time"],
                "field": record["_field"],
                "value": record["_value"]
            }
            for record in result_json
        ]
        
        # Separate charge_current and load_current into different lists
        charge_current = [entry for entry in current_data if entry['field'] == 'charge_current']
        load_current = [entry for entry in current_data if entry['field'] == 'load_current']
        
        return {
            "charge_current": charge_current,
            "load_current": load_current
        }

    except Exception as e:
        print(f"Error fetching current stats for device {device_name}: {e}")
        return {}