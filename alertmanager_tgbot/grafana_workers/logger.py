"""Logger configuration for module"""

import logging

grafana_workers_logger = logging.getLogger("grafana_workers")
grafana_workers_logger.propagate = False
