# =============================================================================
# File: notifier.py
# Author: deArrudal
# Description: Handles desktop notifications via system's notification service.
# Created: 2025-05-19
# License: GPL-3.0 License
# =============================================================================

# FIXME: Execute only for users and only when GUI exists.

import json
import subprocess
import logging

# Constants
DEFAULT_TITLE = "Blacklist Monitor"
DEFAULT_TYPE = "information"
URGENCY_MAP = {
    "information": "normal",
    "warning": "normal",
    "error": "critical",
}
LOGGER = logging.getLogger(__name__)


# Display a desktop notification using `notify-send` based on a JSON string
def show_notification(json_notification):
    try:
        # JSON keys: 'message', 'type' (information/warning/error), 'title'
        data = json.loads(json_notification)

        message = data.get("message", "")
        if not message:
            LOGGER.warning("Notification message is empty.")
            return

        notification_type = str(data.get("type", DEFAULT_TYPE)).lower()
        title = data.get("title", DEFAULT_TITLE)
        urgency = URGENCY_MAP.get(notification_type, "normal")

        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, message],
            check=True,
        )

        LOGGER.info(f"Notification sent: {title} - {message}")

    except (json.JSONDecodeError, KeyError) as e:
        LOGGER.warning(f"Invalid notification format: {e}")

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Call process failed: {e}")

    except Exception as e:
        LOGGER.error(f"Unexpected error in show_notification: {e}")
