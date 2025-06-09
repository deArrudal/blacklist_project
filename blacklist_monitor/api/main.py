# =============================================================================
# File: main.py
# Author: deArrudal
# Description: Executes the full blacklist monitoring pipeline.
# Created: 2025-05-21
# License: GPL-3.0 License
# =============================================================================

import json
import logging

from notifier import show_notification
from blacklists_fetcher import fetch_blacklists
from ips_aggregator import aggregate_ips
from ports_monitor import monitor_ports

# Paths
LOG_PATH = "/var/log/blacklist_monitor/main.log"

# Constants
DEFAULT_NOTIFICATION_TYPE = "information"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Show notification on user's screen
def notify(message, notification_type=DEFAULT_NOTIFICATION_TYPE):
    data = json.dumps({"message": message, "type": notification_type})
    show_notification(data)


def main():
    try:
        logging.info("Fetching blacklists")
        fetch_blacklists()

        logging.info("Consolidating blacklisted IPs")
        aggregate_ips()

        notify("Starting port monitor")
        logging.info("Starting port monitor")
        monitor_ports()

    except Exception as e:
        logging.error(f"[!] Error in execution: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
