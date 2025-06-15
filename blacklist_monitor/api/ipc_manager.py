# =============================================================================
# File: ipc_manager.py
# Author: deArrudal
# Description: Manages the creation of the IPC named pipe.
# Created: 2025-06-10
# License: GPL-3.0 License
# =============================================================================

import os
import stat
import logging

# Define the shared pipe path
NOTIFICATION_PIPE_DIR = "/run/blacklist_monitor"
NOTIFICATION_PIPE_PATH = os.path.join(NOTIFICATION_PIPE_DIR, "notifications.fifo")

LOGGER = logging.getLogger(__name__)


def setup_notification_pipe():
    try:
        # Create directory if needed
        if not os.path.exists(NOTIFICATION_PIPE_DIR):
            os.makedirs(NOTIFICATION_PIPE_DIR, mode=0o755, exist_ok=True)
            LOGGER.info(f"Created notification pipe directory: {NOTIFICATION_PIPE_DIR}")

        # Create pipe if needed
        if not os.path.exists(NOTIFICATION_PIPE_PATH):
            os.mkfifo(NOTIFICATION_PIPE_PATH, mode=0o666)
            LOGGER.info(f"Created notification pipe: {NOTIFICATION_PIPE_PATH}")

        else:
            # Verify existing path is a FIFO
            if not stat.S_ISFIFO(os.stat(NOTIFICATION_PIPE_PATH).st_mode):
                LOGGER.critical(f"Path '{NOTIFICATION_PIPE_PATH}' is not a FIFO")
                raise RuntimeError(f"Path '{NOTIFICATION_PIPE_PATH}' is not a FIFO")

    except Exception as e:
        LOGGER.critical(f"Fatal error setting up pipe at {NOTIFICATION_PIPE_PATH}: {e}")
        raise RuntimeError(
            f"Fatal error setting up pipe at {NOTIFICATION_PIPE_PATH}: {e}"
        )


if __name__ == "__main__":
    setup_notification_pipe()
