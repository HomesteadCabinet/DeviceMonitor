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
                'name': 'Example IP',
                'value': '192.168.1.1',
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
sender_email = "noreply@example.net"
receiver_emails = ["example@example.net", "example.1@example.net"]
email_password = "roureyteww834n"
smtp_server = "smtp.gmail.com"
smtp_port = 587

# The credentials for the Google Sheets API
google_credentials = {
    "type": "service_account",
    "project_id": "devicemonitor-435921",
    "private_key_id": "something",
    "private_key": "something",
    "client_email": "device-monitor-hs@devicemonitor-435921.iam.gserviceaccount.com",
    "client_id": "something",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/device-monitor-hs%40devicemonitor-435921.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
google_sheet_id = "YOUR_GOOGLE_SHEET_ID"           # Replace with your Google Sheet ID
google_sheet_name = "Device Status"                # Name of the sheet/tab within the Google Sheet
