# =============================================================================
# File: blacklists_fetcher.py
# Author: deArrudal
# Description: Downloads and normalizes IP blacklist from configured URLs.
# Created: 2025-05-20
# License: GPL-3.0 License
# =============================================================================

import os
import json
import logging
import subprocess
import re

from notifier import show_notification

# Paths
REFERENCE_PATH = "/opt/blacklist_monitor/resources/blacklist_sources.txt"
BLACKLIST_PATH = "/opt/blacklist_monitor/resources/blacklists"

# Constants
IPV4_PATTERN = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}")
DEFAULT_NOTIFICATION_TYPE = "information"
LOGGER = logging.getLogger(__name__)

# Ensure the blacklist directory exists
os.makedirs(BLACKLIST_PATH, exist_ok=True)


# Show notification on user's screen
def notify(message, notification_type=DEFAULT_NOTIFICATION_TYPE):
    data = json.dumps({"message": message, "type": notification_type})
    show_notification(data)


# Check if downloaded file is valid (not an HTML error page)
def is_valid_download(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            first_line = file.readline()
            if "<html" in first_line.lower():
                return False

        return True

    except Exception:
        LOGGER.error(f"Error validating download file: {filepath}", exc_info=True)
        return False


# Use wget to download file from URL to the destination
def download_file(url, destination):
    try:
        subprocess.run(["wget", "-q", "-O", destination, url], check=True)

        if not is_valid_download(destination):
            LOGGER.error(f"Invalid content in downloaded file: {destination}")
            os.remove(destination)
            return False

        LOGGER.info(f"Downloaded file from {url} to {destination}")
        return True

    except subprocess.CalledProcessError:
        LOGGER.error(f"Download failed for {url}", exc_info=True)
        return False


# Convert downloaded file to .txt and filtering lines that start with a digit
def convert_to_txt(name, filepath):
    temp_path = os.path.join(BLACKLIST_PATH, f"{name}.tmp")
    output_path = os.path.join(BLACKLIST_PATH, f"{name}.txt")

    try:
        with (
            open(filepath, "r", encoding="utf-8") as infile,
            open(temp_path, "w", encoding="utf-8") as outfile,
        ):
            for line in infile:
                line = line.strip()

                match = IPV4_PATTERN.match(line)
                if match:
                    ip_address = match.group(0)
                    outfile.write(f"{ip_address}\n")

        os.remove(filepath)
        os.rename(temp_path, output_path)

        LOGGER.info(f"Converted {filepath} to {output_path}")

    except Exception:
        LOGGER.error(f"Conversion failed for {filepath}", exc_info=True)


# Process each source (download and convert it)
def process_source(name, url, filetype):
    filename = f"{name}.{filetype}"
    source_path = os.path.join(BLACKLIST_PATH, filename)

    try:
        if download_file(url, source_path):
            convert_to_txt(name, source_path)

    except Exception:
        LOGGER.error(f"Error processing {name}", exc_info=True)


def fetch_blacklists():
    if not os.path.exists(REFERENCE_PATH):
        notify("blacklist_sources.txt file not found", "error")
        LOGGER.error("blacklist_sources.txt file not found")
        # Fallback: an initial blacklist_ips.txt is set during installation
        return

    with open(REFERENCE_PATH, "r", encoding="utf-8") as reference_file:
        for line in reference_file:
            line = line.strip()

            # Skip comment and blank lines in blacklist_sources.txt
            if not line or line.startswith("#"):
                continue

            parts = line.split()

            # Verify if entry follows the expected format NAME <URL> <TYPE>
            if len(parts) != 3:
                LOGGER.warning(f"Invalid reference format: {line}")
                continue

            name, url, ftype = parts
            process_source(name, url, ftype.lower())


if __name__ == "__main__":
    fetch_blacklists()
