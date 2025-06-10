# =============================================================================
# File: ips_aggregator.py
# Author: deArrudal
# Description: Aggregates multiple blacklist files into a deduplicated IP list.
# Created: 2025-05-19
# License: GPL-3.0 License
# =============================================================================

import os
import logging
import re

# Paths
TARGET_DIR = "/opt/blacklist_monitor/resources/blacklists"
BLACKLIST_FILE = "/opt/blacklist_monitor/resources/blacklists/blacklist_ips.txt"
BLACKLIST_OLD_FILE = "/opt/blacklist_monitor/resources/blacklists/blacklist_ips.old"

# Constants
IPV4_PATTERN = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}")
LOGGER = logging.getLogger(__name__)


# Backup blacklist_ips.txt file if it exists
def set_backup():
    if os.path.exists(BLACKLIST_FILE):
        os.rename(BLACKLIST_FILE, BLACKLIST_OLD_FILE)
        LOGGER.info("Backup file created")

    else:
        LOGGER.warning("Backup file not set")


# Restore blacklist_ips.txt file from backup if it exists
def restore_backup():
    if os.path.exists(BLACKLIST_OLD_FILE):
        os.rename(BLACKLIST_OLD_FILE, BLACKLIST_FILE)
        LOGGER.info("Restored previous blacklist from backup")

    else:
        LOGGER.critical("Backup file not found during restore")
        raise FileNotFoundError("Backup file not found during restore")


# Aggregate all IPs from .txt blacklist files into blacklist_ips.txt
def aggregate_ips():
    ip_set = set()

    try:
        # Validate if blacklists directory exists
        if not os.path.exists(TARGET_DIR):
            LOGGER.critical(f"Blacklist directory not found: {TARGET_DIR}")
            raise FileNotFoundError(f"Blacklist directory not found: {TARGET_DIR}")

        # Backup blacklist_ips.txt file if it exists
        set_backup()

        # Loop through IPs files
        for entry in os.listdir(TARGET_DIR):
            if not entry.endswith(".txt"):
                continue

            filepath = os.path.join(TARGET_DIR, entry)

            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    for line in file:
                        stripped_line = line.strip()
                        if IPV4_PATTERN.match(stripped_line):
                            ip_set.add(stripped_line)

                LOGGER.info(f"Processed file: {entry}")

            except OSError as read_error:
                LOGGER.warning(f"Error reading file {entry}: {read_error}")

        # Check if set is empty
        if not ip_set:
            LOGGER.critical("No IPs found in blacklist files")
            raise ValueError("No IPs found in blacklist files")

        # Save IPs set in blacklist_ips.txt file
        with open(BLACKLIST_FILE, "w", encoding="utf-8") as file:
            file.writelines(f"{ip}\n" for ip in ip_set)

        LOGGER.info(f"Aggregated {len(ip_set)} unique IPs into {BLACKLIST_FILE}")

    except Exception as e:
        LOGGER.error(f"Failed during Ip aggregation: {e}")

        # Fallback: Revert blacklist_ips.old and use as set
        try:
            restore_backup()

        except Exception as fallback_error:
            LOGGER.critical(f"Failed to restore backup: {fallback_error}")
            raise FileNotFoundError(f"Failed to restore backup: {fallback_error}")


if __name__ == "__main__":
    aggregate_ips()
