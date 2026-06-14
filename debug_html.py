
from netspeed_tracker.monitor import NetMonitor
import json
import tempfile
from pathlib import Path

monitor = NetMonitor()
data = monitor.get_usage_dashboard_data()

# Let's manually generate the HTML snippet
html_data = json.dumps(data)
print('JSON data:', repr(html_data))
print('\n')

# Now, let's manually write a test file
test_file = Path(tempfile.gettempdir()) / 'test_debug.html'
test_content = f'''
<!doctype html>
<html>
<body>
<script>
const data = {html_data};
console.log('Data:', data);
document.write('<pre>' + JSON.stringify(data, null, 2) + '</pre>');
</script>
</body>
</html>'''

test_file.write_text(test_content, encoding='utf-8')
print(f'Test file written to {test_file}')

import webbrowser
webbrowser.open(test_file.as_uri())

# Okay, let's now test what open_usage_dashboard_browser is doing
import html
from PyQt5 import QtCore
from netspeed_tracker.tray import open_usage_dashboard_browser
generated_at = QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
report_path = Path(tempfile.gettempdir()) / 'netspeed_usage_dashboard.html'

# Let's manually write what tray.py is writing
from netspeed_tracker.tray import open_usage_dashboard_browser
# Wait no, let's copy tray.py's code temporarily here
report = f'''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NetSpeed Usage Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 NetSpeed Usage Dashboard</h1>
            <div class="timestamp">Generated at: {html.escape(generated_at)}</div>
        </header>
    </div>

    <script>
        const data = {json.dumps(data)};
        document.write('<pre>' + JSON.stringify(data, null, 2) + '</pre>');
    </script>
</body>
</html>'''

test_path = Path(tempfile.gettempdir()) / 'test_tray.html'
test_path.write_text(report, encoding='utf-8')
print(f'Test tray HTML written to {test_path}')
webbrowser.open(test_path.as_uri())

