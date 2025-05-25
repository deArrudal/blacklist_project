# Network Blacklist Monitor

This module automates the process of downloading IP blacklists from pre-defined sources, consolidating them into a deduplicated list, and actively monitoring network traffic in real time for matches against these blacklisted IPs.

## Features

- Downloads and normalizes multiple blacklist sources.
- Aggregates all IPs into a single deduplicated file.
- Uses a Bloom filter for fast, memory-efficient IP lookups.
- Monitors all network interfaces using `pcapy` and `dpkt`.
- Notifies the user of suspicious traffic via desktop notifications.
- Logs all events to disk for auditing.

## Project Structure

```
./blacklist
├── api
│   ├── blacklists_fetcher.py
│   ├── bloom_filter.py
│   ├── ips_aggregator.py
│   ├── main.py
│   └── ports_monitor.py
├── execstart.py
├── install.py
├── README.md
├── resources
│   ├── blacklist_ips.txt
│   ├── blacklist.service
│   ├── blacklist_sources.txt
│   ├── dependencies.txt
│   └── requirements.txt
├── restart.py
├── start.py
└── stop.py
```

## Installation

### 1. Install APT Dependencies (Debian/Ubuntu)

```bash
sudo apt update && sudo apt install -y \
  libpcap-dev python3-dev python3-pip build-essential \
  libffi-dev libssl-dev libnotify-bin
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

Run the full pipeline with:

```bash
python3 main.py
```

This will:
1. Fetch IP blacklists from configured URLs.
2. Normalize and aggregate IPs into `blacklist_ips.txt`.
3. Launch the network interface monitor to detect suspicious traffic.

## Configuration

Edit `blacklist_sources.txt` to define custom blacklist sources. Each line should follow the format:

```
<name> <url> <filetype>
```

Example:

```
firehol https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset netset
spamhaus https://www.spamhaus.org/drop/drop.txt txt
```

Supported file types: `txt`, `csv`, `netset`.

**Please ensures that the source file has a single ip per line.**

## Logs

Log files are stored in:

- `/var/kfm/log/blacklist/`

## License

MIT License