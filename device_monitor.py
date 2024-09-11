# noqa

import os
import platform
import subprocess
import smtplib
import time
import socket
import csv
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# Threshold for slow response time (default 5 seconds = 5000 milliseconds)
RESPONSE_TIME_THRESHOLD = 5000

# Set TEMP_DIR to the directory where the script is located
TEMP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(TEMP_DIR, "device_scan_log.csv")
LAST_CLEARED_DATE_FILE = os.path.join(TEMP_DIR, "last_cleared_date.txt")

# List of devices to monitor with named URLs, IPs, directories, and ports
devices = {
    # "Production Coach": {
    #     "ips": [
    #         {'name': 'ANDI Station', 'value': "192.168.1.52"},
    #         {'name': 'BHX Station', 'value': "192.168.1.70"},
    #         {'name': 'Checking', 'value': "192.168.1.198"},
    #         {'name': 'Staging', 'value': "192.168.1.165"},
    #         {'name': 'Wrapping', 'value': "192.168.1.134"},
    #         {'name': 'Loading', 'value': "192.168.1.141"},
    #     ],
    # },
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
            {'name': 'vPC', 'value': "cloud.homesteadcabinet.net", 'ports': [13]},
            {'name': 'Rivermill', 'value': "cloud.homesteadcabinet.net", 'ports': [15]},
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
sender_email = "noreply@homesteadcabinet.net"
receiver_emails = ["brad@homesteadcabinet.net", "brad.1@homesteadcabinet.net"]  # Multiple recipients
email_password = "yxmlclxkclfsoydf"
smtp_server = "smtp.gmail.com"
smtp_port = 587


def clear_log_if_needed():
    """Clear the log file once per day."""
    today = datetime.now().strftime('%Y-%m-%d')

    # Check if the last cleared date is saved and if it's different from today
    if os.path.exists(LAST_CLEARED_DATE_FILE):
        with open(LAST_CLEARED_DATE_FILE, "r") as file:
            last_cleared_date = file.read().strip()
    else:
        last_cleared_date = None

    # Clear log if the last cleared date is not today
    if last_cleared_date != today:
        with open(LOG_FILE, "w", newline='') as log_file:
            writer = csv.writer(log_file)
            writer.writerow(["Date/Time", "Status", "Message"])  # Write header
        with open(LAST_CLEARED_DATE_FILE, "w") as file:
            file.write(today)


def log_scan(status, message):
    """Log the scan result in CSV format."""
    with open(LOG_FILE, "a", newline='') as log_file:
        writer = csv.writer(log_file)
        if status is None and message is None:
            writer.writerow(["----------", "----------", "----------"])
        else:
            writer.writerow([datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'), status, message])


def log_error(message):
    """Log errors in CSV format."""
    log_scan("ERROR", message)


def ping_device(ip_info, device_name):
    """Ping a device."""
    ip = ip_info['value']
    print(f"Starting ping check for {device_name} ({ip_info['name']}) - {ip}")
    try:
        command = ["ping", "-n", "1", ip] if platform.system().lower() == "windows" else ["ping", "-c", "1", ip]
        start_time = time.time()
        ping = subprocess.run(command, stdout=subprocess.PIPE)
        end_time = (time.time() - start_time) * 1000
        end_time = round(end_time, 2)
        if ping.returncode == 0:
            log_scan("SUCCESS", f"{device_name} ({ip_info['name']}) Ping successful: {ip}")
            print(f"Finished ping check for {device_name} ({ip_info['name']}) - Success ({end_time}ms)")
            return end_time
        else:
            log_scan("FAILED", f"{device_name} ({ip_info['name']}) Ping failed: {ip}")
            print(f"Finished ping check for {device_name} ({ip_info['name']}) - Failed ({end_time}ms)")
            return None
    except Exception as e:
        log_error(f"{device_name} ({ip_info['name']}) Ping error: {ip}. {e}")
        print(f"Finished ping check for {device_name} ({ip_info['name']}) - Error")
        return None


def check_port(ip_info, device_name):
    """Check specified ports."""
    ip = ip_info['value']
    if 'ports' not in ip_info:
        return

    for port in ip_info['ports']:
        print(f"Starting port check for {device_name} ({ip_info['name']}) - {ip}:{port}")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((ip, port))
            if result == 0:
                log_scan("SUCCESS", f"{device_name} ({ip_info['name']}) Port {port} is open on {ip}")
                print(f"Finished port check for {device_name} ({ip_info['name']}) - Port {port} Open")
            else:
                log_scan("FAILED", f"{device_name} ({ip_info['name']}) Port {port} is closed on {ip}")
                print(f"Finished port check for {device_name} ({ip_info['name']}) - Port {port} Closed")
            sock.close()
        except Exception as e:
            log_error(f"{device_name} ({ip_info['name']}) Port {port} check error on {ip}. {e}")
            print(f"Finished port check for {device_name} ({ip_info['name']}) - Error on Port {port}")


def check_http(url_info, device_name):
    """Check HTTP response."""
    url = url_info['value']
    print(f"Starting HTTP check for {device_name} ({url_info['name']}) - {url}")
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            log_scan("SUCCESS", f"{device_name} ({url_info['name']}) HTTP check successful: {url}")
            print(f"Finished HTTP check for {device_name} ({url_info['name']}) - Success")
            return (time.time() - start_time) * 1000
        else:
            log_scan("FAILED", f"{device_name} ({url_info['name']}) HTTP failed: {url}")
            print(f"Finished HTTP check for {device_name} ({url_info['name']}) - Failed")
            return None
    except Exception as e:
        log_error(f"{device_name} ({url_info['name']}) HTTP error: {url}. {e}")
        print(f"Finished HTTP check for {device_name} ({url_info['name']}) - Error")
        return None


def check_directory(directory_info, device_name):
    """Check if directory exists."""
    directory = directory_info['value']
    print(f"Starting directory check for {device_name} ({directory_info['name']}) - {directory}")
    if os.path.exists(directory):
        log_scan("SUCCESS", f"{device_name} ({directory_info['name']}) Directory check successful: {directory}")
        print(f"Finished directory check for {device_name} ({directory_info['name']}) - Success")
        return True
    else:
        log_scan("FAILED", f"{device_name} ({directory_info['name']}) Directory not found: {directory}")
        print(f"Finished directory check for {device_name} ({directory_info['name']}) - Failed")
        return False


def check_devices():
    """Check all devices."""
    offline_devices = {}
    high_response_devices = {}

    for device_name, resources in devices.items():
        # Check URLs
        if "urls" in resources:
            for url_info in resources["urls"]:
                response_time = check_http(url_info, device_name)
                if response_time is None:
                    offline_devices.setdefault(device_name, []).append(f"URL ({url_info['name']}): {url_info['value']}")
                elif response_time > RESPONSE_TIME_THRESHOLD:
                    high_response_devices.setdefault(device_name, []).append(f"URL ({url_info['name']}): {url_info['value']}")

        # Check IPs
        if "ips" in resources:
            for ip_info in resources["ips"]:
                response_time = ping_device(ip_info, device_name)
                if response_time is None:
                    offline_devices.setdefault(device_name, []).append(f"IP ({ip_info['name']}): {ip_info['value']}")
                elif response_time > RESPONSE_TIME_THRESHOLD:
                    high_response_devices.setdefault(device_name, []).append(f"IP ({ip_info['name']}): {ip_info['value']}")

                # Check Ports
                check_port(ip_info, device_name)

        # Check directories
        if "directories" in resources:
            for directory_info in resources["directories"]:
                if not check_directory(directory_info, device_name):
                    offline_devices.setdefault(device_name, []).append(f"Directory ({directory_info['name']}): {directory_info['value']}")

    return offline_devices, high_response_devices


def send_email(subject, body):
    """Send an email to multiple recipients."""
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(receiver_emails)  # Join all recipient emails with a comma
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, email_password)
        server.sendmail(sender_email, receiver_emails, message.as_string())
        server.quit()
        print(f"Email sent to {', '.join(receiver_emails)}")
    except Exception as e:
        log_error(f"Email failed: {e}")


def prepare_email_body(offline_devices, high_response_devices):
    """Prepare and send emails if there are offline or slow response devices."""
    if not offline_devices and not high_response_devices:
        print("All devices are online. No email sent.")
        return  # Don't send an email if everything is online

    email_body = ""

    # Handle offline devices
    if offline_devices:
        email_body += "Devices offline:\n"
        for device, issues in offline_devices.items():
            email_body += f"{device}:\n"
            for issue in issues:
                email_body += f"  {issue}\n"

    # Handle high response time devices
    if high_response_devices:
        email_body += "\nDevices with slow responses:\n"
        for device, issues in high_response_devices.items():
            email_body += f"{device}:\n"
            for issue in issues:
                email_body += f"  {issue}\n"

    # Include log file contents in the email body
    with open(LOG_FILE, "r") as log_file:
        email_body += "\n\nLog Details:\n"
        email_body += log_file.read()

    send_email("Device Monitoring Report", email_body)


def main():
    """Main function."""
    clear_log_if_needed()
    offline_devices, high_response_devices = check_devices()
    if offline_devices or high_response_devices:
        log_scan("SUMMARY", f"Offline: {offline_devices}, Slow: {high_response_devices}")
    log_scan(None, None)
    prepare_email_body(offline_devices, high_response_devices)


if __name__ == "__main__":
    main()
