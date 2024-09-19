# Python 2.7 compatibile code

from __future__ import print_function, division, unicode_literals
import os
import platform
import subprocess
import smtplib
import local_config
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import requests
import time
import socket

ONLINE = "Online"
OFFLINE = "Offline"

sender_email = local_config.sender_email
sender_name = local_config.sender_name
receiver_emails = local_config.receiver_emails
email_password = local_config.email_password
smtp_server = local_config.smtp_server
smtp_port = local_config.smtp_port

google_credentials = local_config.google_credentials
google_sheet_id = local_config.google_sheet_id
google_sheet_name = local_config.google_sheet_name

devices = local_config.devices
RESPONSE_TIME_THRESHOLD = 5000

ws = None
cached_records = None  # Cache to store records
last_cache_time = None  # Time when the cache was last updated
CACHE_DURATION = 60  # Cache duration in seconds, adjust as needed


def initialize_log():
    global ws
    """Initialize the Google Sheet log if it doesn't exist."""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        credentials = Credentials.from_service_account_info(google_credentials, scopes=scopes)
        # Authorize with Google Sheets API
        gc = gspread.authorize(credentials)
    except Exception as e:
        print("Failed to authenticate with Google Sheets API:", e)
        return None

    try:
        sh = gc.open_by_key(google_sheet_id)
        try:
            ws = sh.worksheet(google_sheet_name)
            print("Worksheet '{}' found and loaded successfully.".format(google_sheet_name))
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=google_sheet_name, rows="1000", cols="8")
            print("Worksheet '{}' created.".format(google_sheet_name))
    except gspread.SpreadsheetNotFound:
        print("Spreadsheet with ID {} not found.".format(google_sheet_id))
        ws = None
    except Exception as e:
        print("Error accessing Google Sheets:", e)
        ws = None

    headers = [
        "Device Name",
        "Resource",
        "Type",
        "Value",
        "Status",
        "Previous Status",
        "Last Checked",
        "Offline Since",
        "Online Since"
    ]

    if ws:
        existing_headers = ws.row_values(1)
        if not existing_headers:
            try:
                ws.append_row(headers)
                print("Headers added to the Google Sheet.")
            except Exception as e:
                print("Failed to add headers to the Google Sheet:", e)
    else:
        print("Error: Worksheet is None.")

    return ws


def load_records_from_cache():
    """Load records from cache or fetch from Google Sheets if the cache is expired."""
    global cached_records, last_cache_time

    current_time = time.time()

    # If cache is empty or expired, fetch fresh data from Google Sheets
    if cached_records is None or (last_cache_time is None) or (current_time - last_cache_time > CACHE_DURATION):
        print("Fetching fresh records from Google Sheets...")
        try:
            cached_records = ws.get_all_records()  # Fetch fresh data
            last_cache_time = current_time
        except Exception as e:
            print("Failed to fetch records from Google Sheets:", e)
            cached_records = None

    return cached_records


def update_device_status(device_name, resource_name, resource_type, status, value):
    global ws, cached_records
    """Update or insert device status in the Google Sheet log using batched updates."""
    current_time = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')

    # Load cached records
    records = load_records_from_cache()
    if records is None:
        print("Unable to update {}, cached records are not available.".format(device_name))
        return

    # Find the row to update based on device_name, resource_name, and resource_type
    row_to_update = None
    for i, record in enumerate(records):
        if (record["Device Name"] == device_name and
            record["Resource"] == resource_name and
            record["Type"] == resource_type):
            row_to_update = i + 2  # +2 because records is 0-indexed and sheet row starts at 1 (header row)
            break

    if row_to_update:
        # If the device/resource is found, batch all updates for this row
        updates = [
            {'range': 'D{}'.format(row_to_update), 'values': [[value]]},  # Update "Value"
            {'range': 'E{}'.format(row_to_update), 'values': [[status]]},  # Update "Status"
            {'range': 'G{}'.format(row_to_update), 'values': [[current_time]]},  # Update "Last Checked"
        ]

        # Update "Previous Status" and handle the status changes for "Offline Since" and "Online Since"
        previous_status = ws.cell(row_to_update, 5).value  # Column 5 is 'Status'
        updates.append({'range': 'F{}'.format(row_to_update), 'values': [[previous_status]]})  # Update "Previous Status"

        if previous_status != status:
            if status == OFFLINE:
                updates.append({'range': 'H{}'.format(row_to_update), 'values': [[current_time]]})  # Update "Offline Since"
                updates.append({'range': 'I{}'.format(row_to_update), 'values': [[""]]})  # Clear "Online Since"
            elif status == ONLINE:
                updates.append({'range': 'I{}'.format(row_to_update), 'values': [[current_time]]})  # Update "Online Since"
                updates.append({'range': 'H{}'.format(row_to_update), 'values': [[""]]})  # Clear "Offline Since"

        try:
            ws.batch_update(updates)  # Batch all updates in one API call
            print("Updated row {} for {} - {}.".format(row_to_update, device_name, resource_name))
            cached_records[row_to_update - 2]["Status"] = status  # Update the cached data
        except Exception as e:
            print("Failed to update row {} for {}: {}".format(row_to_update, device_name, e))
    else:
        # If the device/resource is not found, append a new row
        offline_since = current_time if status == OFFLINE else ""
        online_since = current_time if status == ONLINE else ""
        new_row = [
            device_name,
            resource_name,
            resource_type,
            value,
            status,
            "",
            current_time,
            offline_since,
            online_since
        ]
        try:
            ws.append_row(new_row)
            print("Appended new row for {} - {}.".format(device_name, resource_name))
            # Update cache by adding the new row
            cached_records.append({
                "Device Name": device_name,
                "Resource": resource_name,
                "Type": resource_type,
                "Value": value,
                "Status": status,
                "Previous Status": "",
                "Last Checked": current_time,
                "Offline Since": offline_since,
                "Online Since": online_since
            })
        except Exception as e:
            print("Failed to append new row for {} - {}: {}".format(device_name, resource_name, e))


def get_previous_status(device_name, resource_name, resource_type):
    global cached_records

    """Retrieve the previous status of a device/resource from the cached Google Sheet log."""
    records = load_records_from_cache()
    if records is None:
        print("Unable to retrieve status for {}, cached records are not available.".format(device_name))
        return None

    for record in records:
        if (record["Device Name"] == device_name and
            record["Resource"] == resource_name and
            record["Type"] == resource_type):
            return record["Status"]

    return None


def ping_device(ip_info, device_name):
    """Ping a device and return its status and response time."""
    ip = ip_info['value']
    print("Starting ping check for {} ({} - {})".format(device_name, ip_info['name'], ip))
    try:
        start_time = time.time()
        command = ["ping", "-n", "1", ip] if platform.system().lower() == "windows" else ["ping", "-c", "1", ip]
        ping = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        if ping.returncode == 0:
            print("    {} ({} - {}) - {} ({}ms)".format(device_name, ip_info['name'], ip, ONLINE, end_time))
            return ONLINE, end_time
        else:
            print("    {} ({} - {}) - {}".format(device_name, ip_info['name'], ip, OFFLINE))
            return OFFLINE, None
    except Exception as e:
        print("    {} ({} - {}) - {} - Error: {}".format(device_name, ip_info['name'], ip, OFFLINE, e))
        return OFFLINE, None


def check_port(ip_info, device_name):
    """Check specified ports and return status."""
    ip = ip_info['value']
    if 'ports' not in ip_info:
        return ONLINE, None  # If no ports specified, assume online

    port_statuses = []
    for port in ip_info['ports']:
        print("Starting port check for {} ({} - {}:{})".format(device_name, ip_info['name'], ip, port))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3 seconds timeout
            start_time = time.time()
            result = sock.connect_ex((ip, port))
            end_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            if result == 0:
                print("    {} ({} - {}) Port {} - {} ({}ms)".format(device_name, ip_info['name'], ip, port, ONLINE, end_time))
                port_statuses.append((port, ONLINE, end_time))
            else:
                print("    {} ({} - {}) Port {} - {}".format(device_name, ip_info['name'], ip, port, OFFLINE))
                port_statuses.append((port, OFFLINE, None))
            sock.close()
        except Exception as e:
            print("    {} ({} - {}) Port {} - {} - Error: {}".format(device_name, ip_info['name'], ip, port, OFFLINE, e))
            sock.close()
            port_statuses.append((port, OFFLINE, None))
    # For simplicity, return the first port status. Adjust if needed.
    if port_statuses:
        return port_statuses[0][1], port_statuses[0][2]
    return OFFLINE, None


def check_http(url_info, device_name):
    """Check HTTP response and return its status and response time."""
    url = url_info['value']
    print("Starting HTTP check for {} ({}) - {}".format(device_name, url_info['name'], url))
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        if response.status_code == 200:
            print("    {} ({}) - {} ({}ms)".format(device_name, url_info['name'], ONLINE, end_time))
            return ONLINE, end_time
        else:
            print("    {} ({}) - {}".format(device_name, url_info['name'], OFFLINE))
            return OFFLINE, None
    except Exception as e:
        print("    {} ({}) - {} - Error: {}".format(device_name, url_info['name'], OFFLINE, e))
        return OFFLINE, None


def check_directory(directory_info, device_name):
    """Check if directory exists and return its status."""
    directory = directory_info['value']
    print("Starting directory check for {} ({}) - {}".format(device_name, directory_info['name'], directory))
    try:
        if os.path.exists(directory):
            print("    {} ({}) - {}".format(device_name, directory_info['name'], ONLINE))
            return ONLINE, None  # No response time for directories
        else:
            print("    {} ({}) - {}".format(device_name, directory_info['name'], OFFLINE))
            return OFFLINE, None
    except Exception as e:
        print("    {} ({}) - {} - Error: {}".format(device_name, directory_info['name'], OFFLINE, e))
        return OFFLINE, None


def send_summary_email(offline_devices, online_devices):
    """Send a single email with a summary of offline and online devices, including response times."""
    if not offline_devices and not online_devices:
        print("No changes in status since last run... all done.")
        return

    offline_count = len(offline_devices)
    online_count = len(online_devices)
    body = ""

    subject_parts = []
    if offline_count > 0:
        offline_label = "Device" if offline_count == 1 else "Devices"
        subject_parts.append("{} New Offline {}".format(offline_count, offline_label))
    if online_count > 0:
        online_label = "Device" if online_count == 1 else "Devices"
        subject_parts.append("{} New Online {}".format(online_count, online_label))

    subject = "Devices"
    if subject_parts:
        subject += " - " + " and ".join(subject_parts)

    if offline_devices:
        body += "Devices that went offline:\n"
        for device, resource, value, response_time in offline_devices:
            if response_time:
                append = " - {:.2f}ms".format(response_time)
            else:
                append = ""
            body += "{} - {} ({}){}\n".format(device, resource, value, append)

    if online_devices:
        body += "\nDevices that came back online:\n"
        for device, resource, value, response_time in online_devices:
            if response_time:
                append = " - {:.2f}ms".format(response_time)
            else:
                append = ""
            body += "{} - {} ({}){}\n".format(device, resource, value, append)

    google_sheet_link = "https://docs.google.com/spreadsheets/d/{}/edit#gid=0".format(google_sheet_id)
    body += "\n\n\nGoogle Sheet: {}".format(google_sheet_link)

    send_email(subject, body)


def send_email(subject, body):
    """Send an email to notify the recipient of status changes."""
    print("Sending email to {}".format(", ".join(receiver_emails)))
    print("Subject: {}".format(subject))
    print("Body:\n{}".format(body))
    message = MIMEMultipart()
    message["From"] = formataddr((sender_name, sender_email))
    message["To"] = ", ".join(receiver_emails)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, email_password)
        server.sendmail(sender_email, receiver_emails, message.as_string())
        server.quit()
        print("Email sent to {}".format(", ".join(receiver_emails)))
    except Exception as e:
        print("Failed to send email:", e)


def check_devices():
    """Check the status of all devices and collect any that changed status."""
    offline_devices = []
    online_devices = []

    for device_name, resources in devices.iteritems():  # Use iteritems for Python 2
        # Check URLs
        if "urls" in resources:
            for url_info in resources["urls"]:
                current_status, response_time = check_http(url_info, device_name)
                previous_status = get_previous_status(device_name, url_info['name'], "URL")

                # Update device status before handling status changes
                update_device_status(device_name, url_info['name'], "URL", current_status, url_info['value'])

                # Handle the case when it's the first run (no previous status)
                if previous_status is None:
                    if current_status == OFFLINE:
                        offline_devices.append((device_name, url_info['name'], url_info['value'], response_time))
                    elif current_status == ONLINE:
                        online_devices.append((device_name, url_info['name'], url_info['value'], response_time))
                    continue

                # Handle status transitions
                if previous_status == ONLINE and current_status == OFFLINE:
                    offline_devices.append((device_name, url_info['name'], url_info['value'], response_time))
                elif previous_status == OFFLINE and current_status == ONLINE:
                    online_devices.append((device_name, url_info['name'], url_info['value'], response_time))

        # Check IPs
        if "ips" in resources:
            for ip_info in resources["ips"]:
                if ip_info.get('ports'):
                    current_status, response_time = check_port(ip_info, device_name)
                else:
                    current_status, response_time = ping_device(ip_info, device_name)
                previous_status = get_previous_status(device_name, ip_info['name'], "IP")

                # Update device status before handling status changes
                update_device_status(device_name, ip_info['name'], "IP", current_status, ip_info['value'])

                # Handle the case when it's the first run (no previous status)
                if previous_status is None:
                    if current_status == OFFLINE:
                        offline_devices.append((device_name, ip_info['name'], ip_info['value'], response_time))
                    elif current_status == ONLINE:
                        online_devices.append((device_name, ip_info['name'], ip_info['value'], response_time))
                    continue

                # Handle status transitions
                if previous_status == ONLINE and current_status == OFFLINE:
                    offline_devices.append((device_name, ip_info['name'], ip_info['value'], response_time))
                elif previous_status == OFFLINE and current_status == ONLINE:
                    online_devices.append((device_name, ip_info['name'], ip_info['value'], response_time))

        # Check directories
        if "directories" in resources:
            for directory_info in resources["directories"]:
                current_status, response_time = check_directory(directory_info, device_name)
                previous_status = get_previous_status(device_name, directory_info['name'], "Directory")

                # Update device status before handling status changes
                update_device_status(device_name, directory_info['name'], "Directory", current_status, directory_info['value'])

                # Handle the case when it's the first run (no previous status)
                if previous_status is None:
                    if current_status == OFFLINE:
                        offline_devices.append((device_name, directory_info['name'], directory_info['value'], response_time))
                    elif current_status == ONLINE:
                        online_devices.append((device_name, directory_info['name'], directory_info['value'], response_time))
                    continue

                # Handle status transitions
                if previous_status == ONLINE and current_status == OFFLINE:
                    offline_devices.append((device_name, directory_info['name'], directory_info['value'], response_time))
                elif previous_status == OFFLINE and current_status == ONLINE:
                    online_devices.append((device_name, directory_info['name'], directory_info['value'], response_time))

    return offline_devices, online_devices


initialize_log()
