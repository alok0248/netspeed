
import html
import tempfile
import webbrowser
import threading
import json
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from PyQt5 import QtWidgets, QtGui, QtCore

from netspeed_tracker.monitor import format_data_size


def get_free_port():
    """Get a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        return s.getsockname()[1]


class DashboardRequestHandler(BaseHTTPRequestHandler):
    monitor = None
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.get_dashboard_html()
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if self.monitor:
                data = self.monitor.get_usage_dashboard_data()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({'error': 'No monitor available'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_dashboard_html(self):
        # Chart.js based beautiful HTML dashboard with live updates
        return '''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NetSpeed Usage Dashboard (Live)</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; }
        html, body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
            color: #e0e0e0; 
            margin: 0; 
            padding: 0.75rem; 
            max-width: 100vw;
            overflow-x: hidden;
        }
        .container { 
            max-width: 100%; 
            margin: 0 auto; 
        }
        header { 
            display: flex; 
            flex-wrap: wrap;
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 1rem; 
            border-bottom: 2px solid #00ff00; 
            padding-bottom: 0.75rem; 
        }
        h1 { 
            color: #00ff00; 
            margin: 0; 
            font-size: clamp(1.2rem, 3vw, 2rem); 
            text-shadow: 0 0 10px rgba(0,255,0,0.3);
        }
        .live-status { 
            color: #888; 
            font-size: clamp(0.75rem, 1.5vw, 0.9rem); 
            background: #1a1a1a;
            padding: 0.4rem 0.8rem;
            border-radius: 8px;
            border: 1px solid #333;
        }
        .view-toggle {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        .view-toggle button {
            background: #333;
            color: #e0e0e0;
            border: 1px solid #444;
            padding: 0.4rem 0.8rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: clamp(0.75rem, 1.5vw, 0.9rem);
            transition: all 0.2s;
        }
        .view-toggle button:hover {
            background: #444;
            border-color: #00ff00;
        }
        .view-toggle button.active {
            background: #00ff00;
            color: #000;
            border-color: #00ff00;
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 1rem;
        }
        .card { 
            background: #1a1a1a; 
            border-radius: 12px; 
            padding: 1rem; 
            border: 1px solid #333; 
            box-shadow: 0 4px 16px rgba(0,0,0,0.6); 
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.8);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .card h2 { 
            margin: 0; 
            font-size: clamp(0.9rem, 2.5vw, 1.2rem); 
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .card h2:hover {
            transform: scale(1.05);
        }
        .chart-toggle {
            display: flex;
            gap: 0.4rem;
        }
        .chart-toggle button {
            background: #333;
            color: #e0e0e0;
            border: 1px solid #444;
            padding: 0.3rem 0.7rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: clamp(0.7rem, 1.5vw, 0.8rem);
            transition: all 0.2s;
        }
        .chart-toggle button:hover {
            background: #444;
            border-color: #00ff00;
        }
        .chart-toggle button.active {
            background: #00ff00;
            color: #000;
            border-color: #00ff00;
        }
        canvas { 
            max-width: 100%; 
            max-height: 40vh !important;
        }
        .table-container {
            max-height: 200px;
            overflow-y: auto;
            margin-top: 0.75rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: clamp(0.7rem, 1.5vw, 0.85rem);
        }
        th {
            background: #2a2a2a;
            padding: 0.5rem;
            text-align: left;
            border-bottom: 2px solid #333;
            position: sticky;
            top: 0;
        }
        td {
            padding: 0.4rem 0.5rem;
            border-bottom: 1px solid #333;
        }
        tr:hover {
            background: #252525;
        }
        .show-table-btn {
            width: 100%;
            margin-top: 0.75rem;
            background: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #333;
            padding: 0.4rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: clamp(0.75rem, 1.5vw, 0.85rem);
            transition: all 0.2s;
        }
        .show-table-btn:hover {
            background: #333;
            border-color: #00ff00;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 NetSpeed Usage Dashboard</h1>
            <div class="live-status" id="liveStatus">🔴 Not Connected</div>
        </header>
        
        <div class="view-toggle">
            <button class="active" onclick="setView('all')">Show All</button>
            <button onclick="setView('yearly')">🗓️ Yearly Only</button>
            <button onclick="setView('monthly')">📅 Monthly Only</button>
            <button onclick="setView('daily')">📆 Daily Only</button>
            <button onclick="setView('hourly')">⏰ Hourly Only</button>
            <button onclick="setView('minute')">⏱️ Minute Only</button>
        </div>
        
        <div class="grid" id="grid">
            <div class="card" id="yearlyCard" data-key="yearly">
                <div class="card-header">
                    <h2 onclick="setView('yearly')" style="color: #ff6b6b;">🗓️ Yearly Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('yearly', 'line')">Line</button>
                        <button onclick="toggleChartType('yearly', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="yearlyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('yearly')">Show Data Table</button>
                <div class="table-container" id="yearlyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="monthlyCard" data-key="monthly">
                <div class="card-header">
                    <h2 onclick="setView('monthly')" style="color: #00ff00;">📅 Monthly Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('monthly', 'line')">Line</button>
                        <button onclick="toggleChartType('monthly', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="monthlyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('monthly')">Show Data Table</button>
                <div class="table-container" id="monthlyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="dailyCard" data-key="daily">
                <div class="card-header">
                    <h2 onclick="setView('daily')" style="color: #00ccff;">📆 Daily Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('daily', 'line')">Line</button>
                        <button onclick="toggleChartType('daily', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="dailyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('daily')">Show Data Table</button>
                <div class="table-container" id="dailyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="hourlyCard" data-key="hourly">
                <div class="card-header">
                    <h2 onclick="setView('hourly')" style="color: #ffcc00;">⏰ Hourly Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('hourly', 'line')">Line</button>
                        <button onclick="toggleChartType('hourly', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="hourlyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('hourly')">Show Data Table</button>
                <div class="table-container" id="hourlyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="minuteCard" data-key="minute">
                <div class="card-header">
                    <h2 onclick="setView('minute')" style="color: #ff00ff;">⏱️ Minute-wise Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('minute', 'line')">Line</button>
                        <button onclick="toggleChartType('minute', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="minuteChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('minute')">Show Data Table</button>
                <div class="table-container" id="minuteTable" style="display: none;"></div>
            </div>
        </div>
    </div>

    <script>
        let data = null;
        let currentView = 'all';
        const charts = {};
        const chartTypes = {};
        const colors = {
            yearly: { main: '#ff6b6b', bg: '#ff6b6b33' },
            monthly: { main: '#00ff00', bg: '#00ff0033' },
            daily: { main: '#00ccff', bg: '#00ccff33' },
            hourly: { main: '#ffcc00', bg: '#ffcc0033' },
            minute: { main: '#ff00ff', bg: '#ff00ff33' }
        };

        // Helper to format bytes to human readable
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function createChart(key, type) {
            const canvas = document.getElementById(key + 'Chart');
            const ctx = canvas.getContext('2d');
            const labels = data[key] ? data[key].map(item => item.label) : [];
            const values = data[key] ? data[key].map(item => item.total) : [];
            
            if (charts[key]) {
                charts[key].destroy();
            }
            
            // Ensure canvas is responsive
            canvas.style.width = '100%';
            canvas.style.height = 'auto';
            
            charts[key] = new Chart(ctx, {
                type: type,
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Total Usage',
                        data: values,
                        borderColor: colors[key].main,
                        backgroundColor: colors[key].bg,
                        borderWidth: type === 'line' ? 3 : 2,
                        pointRadius: type === 'line' ? 4 : 0,
                        pointHoverRadius: 6,
                        fill: type === 'line',
                        tension: 0.4,
                        borderRadius: type === 'bar' ? 6 : 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        x: { 
                            grid: { color: '#333' }, 
                            ticks: { color: '#888', maxRotation: 45, minRotation: 0 } 
                        },
                        y: { 
                            grid: { color: '#333' }, 
                            ticks: { 
                                color: '#888',
                                callback: function(value) { return formatBytes(value); }
                            } 
                        }
                    },
                    plugins: {
                        legend: { 
                            labels: { 
                                color: '#e0e0e0', 
                                font: { 
                                    size: window.innerWidth < 768 ? 12 : 14 
                                } 
                            } 
                        },
                        tooltip: {
                            backgroundColor: '#1a1a1a',
                            titleColor: '#00ff00',
                            bodyColor: '#e0e0e0',
                            borderColor: '#333',
                            borderWidth: 1,
                            callbacks: {
                                label: function(context) {
                                    return 'Usage: ' + formatBytes(context.raw);
                                }
                            }
                        }
                    }
                }
            });
            chartTypes[key] = type;
        }

        function toggleChartType(key, type) {
            const card = document.getElementById(key + 'Card');
            const buttons = card.querySelectorAll('.chart-toggle button');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            createChart(key, type);
        }

        function toggleTable(key) {
            const tableDiv = document.getElementById(key + 'Table');
            const btn = tableDiv.previousElementSibling;
            
            if (tableDiv.style.display === 'none') {
                tableDiv.style.display = 'block';
                btn.textContent = 'Hide Data Table';
                
                let tableHTML = '<table><thead><tr><th>Time Period</th><th>Downloaded</th><th>Uploaded</th><th>Total</th></tr></thead><tbody>';
                const items = data[key] || [];
                items.forEach(item => {
                    tableHTML += `<tr>
                        <td>${item.label}</td>
                        <td>${formatBytes(item.downloaded)}</td>
                        <td>${formatBytes(item.uploaded)}</td>
                        <td>${formatBytes(item.total)}</td>
                    </tr>`;
                });
                tableHTML += '</tbody></table>';
                tableDiv.innerHTML = tableHTML;
            } else {
                tableDiv.style.display = 'none';
                btn.textContent = 'Show Data Table';
            }
        }
        
        function setView(view) {
            currentView = view;
            
            // Update buttons
            document.querySelectorAll('.view-toggle button').forEach(btn => {
                btn.classList.remove('active');
            });
            event?.target?.classList.add('active');
            
            // Find which button corresponds to this view and mark as active
            document.querySelectorAll('.view-toggle button').forEach(btn => {
                if ((view === 'all' && btn.textContent === 'Show All') || 
                    (view === 'yearly' && btn.textContent.includes('Yearly')) || 
                    (view === 'monthly' && btn.textContent.includes('Monthly')) || 
                    (view === 'daily' && btn.textContent.includes('Daily')) || 
                    (view === 'hourly' && btn.textContent.includes('Hourly')) || 
                    (view === 'minute' && btn.textContent.includes('Minute'))) {
                    btn.classList.add('active');
                }
            });
            
            // Update card grid and sizing
            const cards = document.querySelectorAll('.card');
            const grid = document.getElementById('grid');
            const isSingleView = view !== 'all';
            
            cards.forEach(card => {
                const key = card.dataset.key;
                if (isSingleView && key === view) {
                    card.style.display = 'block';
                    card.style.maxWidth = '100%';
                } else if (view === 'all') {
                    card.style.display = 'block';
                    card.style.maxWidth = '100%'; // Reset for all view
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Adjust grid columns based on view
            if (isSingleView) {
                grid.style.gridTemplateColumns = '1fr';
            } else {
                grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(280px, 1fr))';
            }
        }
        
        function updateAllCharts() {
            ['yearly', 'monthly', 'daily', 'hourly', 'minute'].forEach(key => {
                createChart(key, chartTypes[key] || 'line');
            });
        }
        
        // Fetch initial data
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                data = await response.json();
                document.getElementById('liveStatus').textContent = '🟢 Live Update';
                
                if (Object.keys(charts).length === 0) {
                    // Initialize all charts
                    ['yearly', 'monthly', 'daily', 'hourly', 'minute'].forEach(key => {
                        createChart(key, 'line');
                    });
                } else {
                    updateAllCharts();
                }
                
            } catch (e) {
                console.error(e);
                document.getElementById('liveStatus').textContent = '🔴 Connection Error';
            }
        }
        
        // Fetch data and set interval to refresh
        fetchData();
        setInterval(fetchData, 3000); // Refresh every 3 seconds
        
        // Handle window resize to update charts
        window.addEventListener('resize', function() {
            updateAllCharts();
        });
    </script>
</body>
</html>'''
    
    def log_message(self, format, *args):
        """Suppress logging."""
        pass


def open_usage_dashboard_browser(monitor):
    # Ensure at least one sample exists
    data = monitor.get_usage_dashboard_data()
    if not data:
        monitor.log_current_sample()
    generated_at = QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
    report_path = Path(tempfile.gettempdir()) / 'netspeed_usage_dashboard.html'

    # Chart.js based beautiful HTML dashboard (static backup)
    report = f'''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NetSpeed Usage Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        html, body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
            color: #e0e0e0; 
            margin: 0; 
            padding: 0.75rem; 
            max-width: 100vw;
            overflow-x: hidden;
        }}
        .container {{ 
            max-width: 100%; 
            margin: 0 auto; 
        }}
        header {{ 
            display: flex; 
            flex-wrap: wrap;
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 1rem; 
            border-bottom: 2px solid #00ff00; 
            padding-bottom: 0.75rem; 
        }}
        h1 {{ 
            color: #00ff00; 
            margin: 0; 
            font-size: clamp(1.2rem, 3vw, 2rem); 
            text-shadow: 0 0 10px rgba(0,255,0,0.3);
        }}
        .timestamp {{ 
            color: #888; 
            font-size: clamp(0.75rem, 1.5vw, 0.9rem); 
            background: #1a1a1a;
            padding: 0.4rem 0.8rem;
            border-radius: 8px;
            border: 1px solid #333;
        }}
        .view-toggle {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        .view-toggle button {{
            background: #333;
            color: #e0e0e0;
            border: 1px solid #444;
            padding: 0.4rem 0.8rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: clamp(0.75rem, 1.5vw, 0.9rem);
            transition: all 0.2s;
        }}
        .view-toggle button:hover {{
            background: #444;
            border-color: #00ff00;
        }}
        .view-toggle button.active {{
            background: #00ff00;
            color: #000;
            border-color: #00ff00;
        }}
        .grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 1rem;
        }}
        .card {{ 
            background: #1a1a1a; 
            border-radius: 12px; 
            padding: 1rem; 
            border: 1px solid #333; 
            box-shadow: 0 4px 16px rgba(0,0,0,0.6); 
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.8);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .card h2 {{ 
            color: #00ff00; 
            margin: 0; 
            font-size: clamp(0.9rem, 2.5vw, 1.2rem); 
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        .card h2:hover {{
            transform: scale(1.05);
            text-shadow: 0 0 15px rgba(0,255,0,0.5);
        }}
        .chart-toggle {{
            display: flex;
            gap: 0.4rem;
        }}
        .chart-toggle button {{
            background: #333;
            color: #e0e0e0;
            border: 1px solid #444;
            padding: 0.3rem 0.7rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: clamp(0.7rem, 1.5vw, 0.8rem);
            transition: all 0.2s;
        }}
        .chart-toggle button:hover {{
            background: #444;
            border-color: #00ff00;
        }}
        .chart-toggle button.active {{
            background: #00ff00;
            color: #000;
            border-color: #00ff00;
        }}
        canvas {{ 
            max-width: 100%; 
            max-height: 40vh !important;
        }}
        .table-container {{
            max-height: 200px;
            overflow-y: auto;
            margin-top: 0.75rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: clamp(0.7rem, 1.5vw, 0.85rem);
        }}
        th {{
            background: #2a2a2a;
            color: #00ff00;
            padding: 0.5rem;
            text-align: left;
            border-bottom: 2px solid #333;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 0.4rem 0.5rem;
            border-bottom: 1px solid #333;
        }}
        tr:hover {{
            background: #252525;
        }}
        .show-table-btn {{
            width: 100%;
            margin-top: 0.75rem;
            background: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #333;
            padding: 0.4rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: clamp(0.75rem, 1.5vw, 0.85rem);
            transition: all 0.2s;
        }}
        .show-table-btn:hover {{
            background: #333;
            border-color: #00ff00;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 NetSpeed Usage Dashboard</h1>
            <div class="timestamp">Generated at: {html.escape(generated_at)}</div>
        </header>
        
        <div class="view-toggle">
            <button class="active" onclick="setView('all')">Show All</button>
            <button onclick="setView('yearly')">🗓️ Yearly Only</button>
            <button onclick="setView('monthly')">📅 Monthly Only</button>
            <button onclick="setView('daily')">📆 Daily Only</button>
            <button onclick="setView('hourly')">⏰ Hourly Only</button>
            <button onclick="setView('minute')">⏱️ Minute Only</button>
        </div>
        
        <div class="grid" id="grid">
            <div class="card" id="yearlyCard" data-key="yearly">
                <div class="card-header">
                    <h2 onclick="setView('yearly')" style="color: #ff6b6b;">🗓️ Yearly Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('yearly', 'line')">Line</button>
                        <button onclick="toggleChartType('yearly', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="yearlyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('yearly')">Show Data Table</button>
                <div class="table-container" id="yearlyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="monthlyCard" data-key="monthly">
                <div class="card-header">
                    <h2 onclick="setView('monthly')" style="color: #00ff00;">📅 Monthly Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('monthly', 'line')">Line</button>
                        <button onclick="toggleChartType('monthly', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="monthlyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('monthly')">Show Data Table</button>
                <div class="table-container" id="monthlyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="dailyCard" data-key="daily">
                <div class="card-header">
                    <h2 onclick="setView('daily')" style="color: #00ccff;">📆 Daily Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('daily', 'line')">Line</button>
                        <button onclick="toggleChartType('daily', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="dailyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('daily')">Show Data Table</button>
                <div class="table-container" id="dailyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="hourlyCard" data-key="hourly">
                <div class="card-header">
                    <h2 onclick="setView('hourly')" style="color: #ffcc00;">⏰ Hourly Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('hourly', 'line')">Line</button>
                        <button onclick="toggleChartType('hourly', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="hourlyChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('hourly')">Show Data Table</button>
                <div class="table-container" id="hourlyTable" style="display: none;"></div>
            </div>
            
            <div class="card" id="minuteCard" data-key="minute">
                <div class="card-header">
                    <h2 onclick="setView('minute')" style="color: #ff00ff;">⏱️ Minute-wise Usage</h2>
                    <div class="chart-toggle">
                        <button class="active" onclick="toggleChartType('minute', 'line')">Line</button>
                        <button onclick="toggleChartType('minute', 'bar')">Bar</button>
                    </div>
                </div>
                <canvas id="minuteChart"></canvas>
                <button class="show-table-btn" onclick="toggleTable('minute')">Show Data Table</button>
                <div class="table-container" id="minuteTable" style="display: none;"></div>
            </div>
        </div>
    </div>

    <script>
        const data = {json.dumps(data)};
        let currentView = 'all';
        const charts = {{}};
        const chartTypes = {{}};
        const colors = {{
            monthly: {{ main: '#00ff00', bg: '#00ff0033' }},
            daily: {{ main: '#00ccff', bg: '#00ccff33' }},
            hourly: {{ main: '#ffcc00', bg: '#ffcc0033' }},
            minute: {{ main: '#ff00ff', bg: '#ff00ff33' }}
        }};

        // Helper to format bytes to human readable
        function formatBytes(bytes) {{
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }}

        function createChart(key, type) {{
            const canvas = document.getElementById(key + 'Chart');
            const ctx = canvas.getContext('2d');
            const labels = data[key] ? data[key].map(item => item.label) : [];
            const values = data[key] ? data[key].map(item => item.total) : [];
            
            if (charts[key]) {{
                charts[key].destroy();
            }}
            
            // Ensure canvas is responsive
            canvas.style.width = '100%';
            canvas.style.height = 'auto';
            
            charts[key] = new Chart(ctx, {{
                type: type,
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Total Usage',
                        data: values,
                        borderColor: colors[key].main,
                        backgroundColor: colors[key].bg,
                        borderWidth: type === 'line' ? 3 : 2,
                        pointRadius: type === 'line' ? 4 : 0,
                        pointHoverRadius: 6,
                        fill: type === 'line',
                        tension: 0.4,
                        borderRadius: type === 'bar' ? 6 : 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    scales: {{
                        x: {{ 
                            grid: {{ color: '#333' }}, 
                            ticks: {{ color: '#888', maxRotation: 45, minRotation: 0 }} 
                        }},
                        y: {{ 
                            grid: {{ color: '#333' }}, 
                            ticks: {{ 
                                color: '#888',
                                callback: function(value) {{ return formatBytes(value); }}
                            }} 
                        }}
                    }},
                    plugins: {{
                        legend: {{ 
                            labels: {{ 
                                color: '#e0e0e0', 
                                font: {{ 
                                    size: window.innerWidth < 768 ? 12 : 14 
                                }} 
                            }} 
                        }},
                        tooltip: {{
                            backgroundColor: '#1a1a1a',
                            titleColor: '#00ff00',
                            bodyColor: '#e0e0e0',
                            borderColor: '#333',
                            borderWidth: 1,
                            callbacks: {{
                                label: function(context) {{
                                    return 'Usage: ' + formatBytes(context.raw);
                                }}
                            }}
                        }}
                    }}
                }}
            }});
            chartTypes[key] = type;
        }}

        function toggleChartType(key, type) {{
            const card = document.getElementById(key + 'Card');
            const buttons = card.querySelectorAll('.chart-toggle button');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            createChart(key, type);
        }}

        function toggleTable(key) {{
            const tableDiv = document.getElementById(key + 'Table');
            const btn = tableDiv.previousElementSibling;
            
            if (tableDiv.style.display === 'none') {{
                tableDiv.style.display = 'block';
                btn.textContent = 'Hide Data Table';
                
                let tableHTML = '<table><thead><tr><th>Time Period</th><th>Downloaded</th><th>Uploaded</th><th>Total</th></tr></thead><tbody>';
                const items = data[key] || [];
                items.forEach(item => {{
                    tableHTML += `<tr>
                        <td>${{item.label}}</td>
                        <td>${{formatBytes(item.downloaded)}}</td>
                        <td>${{formatBytes(item.uploaded)}}</td>
                        <td>${{formatBytes(item.total)}}</td>
                    </tr>`;
                }});
                tableHTML += '</tbody></table>';
                tableDiv.innerHTML = tableHTML;
            }} else {{
                tableDiv.style.display = 'none';
                btn.textContent = 'Show Data Table';
            }}
        }}
        
        function setView(view) {{
            currentView = view;
            
            // Update buttons
            document.querySelectorAll('.view-toggle button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event?.target?.classList.add('active');
            
            // Find which button corresponds to this view and mark as active
            document.querySelectorAll('.view-toggle button').forEach(btn => {{
                if ((view === 'all' && btn.textContent === 'Show All') || 
                    (view === 'yearly' && btn.textContent.includes('Yearly')) || 
                    (view === 'monthly' && btn.textContent.includes('Monthly')) || 
                    (view === 'daily' && btn.textContent.includes('Daily')) || 
                    (view === 'hourly' && btn.textContent.includes('Hourly')) || 
                    (view === 'minute' && btn.textContent.includes('Minute'))) {{
                    btn.classList.add('active');
                }}
            }});
            
            // Update card grid and sizing
            const cards = document.querySelectorAll('.card');
            const grid = document.getElementById('grid');
            const isSingleView = view !== 'all';
            
            cards.forEach(card => {{
                const key = card.dataset.key;
                if (isSingleView && key === view) {{
                    card.style.display = 'block';
                    card.style.maxWidth = '100%';
                }} else if (view === 'all') {{
                    card.style.display = 'block';
                    card.style.maxWidth = '100%'; // Reset for all view
                }} else {{
                    card.style.display = 'none';
                }}
            }});
            
            // Adjust grid columns based on view
            if (isSingleView) {{
                grid.style.gridTemplateColumns = '1fr';
            }} else {{
                grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(280px, 1fr))';
            }}
        }}

        // Update all charts function for static dashboard
        function updateAllCharts() {{
            ['yearly', 'monthly', 'daily', 'hourly', 'minute'].forEach(key => {{
                createChart(key, chartTypes[key] || 'line');
            }});
        }}
        
        // Initialize all charts
        ['yearly', 'monthly', 'daily', 'hourly', 'minute'].forEach(key => {{
            createChart(key, 'line');
        }});
        
        // Handle window resize to update charts
        window.addEventListener('resize', function() {{
            updateAllCharts();
        }});
    </script>
</body>
</html>'''

    report_path.write_text(report, encoding='utf-8')
    
    # Try to start a local web server for live updates
    try:
        port = get_free_port()
        DashboardRequestHandler.monitor = monitor
        
        server = HTTPServer(('127.0.0.1', port), DashboardRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        webbrowser.open(f'http://127.0.0.1:{port}')
    except Exception as e:
        print(f"Failed to start server: {e}")
        webbrowser.open(report_path.as_uri())


def open_daily_usage_browser(monitor):
    usage = monitor.get_daily_usage()
    generated_at = QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
    percent_used = f"{usage['percent_used']:.2f}%"
    report_path = Path(tempfile.gettempdir()) / 'netspeed_daily_usage.html'

    report = f'''<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>NetSpeed Daily Usage</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #111;
            color: #fff;
            margin: 0;
            padding: 40px;
        }}
        .card {{
            max-width: 520px;
            margin: 0 auto;
            background: #222;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 28px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        }}
        h1 {{
            color: #00ff00;
            margin-top: 0;
        }}
        .row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #333;
        }}
        .label {{
            color: #aaa;
        }}
        .value {{
            font-weight: bold;
        }}
        .progress {{
            height: 16px;
            background: #333;
            border-radius: 8px;
            overflow: hidden;
            margin-top: 16px;
        }}
        .bar {{
            height: 100%;
            background: #00ff00;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>NetSpeed Daily Usage</h1>
        <div class="row"><span class="label">Date</span><span class="value">{html.escape(usage['date'])}</span></div>
        <div class="row"><span class="label">Downloaded</span><span class="value">{format_data_size(usage['downloaded'])}</span></div>
        <div class="row"><span class="label">Uploaded</span><span class="value">{format_data_size(usage['uploaded'])}</span></div>
        <div class="row"><span class="label">Total Used</span><span class="value">{format_data_size(usage['total'])}</span></div>
        <div class="row"><span class="label">Daily Limit</span><span class="value">{format_data_size(usage['limit'])}</span></div>
        <div class="row"><span class="label">Limit Used</span><span class="value">{percent_used}</span></div>
        <div class="progress"><div class="bar" style="width: {min(usage['percent_used'], 100):.2f}%"></div></div>
        <p>Generated: {html.escape(generated_at)}</p>
    </div>
</body>
</html>'''

    report_path.write_text(report, encoding='utf-8')
    webbrowser.open(report_path.as_uri())


def start_tray(app, overlay, monitor=None):
    # Create tray icon
    tray_icon = QtWidgets.QSystemTrayIcon(app)
    
    # Create a simple icon
    icon_pixmap = QtGui.QPixmap(64, 64)
    icon_pixmap.fill(QtCore.Qt.black)
    painter = QtGui.QPainter(icon_pixmap)
    painter.setBrush(QtGui.QColor("#00FF00"))
    painter.drawRect(16, 16, 32, 32)
    painter.end()
    tray_icon.setIcon(QtGui.QIcon(icon_pixmap))
    tray_icon.setToolTip("NetSpeed Monitor")
    
    # Create context menu
    menu = QtWidgets.QMenu()
    
    show_action = menu.addAction("Show Overlay")
    show_action.triggered.connect(overlay.show)
    
    hide_action = menu.addAction("Hide Overlay")
    hide_action.triggered.connect(overlay.hide)
    
    # Check if report is enabled
    settings = QtCore.QSettings('NetSpeed', 'Overlay')
    report_enabled = settings.value('report_enabled', True, type=bool)
    
    if monitor is not None:
        menu.addSeparator()
        if report_enabled:
            usage_action = menu.addAction("View Daily Usage")
            usage_action.triggered.connect(lambda: open_daily_usage_browser(monitor))
    
    if report_enabled:
        menu.addSeparator()
        dashboard_action = menu.addAction("Usage Dashboard (Live)")
        dashboard_action.triggered.connect(lambda: open_usage_dashboard_browser(monitor))
    
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(menu)
    
    # Show tray icon
    tray_icon.show()
    
    return tray_icon
