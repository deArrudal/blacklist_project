# =============================================================================
# File: blacklists_fetcher.py
# Author: deArrudal
# Description: Downloads and normalizes IP blacklist from configured URLs.
# Created: 2025-05-20
# License: GPL-3.0 License
# =============================================================================

import os
import logging
import subprocess
import re

# Paths
SOURCE_FILE = "/opt/blacklist_monitor/resources/blacklist_sources.txt"
TARGET_DIR = "/opt/blacklist_monitor/resources/blacklists"

# Constants
IPV4_PATTERN = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}")
DEFAULT_NOTIFICATION_TYPE = "information"
LOGGER = logging.getLogger(__name__)

# Ensure the blacklist directory exists
os.makedirs(TARGET_DIR, exist_ok=True)


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
def download_file(url, filepath):
    try:
        subprocess.run(["wget", "-q", "-O", filepath, url], check=True)

        if not is_valid_download(filepath):
            os.remove(filepath)

            LOGGER.error(f"Invalid content in downloaded file: {filepath}")
            return False

        LOGGER.info(f"Downloaded file from {url} to {filepath}")
        return True

    except subprocess.CalledProcessError:
        LOGGER.error(f"Download failed for {url}", exc_info=True)
        return False


# Convert downloaded file to .txt and filtering lines that start with a digit
def convert_to_txt(name, filepath):
    temp = os.path.join(TARGET_DIR, f"{name}.tmp")
    output = os.path.join(TARGET_DIR, f"{name}.txt")

    try:
        with (
            open(filepath, "r", encoding="utf-8") as infile,
            open(temp, "w", encoding="utf-8") as outfile,
        ):
            for line in infile:
                line = line.strip()

                match = IPV4_PATTERN.match(line)
                if match:
                    ip_address = match.group(0)
                    outfile.write(f"{ip_address}\n")

        os.remove(filepath)
        os.rename(temp, output)

        LOGGER.info(f"Converted {filepath} to {output}")

    except Exception:
        LOGGER.error(f"Conversion failed for {filepath}", exc_info=True)


# Process each source (download and convert it)
def process_source(name, url, file_type):
    filename = f"{name}.{file_type}"
    filepath = os.path.join(TARGET_DIR, filename)

    try:
        if download_file(url, filepath):
            convert_to_txt(name, filepath)

    except Exception:
        LOGGER.error(f"Error processing {name}", exc_info=True)


def fetch_blacklists():
    # Validate if blacklist_sources exists
    if not os.path.exists(SOURCE_FILE):
        # Fallback: An backup blacklist_ips.txt is set during installation
        LOGGER.error("blacklist_sources.txt file not found", exc_info=True)
        return

    with open(SOURCE_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            # Skip comment and blank lines in blacklist_sources.txt
            if not line or line.startswith("#"):
                continue

            # Separate line in NAME <URL> <TYPE>
            parts = line.split()

            # Verify if entry follows the expected format
            if len(parts) != 3:
                LOGGER.warning(f"Invalid reference format: {line}")
                continue

            # Source
            name, url, file_type = parts
            process_source(name, url, file_type.lower())


if __name__ == "__main__":
    fetch_blacklists()
