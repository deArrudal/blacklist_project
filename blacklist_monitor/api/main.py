# =============================================================================
# File: main.py
# Author: deArrudal
# Description: Executes the full blacklist monitoring pipeline.
# Created: 2025-05-21
# License: GPL-3.0 License
# =============================================================================

import logging
import logging_config  # noqa: F401

from blacklists_fetcher import fetch_blacklists
from ips_aggregator import aggregate_ips
from ports_monitor import monitor_ports

# Constants
LOGGER = logging.getLogger(__name__)


def main():
    try:
        LOGGER.info("Fetching blacklists")
        fetch_blacklists()

        LOGGER.info("Consolidating blacklisted IPs")
        aggregate_ips()

        LOGGER.info("Starting port monitor")
        monitor_ports()

    except Exception as e:
        LOGGER.error(f"Error in execution: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
