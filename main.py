import device_monitor as dm


dm.devices = {
    "Production Coach": {
        "ips": [
            {'name': 'ANDI Station', 'value': "192.168.1.52"},
            {'name': 'BHX Station', 'value': "192.168.1.70"},
            {'name': 'Checking', 'value': "192.168.1.198"},
            {'name': 'Staging', 'value': "192.168.1.165"},
            {'name': 'Wrapping', 'value': "192.168.1.134"},
            {'name': 'Loading', 'value': "192.168.1.141"},
        ],
    },
    "LiteBeams": {
        "ips": [
            {'name': 'Beam1', 'value': "192.168.1.250"},
            {'name': 'Beam2', 'value': "192.168.1.251"},
        ],
    },
    "Reolink_NVR": {
        "ips": [{'name': 'NVR', 'value': "192.168.1.28"}],
    },
    "Server 2019": {
        "ips": [{'name': 'Server 2019', 'value': "192.168.1.35"}],
    },
    "Linux Server": {
        "ips": [{'name': 'Linux Server', 'value': "192.168.1.84"}],
    },
    "Virtual Machines": {
        "ips": [
            {'name': 'vPC', 'value': "cloud.homesteadcabinet.net", 'ports': [13], 'onlyports': True},
            {'name': 'Rivermill', 'value': "cloud.homesteadcabinet.net", 'ports': [15], 'onlyports': True},
        ],
    },
    "Web Sites": {
        "urls": [
            {"name": "Homestead Cabinet", "value": "https://homesteadcabinet.net"},
            {"name": "Homestead Bidding", "value": "https://orders.homesteadcabinet.net"},
            {"name": "Homestead Cabinet Cloud", "value": "https://cloud.homesteadcabinet.net"},
        ],
    },
}

# Email settings
dm.sender_email = "noreply@homesteadcabinet.net"
dm.receiver_emails = ["brad@homesteadcabinet.net", "brad.1@homesteadcabinet.net"]  # Multiple recipients
dm.email_password = "yxmlclxkclfsoydf"
dm.smtp_server = "smtp.gmail.com"
dm.smtp_port = 587


def main():
    """Main function."""
    dm.clear_log_if_needed()
    offline_devices, high_response_devices = dm.check_devices()
    if offline_devices or high_response_devices:
        dm.log_scan("SUMMARY", f"Offline: {offline_devices}, Slow: {high_response_devices}")
    dm.log_scan(None, None)
    dm.prepare_email_body(offline_devices, high_response_devices)


if __name__ == "__main__":
    main()
