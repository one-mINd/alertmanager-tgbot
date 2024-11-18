"""
Module with tools to format datamodels 
into pretty telegram messages and back
"""

from textwrap import dedent
import dateparser
from jinja2 import Template, StrictUndefined
from jinja2.filters import FILTERS
from jinja2.exceptions import UndefinedError

from data_models import BaseAlert
from conf import conf
from chanel_workers.logger import tgbot_logger


# Custom filters
def format_date(value, target_format='%b %d %Y %H:%M:%S'):
    """
    Format original iso format in alert to specific string
    args
        value: original not formated date
        target_format: format that value will converted
    """
    return dateparser.parse(value).strftime(target_format)


FILTERS["format_date"] = format_date


def format_alert(alert: BaseAlert) -> str:
    """
    Format data model alert into string
    args
        alert: original alert
    """
    try:
        template = Template(conf.ALERT_TEMPLATE, undefined=StrictUndefined)
        formated = template.render(**alert.dict())
        return formated

    except UndefinedError as err:
        tgbot_logger.exception(dedent("""\
            Tried rendering jinja2 template with alert, but failed
            Original alert is - %s
            Target template is - %s"""
            ),
            alert, conf.ALERT_TEMPLATE)
        raise AlertHasNotFieldsForTemplate(alert, conf.ALERT_TEMPLATE) from err


def format_alert_allow_undefined(alert: BaseAlert) -> str:
    """
    Format data model alert into string and ignore undefined variables
    args
        alert: original alert
    """
    template = Template(conf.ALERT_TEMPLATE)
    formated = template.render(**alert.dict())
    return formated


def format_resolve(alert: BaseAlert) -> str:
    """
    Format data model resolve into string
    args
        alert: original resolve alert
    """
    try:
        template = Template(conf.RESOLVE_TEMPLATE, undefined=StrictUndefined)
        formated = template.render(**alert.dict())
        return formated

    except UndefinedError as err:
        tgbot_logger.exception(dedent("""\
            Tried rendering jinja2 template with alert, but failed
            Original alert is - %s
            Target template is - %s"""
            ),
            alert, conf.RESOLVE_TEMPLATE)
        raise AlertHasNotFieldsForTemplate(alert, conf.RESOLVE_TEMPLATE) from err


def format_resolve_allow_undefined(alert: BaseAlert) -> str:
    """
    Format data model resolve into string and ignore undefined variables
    args
        alert: original resolve alert
    """
    template = Template(conf.RESOLVE_TEMPLATE)
    formated = template.render(**alert.dict())
    return formated


class AlertHasNotFieldsForTemplate(Exception):
    """
    Exception for cases when render with jinja failed
    because alert has not fields for specified template
    args:
        alert: original alert
        template: jinja2 template
    """
    def __init__(self, alert: BaseAlert, template: str):
        self.alert = alert
        self.template = template
        super().__init__(
            dedent(f"""Tried rendering jinja2 template with alert, but failed
                Original alert is - {alert}
                Target template is - {template}""")
        )
