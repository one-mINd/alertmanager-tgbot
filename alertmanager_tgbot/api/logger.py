"""Logger configuration for module"""

import logging

api_logger = logging.getLogger("api")
api_logger.propagate = False
