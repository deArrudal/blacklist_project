import os
import json
import logging

from notifier import show_notification

# Paths
BLACKLIST_DIR = "/var/kfm/blacklist/resources/blacklists"
OUTPUT_PATH = "/var/kfm/blacklist/resources/blacklists/blacklist_ips.txt"
TEMP_PATH = "/var/kfm/blacklist/resources/blacklists/blacklist_ips.old"
LOG_PATH = "/var/kfm/log/blacklist/ip_aggregator.log"

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


# Backup blacklist_ips.txt file if it exists
def backup_existing_output():
    if os.path.exists(OUTPUT_PATH):
        os.rename(OUTPUT_PATH, TEMP_PATH)


# Restore blacklist_ips.txt file from backup if it exists
def restore_backup():
    if os.path.exists(TEMP_PATH):
        os.rename(TEMP_PATH, OUTPUT_PATH)
        logging.info("Restored previous blacklist from backup.")

    else:
        raise FileNotFoundError("Backup file not found during restore.")


# Aggregate all IPs from .txt blacklist files into blacklist_ips.txt
def aggregate_ips():
    ip_set = set()

    try:
        if not os.path.exists(BLACKLIST_DIR):
            notify(f"Blacklist directory not found: {BLACKLIST_DIR}", "error")
            logging.critical(f"Blacklist directory not found: {BLACKLIST_DIR}")
            raise FileNotFoundError(f"Blacklist directory not found: {BLACKLIST_DIR}")

        backup_existing_output()

        for filename in os.listdir(BLACKLIST_DIR):
            if not filename.endswith(".txt"):
                continue

            filepath = os.path.join(BLACKLIST_DIR, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    ip_set.update(ip.strip() for ip in file if ip.strip())

                logging.info(f"Processed file: {filename}")

            except OSError as read_error:
                logging.warning(f"Error reading file {filename}: {read_error}")

        # Check if set is empty
        if not ip_set:
            logging.error("No IPs found in blacklist files")
            raise ValueError("No IPs found in blacklist files")

        with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
            output_file.writelines(f"{ip}\n" for ip in sorted(ip_set))

        logging.info(f"Aggregated {len(ip_set)} unique IPs into {OUTPUT_PATH}")

    except Exception as e:
        notify(f"Failed during Ip aggregation: {e}", "error")
        logging.error(f"Failed during Ip aggregation: {e}")

        # Fallback: revert blacklist_ips.old and use as set
        try:
            restore_backup()

        except Exception as fallback_error:
            logging.critical(f"Failed to restore backup: {fallback_error}")
            raise


if __name__ == "__main__":
    aggregate_ips()
