# =============================================================================
# File: notifier_daemon.py
# Author: deArrudal
# Description: Listens for notification requests and sends desktop notifications.
# Created: 2025-06-10
# License: GPL-3.0 License
# =============================================================================

import os
import json
import stat
import subprocess
import logging

# Import the shared pipe path from the new manager file
from ipc_manager import NOTIFICATION_PIPE_PATH

# Notify constants
DEFAULT_TITLE = "Blacklist Monitor"
DEFAULT_TYPE = "information"
URGENCY_MAP = {
    "information": "normal",
    "warning": "normal",
    "error": "critical",
}

# Logging setup for the user service
LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
)


# Send a desktop notification using notify-send
def send_desktop_notification(message, notification_type, title):
    try:
        urgency = URGENCY_MAP.get(notification_type, "normal")

        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, message],
            check=True,
            capture_output=True,
            text=True,
        )

        LOGGER.info(f"Notification sent: {title} - {message}")

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"notify-send failed: {e}", exc_info=True)

    except Exception as e:
        LOGGER.error(f"Unexpected error sending notification: {e}")


# Wait for notification messages from the FIFO
def start_notifier_daemon():
    LOGGER.info(f"Notifier daemon starting. Listening on {NOTIFICATION_PIPE_PATH}")

    while True:
        try:
            # Check if the pipe exists
            if not os.path.exists(NOTIFICATION_PIPE_PATH):
                LOGGER.warning(
                    f"Notification pipe not found at {NOTIFICATION_PIPE_PATH}"
                )
                continue

            # Check if path is for a pipe
            if not stat.S_ISFIFO(os.stat(NOTIFICATION_PIPE_PATH).st_mode):
                LOGGER.critical(
                    f"Path '{NOTIFICATION_PIPE_PATH}' exists but is not a FIFO"
                )
                return

            with open(NOTIFICATION_PIPE_PATH, "r") as fifo:
                for line in fifo:
                    try:
                        # Read json
                        data = json.loads(line.strip())
                        message = data.get("message", "")
                        notification_type = str(data.get("type", DEFAULT_TYPE)).lower()
                        title = data.get("title", DEFAULT_TITLE)

                        if message:
                            send_desktop_notification(message, notification_type, title)

                        else:
                            LOGGER.warning("Received notification with no message")

                    except json.JSONDecodeError:
                        LOGGER.warning(f"Received invalid JSON from pipe: {line.strip()}")

                    except Exception as e:
                        LOGGER.error(f"Error handling message from pipe: {e}")

        except FileNotFoundError:
            LOGGER.warning("Pipe lost or not found")

        except Exception as e:
            LOGGER.critical(f"Critical error with pipe operations: {e}")


if __name__ == "__main__":
    start_notifier_daemon()
