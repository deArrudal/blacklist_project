# =============================================================================
# File: notifier.py
# Author: deArrudal
# Description: Handles desktop notifications via system's notification service.
# Created: 2025-05-19
# License: GPL-3.0 License
# =============================================================================


# =============================================================================
# File: notifier.py
# Author: deArrudal
# Description: Handles desktop notifications via system's notification service.
# Created: 2025-05-19
# License: GPL-3.0 License
# =============================================================================

import json
import subprocess
import logging
import os

# Constants
DEFAULT_TITLE = "Blacklist Monitor"
DEFAULT_TYPE = "information"
URGENCY_MAP = {
    "information": "normal",
    "warning": "normal",
    "error": "critical",
}
LOGGER = logging.getLogger(__name__)


# Detect user bus path
def get_user_bus_address():
    uid = os.getuid()
    bus_path = f"/run/user/{uid}/bus"
    if os.path.exists(bus_path):
        return f"unix:path={bus_path}"

    return None


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

        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")

        bus_address = get_user_bus_address()
        if bus_address:
            env["DBUS_SESSION_BUS_ADDRESS"] = bus_address

        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, message],
            check=True,
            env=env,
        )

        LOGGER.info(f"Notification sent: {title} - {message}")

    except (json.JSONDecodeError, KeyError) as e:
        LOGGER.warning(f"Invalid notification format: {e}")

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Call process failed: {e}")

    except Exception as e:
        LOGGER.error(f"Unexpected error in show_notification: {e}")
