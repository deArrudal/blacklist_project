# Blacklist Monitor

An application module that automates the process of consolidating IP blacklists from pre-defined sources, and actively monitoring network traffic in real time for matches against these blacklisted IPs. Features:

- Downloads and normalizes multiple blacklist sources.
- Aggregates all IPs into a single deduplicated file.
- Uses a Bloom filter for fast, memory-efficient IP lookups.
- Monitors all network interfaces using `pcapy` and `dpkt`.
- Notifies the user of suspicious traffic via desktop notifications.
- Logs all events to disk for auditing.

## Project Structure

```
blacklist_monitor
├── api
│   ├── blacklists_fetcher.py
│   ├── bloom_filter.py
│   ├── ipc_manager.py
│   ├── ips_aggregator.py
│   ├── logging_config.py
│   ├── main.py
│   ├── notifier_daemon.py
│   └── ports_monitor.py
├── resources
│   ├── blacklist_ips.txt
│   ├── blacklist_monitor.service
│   ├── blacklist_notifier.service
│   ├── blacklist_sources.txt
│   ├── dependencies.txt
│   └── requirements.txt
└── install.sh
````

## Installation

### Prerequisites

- Debian or Ubuntu system
- Root access (`sudo` required)
- python3, python3-pip and python3-venv

1. Make the installation script executable

  ```bash
  chmod +x install.sh
  ```

2. Run the Installation Script

  ```bash
  sudo ./install.sh
  ````

This script performs the following steps:

* Copies the application files to `/opt/blacklist_monitor/`
* Creates necessary directories under `/var/log/blacklist_monitor/`
* Installs APT dependencies listed in `resources/dependencies.txt`
* Installs Python packages from `resources/requirements.txt`
* Sets up and enables a background notifier daemon for desktop notifications.

## Notification Daemon

This application includes a user-space daemon that listens for alert messages from the blacklist monitor and sends desktop notifications using notify-send.

- Runs as a systemd service: blacklist_notifier
- Reads from a named pipe: /run/blacklist_monitor/notifications.fifo
- Notifications are shown only if a graphical session is available.

You can check its status using:

  ```bash
  systemctl status blacklist_notifier --user
  ```

> Note: Ensure the daemon runs under the same user that owns the graphical session (typically your desktop user).

## Monitor manually

1. Run the monitor manually:

  ```bash
  python3 /opt/blacklist_monitor/api/main.py
  ```

## Configuration

Edit `resources/blacklist_sources.txt` to define custom blacklist sources. Each line must follow:

  ```
  <name> <url> <filetype>
  ```

E.g.:

  ```
  spamhaus https://www.spamhaus.org/drop/drop.txt txt
  ```

> **Note:** Ensure that each downloaded file contains one IP address per line.

## Logs

Log files are stored in:

* `/var/log/blacklist_monitor/blacklists_fetcher.log`
* `/var/log/blacklist_monitor/ips_aggregator.log`
* `/var/log/blacklist_monitor/ports_monitor.log`
* `/var/log/blacklist_monitor/main.log`
* `/var/log/blacklist_monitor/install.log`

## Authors

 - deArruda, Lucas [@SardinhaArruda](https://twitter.com/SardinhaArruda)

## Version History

* 1.0
    * Initial Release

## License

This project is licensed under the GPL-3.0 License - see the LICENSE.txt file for details