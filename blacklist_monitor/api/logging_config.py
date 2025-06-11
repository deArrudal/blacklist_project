# =============================================================================
# File: logging_config.py
# Author: deArrudal
# Description: Configure logging parameters.
# Created: 2025-06-09
# License: GPL-3.0 License
# =============================================================================

import logging
import os

# Paths
LOG_PATH = "/var/log/blacklist_monitor/main.log"

# Ensure the blacklist directory exists
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
)
