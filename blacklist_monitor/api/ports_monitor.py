# =============================================================================
# File: ports_monitor.py
# Author: deArrudal
# Description: Analyzes live network traffic, comparing IPs against a blacklist
# to detect suspicious activity.
# Created: 2025-05-19
# License: GPL-3.0 License
# =============================================================================

import threading
import pcapy
import dpkt
import socket
import json
import logging

from bloom_filter import BloomFilter
from notifier import show_notification

# Paths
BLACKLIST_FILE = "/opt/blacklist_monitor/resources/blacklists/blacklist_ips.txt"

# Constants
DEFAULT_NOTIFICATION_TYPE = "information"
LOGGER = logging.getLogger(__name__)

SNAP_LEN = 65536
PROMISCUOUS = 1
TIMEOUT_MS = 0


# Show notification on user's screen
def notify(message, notification_type=DEFAULT_NOTIFICATION_TYPE):
    data = json.dumps({"message": message, "type": notification_type})
    show_notification(data)


# Convert an IP address in binary format to a string using Python - extracted from socket documentation
def inet_to_str(inet):
    try:
        return socket.inet_ntop(socket.AF_INET, inet)

    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)


# Handle capture packet - extracted from dpkt documentation
def packet_handler(ip_set, bloom_filter):
    def handler(header, data):
        try:
            # Unpack the Ethernet frame (mac src/dst, ethertype)
            eth = dpkt.ethernet.Ethernet(data)

            # Make sure the Ethernet frame contains an IP packet
            if not isinstance(eth.data, dpkt.ip.IP):
                return

            # Access the data within the Ethernet frame (the IP packet)
            ip = eth.data
            src_ip = inet_to_str(ip.src)

            # Bloom filter check before full set check
            if src_ip in bloom_filter:
                # Confirm if not a false positive
                if src_ip in ip_set:
                    # TODO: Add to firewall rule
                    notify(f"Suspicious IP detected: {src_ip}", "warning")
                    LOGGER.warning(f"Suspicious IP detected: {src_ip}")

        except Exception as e:
            LOGGER.error(f"Packet error: {e}")

    return handler


# Monitor a given interface - extracted from pcapy documentation
def monitor(interface, handler):
    try:
        # Obtain a packet capture descriptor to look at packets on the network
        # open_live(device, snaplength, promiscuous, timeout_ms)
        LOGGER.info(f"Starting monitor on interface: {interface}")
        capture = pcapy.open_live(interface, SNAP_LEN, PROMISCUOUS, TIMEOUT_MS)

        # Collect and process packets
        while True:
            capture.dispatch(1, handler)

    except Exception as e:
        notify(f"Monitor error on interface {interface}: {e}", "error")
        LOGGER.error(f"Monitor error on interface {interface}: {e}")


# Load the blacklisted IPs
def load_blacklist(filepath):
    with open(filepath, encoding="utf-8") as file:
        return {line.strip() for line in file if line.strip()}


def monitor_ports():
    try:
        # Load the blacklisted IPs
        ip_set = load_blacklist(BLACKLIST_FILE)
        LOGGER.info(f"Loaded IP blacklist from {BLACKLIST_FILE}")

        if not ip_set:
            LOGGER.error("Blacklist file return an empty IP list")
            raise Exception("Blacklist file return an empty IP list")

        # Populate bloom filter with loaded IPs
        bloom_filter = BloomFilter(items_count=len(ip_set))
        for ip in ip_set:
            bloom_filter.add(ip)
        LOGGER.info("Bloom filter populated")

        # Create the packet handler closure
        handler = packet_handler(ip_set, bloom_filter)

        # Obtain the list of available network devices
        interfaces = [i for i in pcapy.findalldevs() if i.startswith("enp0s")]
        threads = []

        if not interfaces:
            LOGGER.error("No network interfaces found to monitor")
            raise Exception("No network interfaces found to monitor")

        # Set a thread for each interface
        for interface in interfaces:
            t = threading.Thread(
                target=monitor,
                args=(interface, handler),
                daemon=True,
            )
            t.start()
            threads.append(t)

        # Keep main thread alive as long as child threads are running
        for t in threads:
            t.join()

    except Exception as e:
        notify(f"Fatal error in port monitor: {e}", "error")
        LOGGER.critical(f"Fatal error in port monitor: {e}")


if __name__ == "__main__":
    monitor_ports()
