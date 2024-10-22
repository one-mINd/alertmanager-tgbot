"""Module with service metrics in openmetrics format"""

import pathlib
from uptime import uptime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from api.logger import api_logger

current_directory = str(pathlib.Path(__file__).parent.resolve())
env = Environment(
    loader=FileSystemLoader(current_directory + '/metrics_templates'),
    autoescape=select_autoescape(['j2'])
)

template = env.get_template('metrics.j2')

async def metrics():
    """Return rendered metrics"""
    api_logger.debug("Render metrics")
    return template.render(
        service_uptime=uptime()
    )
