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
import logging
import json
import subprocess

from queue import Queue
from bloom_filter import BloomFilter
from ipc_manager import NOTIFICATION_PIPE_PATH

# Paths
BLACKLIST_FILE = "/opt/blacklist_monitor/resources/blacklists/blacklist_ips.txt"

# Constants
DEFAULT_NOTIFICATION_TYPE = "information"
LOGGER = logging.getLogger(__name__)

SNAP_LEN = 65536
PROMISCUOUS = 1
TIMEOUT_MS = 0

WORKER_COUNT = 5
packet_queue = Queue()


# Send notification to user via IPC pipe
def notify(message, type="information"):
    data = {
        "message": message,
        "type": type,
    }

    try:
        with open(NOTIFICATION_PIPE_PATH, "w") as fifo:
            fifo.write(json.dumps(data) + "\n")

    except Exception as e:
        LOGGER.warning(f"Failed to send notification: {e}")


# Convert an IP address in binary format to a string using Python - extracted from socket documentation
def inet_to_str(inet):
    try:
        return socket.inet_ntop(socket.AF_INET, inet)

    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)


# Bloc IP using nftables if not present already
def block_ip(ip_address):
    try:
        # Check if rule already exists
        check_cmd = ["sudo", "nft", "list", "set", "inet", "filter", "blocked_ips"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            LOGGER.error("Blocked IP set does not exist in nftables")
            return

        if ip_address in result.stdout:
            LOGGER.info(f"IP {ip_address} is already blocked by nftables")
            return

        # Add the IP to the nftables set
        cmd = [
            "sudo",
            "nft",
            "add",
            "element",
            "inet",
            "filter",
            "blocked_ips",
            f"{{ {ip_address} }}",
        ]
        subprocess.run(cmd, check=True)
        notify(f"IP {ip_address} blocked via nftables", "warning")
        LOGGER.warning(f"IP {ip_address} blocked via nftables")

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Failed to block IP {ip_address} via nftables: {e}")


# Handle captured packet - extracted from dpkt documentation
def process_packet(data, ip_set, bloom_filter):
    try:
        # Unpack the Ethernet frame (mac src/dst, ethertype)
        eth = dpkt.ethernet.Ethernet(data)

        # Make sure the Ethernet frame contains an IP packet
        if not isinstance(eth.data, dpkt.ip.IP):
            return

        # Access the data within the Ethernet frame (the IP packet)
        ip = eth.data
        src_ip = inet_to_str(ip.src)

        # Extract target port
        if isinstance(ip.data, (dpkt.tcp.TCP, dpkt.udp.UDP)):
            port = ip.data.dport
        else:
            port = "N/A"

        # Bloom filter check before full set check
        if src_ip in bloom_filter:
            # Confirm if not a false positive
            if src_ip in ip_set:
                block_ip(src_ip)
                notify(f"Suspicious IP detected: {src_ip}, Port: {port}", "warning")
                LOGGER.warning(f"Suspicious IP detected: {src_ip}, Port: {port}")

    except Exception as e:
        LOGGER.error(f"Packet error: {e}")


# Worker threads
def packet_worker(ip_set, bloom_filter):
    while True:
        # Get packet from queue
        data = packet_queue.get()
        if data is None:
            break

        # Process packet
        process_packet(data, ip_set, bloom_filter)

        packet_queue.task_done()


# Monitor a given interface - extracted from pcapy documentation
def monitor(interface):
    try:
        # Obtain a packet capture descriptor to look at packets on the network
        # open_live(device, snaplength, promiscuous, timeout_ms)
        LOGGER.info(f"Starting monitor on interface: {interface}")
        capture = pcapy.open_live(interface, SNAP_LEN, PROMISCUOUS, TIMEOUT_MS)

        # Collect and queue the packets
        def enqueue(_, data):
            packet_queue.put(data)

        capture.loop(-1, enqueue)

    except Exception as e:
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

        # Start packet processing workers
        for worker in range(WORKER_COUNT):
            t = threading.Thread(
                target=packet_worker, args=(ip_set, bloom_filter), daemon=True
            )
            t.start()

        # Obtain the list of available network devices
        interfaces = [i for i in pcapy.findalldevs() if i.startswith("enp0s")]
        if not interfaces:
            LOGGER.error("No network interfaces found to monitor")
            raise Exception("No network interfaces found to monitor")

        # Set a thread for each interface
        threads = []
        for interface in interfaces:
            t = threading.Thread(target=monitor, args=(interface,), daemon=True)
            t.start()
            threads.append(t)

        # Keep main thread alive as long as child threads are running
        for t in threads:
            t.join()

    except Exception as e:
        LOGGER.critical(f"Fatal error in port monitor: {e}")


if __name__ == "__main__":
    monitor_ports()
