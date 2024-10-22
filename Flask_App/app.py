from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from influxdb_client import InfluxDBClient
import psycopg2
import bcrypt
import postgresManagement
import influxHandler
import os
import traceback
import json


app = Flask(__name__)
app.secret_key = 'MyVerySecureKeyHere'

def menuJsonToHTML(menu_jsonb):
    # FontAwesome icons mapping
    icon_map = {
        "home": "fas fa-home",
        "user_dashboard": "fas fa-tachometer-alt",
        "shared_dashboard": "fas fa-share-alt",
        "ongoing_alerts": "fas fa-bell",
        "user_management": "fas fa-users",
        "device_management": "fas fa-tools",
        "settings": "fas fa-cog",
        "logout": "fas fa-sign-out-alt"
    }

    # Start the HTML for the sidebar
    html_menu = '''
    <div class="sidebar" id="sidebar">
        <ul>
            <!-- Collapse button inside the sidebar -->
    '''

    # Loop through the JSON and build the menu items
    for key, value in menu_jsonb.items():
        URLvalue = url_for(value)
        icon_class = icon_map.get(value, "fas fa-question")  # Default icon if not found in the map
        # Build the list item with FontAwesome icon and link
        html_menu += f'  <li><a href="{URLvalue}"><i class="{icon_class}"></i> <span>{value.replace("_", " ").title()}</span></a></li>\n'

    # Close the ul and div
    html_menu += '''
        </ul>
    </div>
    '''

    return html_menu





@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		print(f"Username: {username}")
		
		userData = postgresManagement.checkUserLogin(username)
		print(f"User data: {userData}")
		
		# Check if userData is valid and contains 'password'
		if userData and 'password' in userData:
			try:
				stored_password = userData['password']  # This should already be in bcrypt format

				if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
					session['logged_in'] = True
					session['username'] = username
					session['usergroup'] = userData['usergroup']
					print(session)
					return redirect(url_for('home'))
				else:
					return render_template('login.html', error='Invalid Username or Password. Please Try Again.')
			except ValueError as e:
				print(f"Password validation error: {e}")
				return render_template('login.html', error='Invalid password format. Please contact support.')
		else:
			return render_template('login.html', error='User not found. Please try again.')

	return render_template('login.html')

@app.route('/')
def home():
	if not session.get('logged_in'):
		return redirect(url_for('login'))
	print(session.get('usergroup'))
	menuHTML = menuJsonToHTML(postgresManagement.getMenuLayout(session.get('usergroup')))
	return render_template('home.html', menu=menuHTML)

def parse_duration(duration_str):
    """
    Parse a duration string like '5m', '1h', '2d' into seconds.
    """
    num = int(''.join(filter(str.isdigit, duration_str)))
    unit = ''.join(filter(str.isalpha, duration_str))
    if unit == 'm':
        return num * 60
    elif unit == 'h':
        return num * 3600
    elif unit == 'd':
        return num * 86400
    else:
        return 300  # Default to 5 minutes if unrecognized

def getRefreshRate(duration_str):
    duration_seconds = parse_duration(duration_str)
    # Set refresh rate to be duration / 10, with min 5s, max 900s (15min)
    refresh_rate = max(5, min(duration_seconds / 90, 900))  # 900s = 15min
    return int(refresh_rate)

from flask import request

def parse_duration(duration_str):
    """
    Parse a duration string like '5m', '1h', '2d' into seconds.
    """
    num = int(''.join(filter(str.isdigit, duration_str)))
    unit = ''.join(filter(str.isalpha, duration_str))
    if unit == 'm':
        return num * 60
    elif unit == 'h':
        return num * 3600
    elif unit == 'd':
        return num * 86400
    else:
        return 300  # Default to 5 minutes if unrecognized

def getRefreshRate(duration_str):
    duration_seconds = parse_duration(duration_str)
    # Set refresh rate to be duration / 10, with min 5s, max 900s (15min)
    refresh_rate = max(5, min(duration_seconds / 10, 900))  # 900s = 15min
    return int(refresh_rate)

def getRefreshRate(duration_str):
    duration_seconds = parse_duration(duration_str)
    # Set refresh rate to be duration / 10, with min 5s, max 900s (15min)
    refresh_rate = max(5, min(duration_seconds / 10, 900))  # 900s = 15min
    return int(refresh_rate)

from flask import Flask, render_template, redirect, url_for, request, session
# Ensure you have imported necessary modules like postgresManagement

@app.route('/user_dashboard')
def user_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Define temperature range
    MIN_TEMPERATURE = -5  # Minimum expected temperature
    MAX_TEMPERATURE = 30  # Maximum expected temperature

    # Get the selected time period from the request args
    timePeriod = request.args.get('timePeriod', '5m')
    duration = timePeriod  # Use selected timePeriod as duration

    # Fetching menu and user dashboard data
    menuHTML = menuJsonToHTML(postgresManagement.getMenuLayout(session.get('usergroup')))
    user_dashboard_data = postgresManagement.getUserDashboard(session.get('username'))
    user_css_data = postgresManagement.getUserCSS(session.get('username'))

    # Extract user CSS if available
    if user_css_data and isinstance(user_css_data, (tuple, list)) and len(user_css_data) > 0:
        user_css = user_css_data[0]
    else:
        user_css = {}

    if user_dashboard_data == ({},):
        # If no dashboard data, redirect user to create a new dashboard
        routers = postgresManagement.getAllRouterNames()
        routers_options = ''.join(
            '<option value="{0}">{0}</option>'.format(router[0]) for router in routers
        )

        containerContent = f'''
        <div class="main-content" id="main-content">
            <div class="container">
                <p>It looks like you do not have a user dashboard set up yet, redirecting you to the dashboard creation interface.</p>
                <meta http-equiv="refresh" content="3; {url_for('create_user_dashboard')}" />
            </div>
        </div>
        '''
        return render_template('user-dashboard.html', containerContent=containerContent, menu=menuHTML)
    else:
        # Define time periods for dropdown
        time_periods = [
            ('1m', 'Last 1 minute'),
            ('5m', 'Last 5 minutes'),
            ('15m', 'Last 15 minutes'),
            ('30m', 'Last 30 minutes'),
            ('1h', 'Last 1 hour'),
            ('3h', 'Last 3 hours'),
            ('6h', 'Last 6 hours'),
            ('12h', 'Last 12 hours'),
            ('1d', 'Last 1 day'),
            ('2d', 'Last 2 days'),
            ('7d', 'Last 7 days'),
            ('14d', 'Last 14 days'),
            ('30d', 'Last 30 days')
        ]

        # Generate time period options for the dropdown
        timePeriodOptions = ''.join(
            f'<option value="{value}" {"selected" if value == timePeriod else ""}>{label}</option>'
            for value, label in time_periods
        )

        # If dashboard data exists, build charts
        charts = []
        power_device_rows = []

        # Define default colors for metrics (softer colors)
        default_colors = {
            'rxUsage': '#6c757d',       # Gray
            'txUsage': '#adb5bd',       # Light Gray
            'voltage': '#17a2b8',       # Teal
            'loadCurrent': '#28a745',   # Green
            'chargeCurrent': '#ffc107'  # Yellow
        }

        # Function to get color for a metric
        def get_color(metric_name):
            return user_css.get(metric_name, default_colors.get(metric_name, '#ffffff'))  # Default to white if not found

        # Building chart data for 'Power', 'queues', and 'Interfaces' categories
        for line in user_dashboard_data[0]:
            if line['category'] == 'Power':
                refreshRate = getRefreshRate(duration)
                device_parts = line['device'].split(',')
                if len(device_parts) >= 2:
                    device_name = device_parts[0]
                    device_ip = device_parts[1]
                else:
                    device_name = line['device']
                    device_ip = 'Unknown IP'

                # Prepare URLs
                voltage_chart_url = url_for('get_power_stats', device=device_name, duration=duration, metric='voltage')
                current_chart_url = url_for('get_power_stats', device=device_name, duration=duration, metric='current')
                realtime_data_url = url_for('get_power_realtime', device=device_name)

                power_device_rows.append({
                    'device': device_name,
                    'device_ip': device_ip,
                    'voltage_chart_url': voltage_chart_url,
                    'current_chart_url': current_chart_url,
                    'realtime_data_url': realtime_data_url,
                    'windowPeriod': refreshRate
                })
            elif line['category'] == 'queues':
                refreshRate = getRefreshRate(duration)
                charts.append({
                    'category': 'queues',
                    'router': line['device'],
                    'queue_name': line['target'],
                    'metric': line['metric'],
                    'url': url_for('get_queue_stats', device=(line['device'].split(','))[0], duration=duration, metric=line['metric'], queue_name=line['target'], router_name=line['device']),
                    'windowPeriod': refreshRate  # Use refresh rate as windowPeriod
                })
            elif line['category'] == 'interfaces':
                refreshRate = getRefreshRate(duration)
                charts.append({
                    'category': 'Interfaces',
                    'router': line['device'],
                    'interface_name': line['target'],
                    'metric': line['metric'],
                    'device': line['device'],
                    'url': url_for('get_interface_stats', interface_name=line['target'], duration=duration, router_name=line['device']),
                    'windowPeriod': refreshRate  # Use refresh rate as windowPeriod
                })

        # HTML content for rendering the charts in a responsive grid layout
        chartHTML = ''.join(
            f'''
            <div class="chart-container">
                <canvas id="chart-{i}"></canvas>
            </div>
            ''' for i, chart in enumerate(charts)
        )

        # Updated power_device_HTML with adjusted styles to match heights and new real-time data display
        power_device_HTML = ''.join(
            f'''
            <div class="power-device-container">
                <h3>{power_device['device']} ({power_device['device_ip']})</h3>
                <div class="power-device-content">
                    <!-- Live Stats Column -->
                    <div class="realtime-data" id="realtime-data-{i}">
                        <h4 style="text-decoration: none; color: #ffffff;">Real-Time Data</h4>
                        <div class="metrics">
                            <div class="metric-container voltage" style="background-color: {get_color('voltage')}">
                                <span class="metric-label">Voltage:</span>
                                <span class="metric-value" id="voltage-value-{i}">--</span> V
                            </div>
                            <div class="metric-container load-current" style="background-color: {get_color('loadCurrent')}">
                                <span class="metric-label">Load Current:</span>
                                <span class="metric-value" id="load-current-value-{i}">--</span> A
                            </div>
                            <div class="metric-container charge-current" style="background-color: {get_color('chargeCurrent')}">
                                <span class="metric-label">Charge Current:</span>
                                <span class="metric-value" id="charge-current-value-{i}">--</span> A
                            </div>
                            <div class="metric-container temperature" id="temperature-container-{i}">
                                <span class="metric-label">Temperature:</span>
                                <span class="metric-value" id="temperature-value-{i}">--</span> °C
                            </div>
                        </div>
                    </div>
                    <!-- Voltage Chart Column -->
                    <div class="chart-container">
                        <canvas id="voltage-chart-{i}"></canvas>
                    </div>
                    <!-- Current Chart Column -->
                    <div class="chart-container">
                        <canvas id="current-chart-{i}"></canvas>
                    </div>
                </div>
            </div>
            ''' for i, power_device in enumerate(power_device_rows)
        )

        # Add a toggle button for collapsing the sidebar
        toggleButtonHTML = '''
        <button id="sidebarToggle" class="sidebar-toggle">
            <i class="fas fa-bars"></i>
        </button>
        '''

        # Container content with time period dropdown, charts, and edit button
        containerContent = f'''
        <div class="main-content" id="main-content">
            {toggleButtonHTML}
            <div class="container">
                <div class="dashboard-header">
                    <h2>Dashboard</h2>
                    <div class="actions">
                        <!-- Edit Button to go to create user dashboard -->
                        <a href="{url_for('create_user_dashboard')}" class="btn btn-edit">
                            Edit
                        </a>
                        <form method="GET" action="{url_for('user_dashboard')}">
                            <select name="timePeriod" id="timePeriod" onchange="this.form.submit()">
                                {timePeriodOptions}
                            </select>
                        </form>
                    </div>
                </div>
                <!-- Power Devices -->
                {power_device_HTML}
                <!-- Network Charts -->
                <div class="chart-grid">
                    {chartHTML}
                </div>
            </div>
        </div>
        '''

        # JavaScript for sidebar toggle functionality
        sidebarToggleScript = '''
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const sidebar = document.querySelector('.sidebar');
                const mainContent = document.querySelector('.main-content');
                const toggleButton = document.querySelector('#sidebarToggle');

                toggleButton.addEventListener('click', function() {
                    sidebar.classList.toggle('collapsed');
                    mainContent.classList.toggle('collapsed');
                });
            });
        </script>
        '''

        # JS script for network charts with user-defined colors
        chartScripts = ''.join(
            f'''
            <script>
                (function() {{
                    const ctx = document.getElementById('chart-{i}').getContext('2d');
                    const chart = new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: [],
                            datasets: []
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            animation: false,
                            scales: {{
                                x: {{
                                    type: 'time',
                                    time: {{
                                        unit: 'minute',
                                        displayFormats: {{
                                            minute: 'HH:mm',
                                            hour: 'HH:mm',
                                            second: 'HH:mm:ss'
                                        }}
                                    }},
                                    title: {{
                                        display: true,
                                        text: 'Time',
                                        color: '#eeeeec',
                                        font: {{
                                            size: 10
                                        }}
                                    }},
                                    ticks: {{
                                        color: '#d3d7cf',
                                        font: {{
                                            size: 8
                                        }},
                                        maxTicksLimit: 5
                                    }},
                                    grid: {{
                                        color: '#555753'
                                    }}
                                }},
                                y: {{
                                    beginAtZero: false,
                                    title: {{
                                        display: true,
                                        text: '{chart['metric']}',
                                        color: '#eeeeec',
                                        font: {{
                                            size: 10
                                        }}
                                    }},
                                    ticks: {{
                                        color: '#d3d7cf',
                                        font: {{
                                            size: 8
                                        }}
                                    }},
                                    grid: {{
                                        color: '#555753'
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    display: true,
                                    labels: {{
                                        color: '#eeeeec',
                                        font: {{
                                            size: 8,
                                            family: 'Ubuntu, Arial, sans-serif',
                                            weight: 'normal'
                                        }},
                                        usePointStyle: true,
                                        pointStyle: 'circle',
                                        boxWidth: 6,
                                        boxHeight: 6,
                                        padding: 10
                                    }}
                                }},
                                title: {{
                                    display: true,
                                    text: '{chart['metric']} - {chart.get('interface_name', chart.get('queue_name', chart.get('device')))} ({chart.get('router', chart.get('device_ip', ''))})',
                                    color: '#eeeeec',
                                    font: {{
                                        size: 12
                                    }}
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false,
                                    backgroundColor: '#2e3436',
                                    titleColor: '#eeeeec',
                                    bodyColor: '#eeeeec',
                                    borderColor: '#555753',
                                    borderWidth: 1,
                                    titleFont: {{
                                        size: 8
                                    }},
                                    bodyFont: {{
                                        size: 8
                                    }}
                                }}
                            }}
                        }}
                    }});

                    // Fetching data for the chart
                    async function fetchData() {{
                        try {{
                            const response = await fetch('{chart['url']}');
                            const data = await response.json();

                            if ('{chart['category']}' === 'queues') {{
                                return {{
                                    times: data.map(entry => new Date(entry._time)),
                                    rxUsage: data.map(entry => entry.rx_usage / 1000000),
                                    txUsage: data.map(entry => entry.tx_usage / 1000000),
                                }};
                            }} else if ('{chart['category']}' === 'Interfaces') {{
                                const usageStats = data.usageStats;
                                return {{
                                    times: usageStats.map(entry => new Date(entry._time)),
                                    rxBandwidth: usageStats.map(entry => entry.rx_bandwidth / 1e6),  // Convert to Mbps
                                    txBandwidth: usageStats.map(entry => entry.tx_bandwidth / 1e6),
                                }};
                            }}
                        }} catch (error) {{
                            console.error('Error fetching data for chart {i}:', error);
                        }}
                    }}

                    // Updating the chart data
                    async function updateChart() {{
                        const data = await fetchData();
                        if (data) {{
                            if ('{chart['category']}' === 'queues') {{
                                chart.data.labels = data.times;
                                chart.data.datasets = [
                                    {{
                                        label: 'RX Usage (Mbps)',
                                        data: data.rxUsage,
                                        borderColor: '{get_color('rxUsage')}',
                                        borderWidth: 2,
                                        tension: 0.4,
                                        fill: false,
                                        pointRadius: 0,
                                        pointStyle: 'circle',
                                        pointBackgroundColor: '{get_color('rxUsage')}'
                                    }},
                                    {{
                                        label: 'TX Usage (Mbps)',
                                        data: data.txUsage,
                                        borderColor: '{get_color('txUsage')}',
                                        borderWidth: 2,
                                        tension: 0.4,
                                        fill: false,
                                        pointRadius: 0,
                                        pointStyle: 'circle',
                                        pointBackgroundColor: '{get_color('txUsage')}'
                                    }}
                                ];

                                const allValues = data.rxUsage.concat(data.txUsage);
                                const minValue = Math.min(...allValues);
                                const maxValue = Math.max(...allValues);
                                const midValue = (minValue + maxValue) / 2;
                                const range = (maxValue - minValue) * 1.2 || 1;
                                chart.options.scales.y.min = midValue - range / 2;
                                chart.options.scales.y.max = midValue + range / 2;
                            }} else if ('{chart['category']}' === 'Interfaces') {{
                                chart.data.labels = data.times;
                                chart.data.datasets = [
                                    {{
                                        label: 'RX Bandwidth (Mbps)',
                                        data: data.rxBandwidth,
                                        borderColor: '{get_color('rxUsage')}',  // Assuming 'rxBandwidth' uses 'rxUsage' color
                                        borderWidth: 2,
                                        tension: 0.4,
                                        fill: false,
                                        pointRadius: 0,
                                        pointStyle: 'circle',
                                        pointBackgroundColor: '{get_color('rxUsage')}'
                                    }},
                                    {{
                                        label: 'TX Bandwidth (Mbps)',
                                        data: data.txBandwidth,
                                        borderColor: '{get_color('txUsage')}',  // Assuming 'txBandwidth' uses 'txUsage' color
                                        borderWidth: 2,
                                        tension: 0.4,
                                        fill: false,
                                        pointRadius: 0,
                                        pointStyle: 'circle',
                                        pointBackgroundColor: '{get_color('txUsage')}'
                                    }}
                                ];

                                const allValues = data.rxBandwidth.concat(data.txBandwidth);
                                const minValue = Math.min(...allValues);
                                const maxValue = Math.max(...allValues);
                                const midValue = (minValue + maxValue) / 2;
                                const range = (maxValue - minValue) * 1.2 || 1;
                                chart.options.scales.y.min = midValue - range / 2;
                                chart.options.scales.y.max = midValue + range / 2;
                            }}
                            chart.update();
                        }}
                    }}
                    // Automatically update the chart at regular intervals
                    const refreshRate = {chart['windowPeriod']} * 1000;
                    setInterval(updateChart, refreshRate);
                    updateChart();
                }})();
            </script>
            ''' for i, chart in enumerate(charts)
        )

        # JS scripts for power devices with user-defined colors and improved real-time data display
        power_device_scripts = ''.join(
            f'''
            <script>
                (function() {{
                    // Function to map temperature to color
                    function getTemperatureColor(temp) {{
                        const minTemp = {MIN_TEMPERATURE}; // Minimum temperature
                        const maxTemp = {MAX_TEMPERATURE}; // Maximum temperature

                        // Clamp the temperature within the range
                        const clampedTemp = Math.max(minTemp, Math.min(maxTemp, temp));

                        // Calculate the ratio (0 to 1)
                        const ratio = (clampedTemp - minTemp) / (maxTemp - minTemp);

                        // Convert ratio to hue (240 = blue, 0 = red)
                        const hue = (1 - ratio) * 240;

                        return `hsl(${{hue}}, 100%, 50%)`;
                    }}

                    // Real-time data update
                    async function updateRealtimeData() {{
                        try {{
                            const response = await fetch('{power_device['realtime_data_url']}');
                            const data = await response.json();

                            document.getElementById('voltage-value-{i}').textContent = data.voltage.toFixed(2);
                            document.getElementById('temperature-value-{i}').textContent = data.temperature.toFixed(2);
                            document.getElementById('load-current-value-{i}').textContent = data.load_current.toFixed(2);
                            document.getElementById('charge-current-value-{i}').textContent = data.charge_current.toFixed(2);

                            // Update Temperature Container Color
                            const temperature = data.temperature;
                            const tempContainer = document.getElementById('temperature-container-{i}');
                            const tempColor = getTemperatureColor(temperature);

                            tempContainer.style.backgroundColor = tempColor;
                            tempContainer.style.color = '#ffffff'; // Ensure text is visible

                        }} catch (error) {{
                            console.error('Error fetching real-time data for device {power_device['device']}:', error);
                        }}
                    }}

                    // Voltage Chart
                    const voltageCtx = document.getElementById('voltage-chart-{i}').getContext('2d');
                    const voltageChart = new Chart(voltageCtx, {{
                        type: 'line',
                        data: {{
                            labels: [],
                            datasets: [{{
                                label: 'Voltage (V)',
                                data: [],
                                borderColor: '{get_color('voltage')}',
                                borderWidth: 2,
                                tension: 0.4,
                                fill: false,
                                pointRadius: 0
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {{
                                x: {{
                                    type: 'time',
                                    time: {{
                                        unit: 'minute',
                                        displayFormats: {{
                                            minute: 'HH:mm',
                                            hour: 'HH:mm',
                                            second: 'HH:mm:ss'
                                        }}
                                    }},
                                    title: {{
                                        display: true,
                                        text: 'Time',
                                        color: '#eeeeec',
                                        font: {{
                                            size: 10
                                        }}
                                    }},
                                    ticks: {{
                                        color: '#d3d7cf',
                                        font: {{
                                            size: 8
                                        }},
                                        maxTicksLimit: 5
                                    }},
                                    grid: {{
                                        color: '#555753'
                                    }}
                                }},
                                y: {{
                                    beginAtZero: false,
                                    title: {{
                                        display: true,
                                        text: 'Voltage (V)',
                                        color: '#eeeeec',
                                        font: {{
                                            size: 10
                                        }}
                                    }},
                                    ticks: {{
                                        color: '#d3d7cf',
                                        font: {{
                                            size: 8
                                        }}
                                    }},
                                    grid: {{
                                        color: '#555753'
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    display: true,
                                    labels: {{
                                        color: '#eeeeec',
                                        font: {{
                                            size: 8,
                                            family: 'Ubuntu, Arial, sans-serif',
                                            weight: 'normal'
                                        }},
                                        usePointStyle: true,
                                        pointStyle: 'circle',
                                        boxWidth: 6,
                                        boxHeight: 6,
                                        padding: 10
                                    }}
                                }},
                                title: {{
                                    display: true,
                                    text: 'Voltage (V) - {power_device['device']} ({power_device['device_ip']})',
                                    color: '#eeeeec',
                                    font: {{
                                        size: 12
                                    }}
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false,
                                    backgroundColor: '#2e3436',
                                    titleColor: '#eeeeec',
                                    bodyColor: '#eeeeec',
                                    borderColor: '#555753',
                                    borderWidth: 1,
                                    titleFont: {{
                                        size: 8
                                    }},
                                    bodyFont: {{
                                        size: 8
                                    }}
                                }}
                            }}
                        }}
                    }});

                    // Current Chart
                    const currentCtx = document.getElementById('current-chart-{i}').getContext('2d');
                    const currentChart = new Chart(currentCtx, {{
                        type: 'line',
                        data: {{
                            labels: [],
                            datasets: [
                                {{
                                    label: 'Load Current (A)',
                                    data: [],
                                    borderColor: '{get_color('loadCurrent')}',
                                    borderWidth: 2,
                                    tension: 0.4,
                                    fill: false,
                                    pointRadius: 0
                                }},
                                {{
                                    label: 'Charge Current (A)',
                                    data: [],
                                    borderColor: '{get_color('chargeCurrent')}',
                                    borderWidth: 2,
                                    tension: 0.4,
                                    fill: false,
                                    pointRadius: 0
                                }}
                            ]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {{
                                x: {{
                                    type: 'time',
                                    time: {{
                                        unit: 'minute',
                                        displayFormats: {{
                                            minute: 'HH:mm',
                                            hour: 'HH:mm',
                                            second: 'HH:mm:ss'
                                        }}
                                    }},
                                    title: {{
                                        display: true,
                                        text: 'Time',
                                        color: '#eeeeec',
                                        font: {{
                                            size: 10
                                        }}
                                    }},
                                    ticks: {{
                                        color: '#d3d7cf',
                                        font: {{
                                            size: 8
                                        }},
                                        maxTicksLimit: 5
                                    }},
                                    grid: {{
                                        color: '#555753'
                                    }}
                                }},
                                y: {{
                                    beginAtZero: false,
                                    title: {{
                                        display: true,
                                        text: 'Current (A)',
                                        color: '#eeeeec',
                                        font: {{
                                            size: 10
                                        }}
                                    }},
                                    ticks: {{
                                        color: '#d3d7cf',
                                        font: {{
                                            size: 8
                                        }}
                                    }},
                                    grid: {{
                                        color: '#555753'
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    display: true,
                                    labels: {{
                                        color: '#eeeeec',
                                        font: {{
                                            size: 8,
                                            family: 'Ubuntu, Arial, sans-serif',
                                            weight: 'normal'
                                        }},
                                        usePointStyle: true,
                                        pointStyle: 'circle',
                                        boxWidth: 6,
                                        boxHeight: 6,
                                        padding: 10
                                    }}
                                }},
                                title: {{
                                    display: true,
                                    text: 'Current (A) - {power_device['device']} ({power_device['device_ip']})',
                                    color: '#eeeeec',
                                    font: {{
                                        size: 12
                                    }}
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false,
                                    backgroundColor: '#2e3436',
                                    titleColor: '#eeeeec',
                                    bodyColor: '#eeeeec',
                                    borderColor: '#555753',
                                    borderWidth: 1,
                                    titleFont: {{
                                        size: 8
                                    }},
                                    bodyFont: {{
                                        size: 8
                                    }}
                                }}
                            }}
                        }}
                    }});

                    // Fetch data for charts
                    async function updateCharts() {{
                        try {{
                            // Fetch voltage data
                            const voltageResponse = await fetch('{power_device['voltage_chart_url']}');
                            const voltageData = await voltageResponse.json();

                            // Fetch current data
                            const currentResponse = await fetch('{power_device['current_chart_url']}');
                            const currentData = await currentResponse.json();

                            // Update voltage chart
                            const voltageTimes = voltageData.map(entry => new Date(entry.time));
                            const voltageValues = voltageData.map(entry => entry.voltage || entry.value);
                            voltageChart.data.labels = voltageTimes;
                            voltageChart.data.datasets[0].data = voltageValues;

                            // Adjust y-axis for voltage chart
                            const minVoltage = Math.min(...voltageValues);
                            const maxVoltage = Math.max(...voltageValues);
                            const midVoltage = (minVoltage + maxVoltage) / 2;
                            const rangeVoltage = (maxVoltage - minVoltage) * 1.2 || 1;
                            voltageChart.options.scales.y.min = midVoltage - rangeVoltage / 2;
                            voltageChart.options.scales.y.max = midVoltage + rangeVoltage / 2;

                            voltageChart.update();

                            // Update current chart
                            const currentTimes = currentData.charge_current.map(entry => new Date(entry.time));
                            const loadCurrentValues = currentData.load_current.map(entry => entry.value);
                            const chargeCurrentValues = currentData.charge_current.map(entry => entry.value);
                            currentChart.data.labels = currentTimes;
                            currentChart.data.datasets[0].data = loadCurrentValues;
                            currentChart.data.datasets[1].data = chargeCurrentValues;

                            // Adjust y-axis for current chart
                            const allCurrentValues = loadCurrentValues.concat(chargeCurrentValues);
                            const minCurrent = Math.min(...allCurrentValues);
                            const maxCurrent = Math.max(...allCurrentValues);
                            const midCurrent = (minCurrent + maxCurrent) / 2;
                            const rangeCurrent = (maxCurrent - minCurrent) * 1.2 || 1;
                            currentChart.options.scales.y.min = midCurrent - rangeCurrent / 2;
                            currentChart.options.scales.y.max = midCurrent + rangeCurrent / 2;

                            currentChart.update();
                        }} catch (error) {{
                            console.error('Error fetching chart data for device {power_device['device']}:', error);
                        }}
                    }}

                    // Set intervals for updates
                    const refreshRate = {power_device['windowPeriod']} * 1000;
                    setInterval(updateRealtimeData, refreshRate);
                    setInterval(updateCharts, refreshRate);
                    updateRealtimeData();
                    updateCharts();
                }})();
            </script>
            ''' for i, power_device in enumerate(power_device_rows)
        )

        # JS scripts for power devices with updated temperature color mapping
        allScripts = sidebarToggleScript + chartScripts + power_device_scripts

        # Add necessary CSS for metric containers
        additionalCSS = '''
        <style>
            .realtime-data h4 {
                text-decoration: none; /* Remove underline */
                color: #ffffff; /* Ensure text color is visible */
            }
            .metrics {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                margin-top: 10px;
            }
            .metric-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 10px;
                border-radius: 8px;
                color: #ffffff; /* White text */
                text-align: center;
                min-height: 80px;
            }
            .metric-label {
                font-weight: bold;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 1.2em;
                font-weight: bold;
            }

            /* Transition for smooth color changes */
            .metric-container.temperature {
                transition: background-color 0.5s ease;
            }

            /* Responsive adjustments */
            @media (max-width: 600px) {
                .metrics {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        '''

        # Inject additional CSS into containerContent
        containerContent = f'''
        {additionalCSS}
        {containerContent}
        '''

        # Render the user dashboard page with generated charts and scripts
        return render_template('user-dashboard.html', containerContent=containerContent, menu=menuHTML, chartScripts=allScripts)












@app.route('/get-queue-stats')
def get_queue_stats():
	if not session.get('logged_in'):
		return 'Error, User not Logged In', 500
	queue_name = request.args.get('queue_name')

	router_name = request.args.get('router_name')

	duration = request.args.get('duration')

	queueData = influxHandler.getQueueStats(queueName=queue_name, duration=duration, router=router_name)
	return queueData

@app.route('/get-interface-stats')
def get_interface_stats():
    if not session.get('logged_in'):
        return 'Error, User not Logged In', 500
    interface_name = request.args.get('interface_name')
    router_name = request.args.get('router_name')
    duration = request.args.get('duration')

    interfaceData = influxHandler.getInterfaceStats(interfaceName=interface_name, duration=duration, router=router_name)
    return jsonify(interfaceData)

@app.route('/get-power-stats')
def get_power_stats():
    if not session.get('logged_in'):
        return 'Error, User not Logged In', 500

    device_name = request.args.get('device')
    duration = request.args.get('duration')
    metric = request.args.get('metric')

    # Check if required parameters are present
    if not device_name or not duration or not metric:
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        # Handle voltage metric request
        if metric == 'voltage':
            voltage_stats = influxHandler.getVoltageStats(device_name=device_name, duration=duration)
            if not voltage_stats:
                return jsonify({'error': 'No voltage data found'}), 404
            return jsonify(voltage_stats), 200

        # Handle current metric request (charge_current or load_current)
        elif metric == 'current':
            current_stats = influxHandler.getCurrentStats(device_name=device_name, duration=duration)
            if not current_stats:
                return jsonify({'error': 'No current data found'}), 404

            return jsonify(current_stats), 200

        # If the metric is not supported
        else:
            return jsonify({'error': f'Metric "{metric}" not supported'}), 400

    except Exception as e:
        # Log the error and return a 500 status with an error message
        print(f"Error fetching power stats: {e}")
        return jsonify({'error': 'An error occurred while fetching power stats'}), 500






@app.route('/get-queue-names')
def get_queue_names():
	if not session.get('logged_in'):
		return 'Error, User not Logged In', 500
	router_name = request.args.get('router')
	postgresManagement.updateQueues(router_name)
	queue_names = postgresManagement.getQueues(router_name)
	print(queue_names)
	return jsonify(queue_names)

@app.route('/get-interface-names')
def get_interface_names():
	if not session.get('logged_in'):
		return 'Error, User not Logged In', 500
	router_name = request.args.get('router')
	postgresManagement.updateInterfaces(router_name)
	interface_names = postgresManagement.getInterfaces(router_name)
	return jsonify(interface_names)

@app.route('/get-power-devices')
def get_power_devices():
	if not session.get('logged_in'):
		return 'Error, User not Logged In', 500
	power_devices = postgresManagement.getAllPowerDevices()
	print(power_devices)
	return(power_devices)

@app.route('/get-routers')
def get_routers():
	if not session.get('logged_in'):
		return 'Error, User not Logged In', 500
	routers = postgresManagement.getAllRouterNames()
	return jsonify([router[0] for router in routers])


@app.route('/save-user-dashboard', methods=['POST'])
def save_user_dashboard():
    try:
        # Get the data from the request
        data = request.json
        print(data)
        username = session.get('username')
        devices = data.get('devices')  # Fetch 'devices' key from data

        # Perform validation
        if not username:
            return jsonify({'success': False, 'message': 'Username is required'}), 400

        if not devices:
            return jsonify({'success': False, 'message': 'Devices configuration is required'}), 400

        # Convert devices to JSONB format (if needed)
        devicesJSONB = json.dumps(devices)

        postgresManagement.editUserConfig(username, dashboardConfig=devicesJSONB)

        return jsonify({'success': True, 'message': 'Dashboard updated successfully'}), 200

    except Exception as e:
        # Log the error traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': 'An error occurred on the server'}), 500


@app.route('/save-user-colours', methods=['POST'])
def save_user_colours():
    try:
        # Get the data from the request
        data = request.json
        print(data)
        username = session.get('username')
        colours = data.get('colours')  # Fetch 'devices' key from data

        # Perform validation
        if not username:
            return jsonify({'success': False, 'message': 'Username is required'}), 400

        # Convert devices to JSONB format (if needed)
        coloursJSONB = json.dumps(colours)

        postgresManagement.editUserConfig(username, cssConfig=coloursJSONB)

        return jsonify({'success': True, 'message': 'Dashboard updated successfully'}), 200

    except Exception as e:
        # Log the error traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': 'An error occurred on the server'}), 500

@app.route('/get_power_realtime')
def get_power_realtime():
    if not session.get('logged_in'):
        return jsonify({'error': 'User not logged in'}), 401

    device_name = request.args.get('device')

    if not device_name:
        return jsonify({'error': 'Device name is required'}), 400

    try:
        # Fetch the latest data for the specified device
        realtime_data = influxHandler.getPowerRealtimeData(device_name=device_name)

        if not realtime_data:
            return jsonify({'error': 'No data found for the specified device'}), 404

        return jsonify(realtime_data), 200

    except Exception as e:
        print(f"Error fetching real-time data for device {device_name}: {e}")
        return jsonify({'error': 'An error occurred while fetching real-time data'}), 500


@app.route('/shared-dashboard')
def shared_dashboard():
	if not session.get('logged_in'):
		return redirect(url_for('login'))
	return render_template('shared-dashboards.html', menu=menuHTML)

@app.route('/ongoing-alerts')
def ongoing_alerts():
	if not session.get('logged_in'):
		return redirect(url_for('login'))
	return render_template('ongoing-alerts.html', menu=menuHTML)

@app.route('/user-management')
def user_management():
	if not session.get('logged_in'):
		return redirect(url_for('login'))
	return render_template('user-management.html', menu=menuHTML)

@app.route('/device-management')
def device_management():
	if not session.get('logged_in'):
		return redirect(url_for('login'))
	return render_template('device-management.html', menu=menuHTML)

@app.route('/settings')
def settings():
	if not session.get('logged_in'):
		return redirect(url_for('login'))
	return render_template('settings.html', menu=menuHTML)

@app.route('/create_user_dashboard')
def create_user_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Fetch the user group and menu layout
    menuHTML = menuJsonToHTML(postgresManagement.getMenuLayout(session.get('usergroup')))

    # Check if the user already has a dashboard configuration
    user_dashboard_data = postgresManagement.getUserDashboard(session.get('username'))

    if user_dashboard_data == ({},):
        # No previous dashboard, render a blank setup
        existing_config = False
        dashboard_entries = []
    else:
        # Previous configuration exists, load it for editing
        existing_config = True
        dashboard_entries = user_dashboard_data[0]  # Assuming data is in the first index

    return render_template(
        'create_user_dashboard.html', 
        menu=menuHTML, 
        existing_config=existing_config, 
        dashboard_entries=dashboard_entries
    )

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=5000)