# DeviceMonitor

Brad's Device Monitor. This is a simple program that monitors the devices on a network.  It is designed to be run on any computer that has Python installed.

Configuration is done by usuing `local_config.py` file.
See the 'local_config.example.py' file for an example configuration or refer to the code below:


```python
# List of devices to monitor with named URLs, IPs, directories, and ports
devices = {
    "ExampleDevice": {
        "urls": [
            {
                'name': 'Example URL',
                'value': 'https://example.com',
            }
        ],
        "ips": [
            {
                'name': 'Example IP',
                'value': '192.168.1.1'
            }, {
                'name': 'Example IP, only do a port scan',
                'value': '192.168.1.1',
                'ports': [80, 443],
            },
        ],
        "directories": [
            {
                'name': 'Example Directory',
                'value': '/example/directory',
            }
        ],
    },
}

# Email settings
email_header = "Device Monitoring Report"
sender_name = "Device Monitor"
sender_email = "noreply@example.net"
receiver_emails = ["example@example.net", "example.1@example.net"]
email_password = "roureyteww834n"
smtp_server = "smtp.gmail.com"
smtp_port = 587
```
