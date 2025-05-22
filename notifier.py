import json
import subprocess
import logging

# Paths
LOG_PATH = "/var/kfm/log/blacklist/notifier.log"

# Constants
DEFAULT_TITLE = "KFishmonger"
DEFAULT_TYPE = "information"
URGENCY_MAP = {
    "information": "normal",
    "warning": "normal",
    "error": "critical",
}

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Display a desktop notification using `notify-send` based on a JSON string
def show_notification(json_notification):
    try:
        # JSON keys: 'message', 'type' (information/warning/error), 'title'
        data = json.loads(json_notification)

        message = data.get("message", "")
        if not message:
            logging.warning("Notification message is empty.")
            return

        notification_type = str(data.get("type", DEFAULT_TYPE)).lower()
        title = data.get("title", DEFAULT_TITLE)

        urgency = URGENCY_MAP.get(notification_type, "normal")

        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, message], check=True
        )

        logging.info(f"Notification sent: {title} - {message}")

    except (json.JSONDecodeError, KeyError) as e:
        logging.warning(f"Invalid notification format: {e}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Call process failed: {e}")
