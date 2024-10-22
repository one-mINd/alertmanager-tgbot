"""Logger configuration for module"""

import logging

alertmanager_workers_logger = logging.getLogger("alertmanager_workers")
alertmanager_workers_logger.propagate = False
