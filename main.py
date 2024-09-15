import device_monitor as dm


def main():
    offline_devices, online_devices = dm.check_devices()
    dm.send_summary_email(offline_devices, online_devices)


if __name__ == "__main__":
    main()
