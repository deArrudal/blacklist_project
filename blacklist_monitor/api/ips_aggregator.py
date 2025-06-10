# =============================================================================
# File: ips_aggregator.py
# Author: deArrudal
# Description: Aggregates multiple blacklist files into a deduplicated IP list.
# Created: 2025-05-19
# License: GPL-3.0 License
# =============================================================================

import os
import json
import logging
import re

from notifier import show_notification

# Paths
BLACKLIST_PATH = "/opt/blacklist_monitor/resources/blacklists"
OUTPUT_PATH = "/opt/blacklist_monitor/resources/blacklists/blacklist_ips.txt"
TEMP_PATH = "/opt/blacklist_monitor/resources/blacklists/blacklist_ips.old"

# Constants
IPV4_PATTERN = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}")
DEFAULT_NOTIFICATION_TYPE = "information"
LOGGER = logging.getLogger(__name__)


# Show notification on user's screen
def notify(message, notification_type=DEFAULT_NOTIFICATION_TYPE):
    data = json.dumps({"message": message, "type": notification_type})
    show_notification(data)


# Backup blacklist_ips.txt file if it exists
def backup_existing_output():
    if os.path.exists(OUTPUT_PATH):
        os.rename(OUTPUT_PATH, TEMP_PATH)


# Restore blacklist_ips.txt file from backup if it exists
def restore_backup():
    if os.path.exists(TEMP_PATH):
        os.rename(TEMP_PATH, OUTPUT_PATH)
        LOGGER.info("Restored previous blacklist from backup")

    else:
        raise FileNotFoundError("Backup file not found during restore")


# Aggregate all IPs from .txt blacklist files into blacklist_ips.txt
def aggregate_ips():
    ip_set = set()

    try:
        if not os.path.exists(BLACKLIST_PATH):
            notify(f"Blacklist directory not found: {BLACKLIST_PATH}", "error")
            LOGGER.critical(f"Blacklist directory not found: {BLACKLIST_PATH}")
            raise FileNotFoundError(f"Blacklist directory not found: {BLACKLIST_PATH}")

        backup_existing_output()

        for filename in os.listdir(BLACKLIST_PATH):
            if not filename.endswith(".txt"):
                continue

            filepath = os.path.join(BLACKLIST_PATH, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    for ip_line in file:
                        stripped_ip = ip_line.strip()
                        if IPV4_PATTERN.match(stripped_ip):
                            ip_set.add(stripped_ip)

                LOGGER.info(f"Processed file: {filename}")

            except OSError as read_error:
                LOGGER.warning(f"Error reading file {filename}: {read_error}")

        # Check if set is empty
        if not ip_set:
            LOGGER.error("No IPs found in blacklist files")
            raise ValueError("No IPs found in blacklist files")

        with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
            output_file.writelines(f"{ip}\n" for ip in sorted(ip_set))

        LOGGER.info(f"Aggregated {len(ip_set)} unique IPs into {OUTPUT_PATH}")

    except Exception as e:
        notify(f"Failed during Ip aggregation: {e}", "error")
        LOGGER.error(f"Failed during Ip aggregation: {e}")

        # Fallback: revert blacklist_ips.old and use as set
        try:
            restore_backup()

        except Exception as fallback_error:
            LOGGER.critical(f"Failed to restore backup: {fallback_error}")
            raise FileNotFoundError(f"Failed to restore backup: {fallback_error}")


if __name__ == "__main__":
    aggregate_ips()
