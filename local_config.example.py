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
                'name': 'Example IP With port',
                'value': '192.168.1.1',
                'ports': [80, 443]
            }, {
                'name': 'Example IP, only do a port scan',
                'value': '192.168.1.1',
                'ports': [80, 443],
                'onlyports': True
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
sender_email = "noreply@example.net"
receiver_emails = ["example@example.net", "example.1@example.net"]
email_password = "roureyteww834n"
smtp_server = "smtp.gmail.com"
smtp_port = 587
