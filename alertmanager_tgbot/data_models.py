"""Module with pydantic validation models for FastAPI endpoints"""

from datetime import datetime, timedelta
from typing import Literal, List, Optional, Dict, Any, Callable
from textwrap import dedent
from pydantic_core import PydanticCustomError
from pydantic import (
    BaseModel,
    ValidationInfo,
    field_validator,
    AnyUrl
)


class ConfFileChat(BaseModel):
    """Base model for project configuration in configuration file"""
    id: int
    default: bool = None
    labels: Dict[str, str] = {}


class ConfFile(BaseModel):
    """Base model for project configuration in configuration file"""
    CHATS: List[ConfFileChat] = None
    ACL: Dict[str, List[str]] = None

    ALERT_TEMPLATE: Optional[str] = dedent(
        """
        {%- if silences|length > 0 -%}
        [**MUTED** until {{ silences[0].endsAt | format_date('%b %d %Y %H:%M:%S') }}] 
        {% endif -%}
        **Alert Created** 😱
        **Host**: {{ labels.dns_hostname }}
        **Alert Name**: {{ labels.alertname }}
        **Status**: {{ labels.severity }} ❗️
        **Summary**: {{ annotations.summary }}
        **Started**: {{ startsAt | format_date('%b %d %Y %H:%M:%S') }}
        """
    )

    RESOLVE_TEMPLATE: Optional[str] = dedent(
        """
        **Alert Resolved** 😍
        **Environment**: {{ labels.env }}
        **Host**: {{ labels.dns_hostname }}
        **Alert Name**: {{ labels.alertname }}
        **Status**: OK 👍
        **Summary**: {{ annotations.summary }}
        **Ended**: {{ startsAt | format_date('%b %d %Y %H:%M:%S') }}
        """
    )

    class Config:
        """Model configuration"""
        validate_assignment = True

    @field_validator('ALERT_TEMPLATE', 'RESOLVE_TEMPLATE')
    def defaults(cls, v: str, info: ValidationInfo) -> str:
        """Set defaults values"""
        if v is None or v == '':
            return cls.model_fields[info.field_name].default
        return v

    @field_validator("ACL")
    def validate_acl(cls, v: dict) -> str:
        """Allow only specific values for ACL"""
        allowed_perms = {"mute", "info"}
        for key in v:
            unknown_perms = set(v[key]) - allowed_perms
            if unknown_perms:
                raise PydanticCustomError(
                    'unknown_perms',
                    'ACL has unknown permissions {unknown_perms}',
                    {'unknown_perms': '/'.join(unknown_perms)}
                )
        return v


class Conf(ConfFile):
    """Base model for project configuration"""
    API_ID: int = None
    API_HASH: str = None
    PHONE_NUMBER: str = None
    USER_PASSWORD: str = None
    CLIENT_NAME: str = 'telegram_bot'
    CONFS: ConfFile = None
    DEFAULT_CHATS: List[int] = []
    CHATS_IDS: List[int] = []
    ALERTMANAGER_ADDRESS: AnyUrl = None

    class Config:
        """Model configuration"""
        validate_assignment = True

    @field_validator("*", mode="wrap")
    @classmethod
    def allow_none(cls, value, next_: Callable[..., Any], info: ValidationInfo):
        """Validate None values"""
        required_vars = [
            'API_ID',
            'API_HASH',
            'PHONE_NUMBER',
            'CONFS',
            'ALERTMANAGER_ADDRESS',
            'CHATS',
            'ACL'
        ]

        # when updating, input values can be null, to reset optional fields in the database
        # except when it's the id, because that is mandatory
        if value is None:
            if info.field_name in required_vars:
                raise PydanticCustomError(
                    'missing',
                    'Variable {name} required',
                    {'name': info.field_name}
                )

            else:
                return cls.model_fields[info.field_name].default

        else:
            # in this case the normal validation should run
            return next_(value)

    @field_validator('ALERT_TEMPLATE', 'RESOLVE_TEMPLATE', 'CLIENT_NAME', 'CHATS_IDS')
    def defaults(cls, v: str, info: ValidationInfo) -> str:
        """Set defaults values, when None, empty string or list set"""
        if v is None or v == '' or v == []:
            return cls.model_fields[info.field_name].default
        return v

    @field_validator('ALERTMANAGER_ADDRESS')
    def tostr(cls, v: str) -> str:
        """Convert pydantic url type to str"""
        return str(v)


class BaseAlert(BaseModel):
    """Base model for alerts"""
    annotations: Dict[str, str]
    labels: Dict[str, str] = {}
    endsAt: str
    startsAt: str
    fingerprint: str
    generatorURL: str


class BaseAlerts(BaseModel):
    """List of base alerts"""
    alerts: List[BaseAlert]


class Alert(BaseAlert):
    """Single alert model"""
    status: Literal["resolved", "firing"]


class Alerts(BaseModel):
    """List of alerts model"""
    version: Optional[str]
    externalURL: Optional[str]
    receiver: Optional[str]
    groupKey: Optional[str]
    truncatedAlerts: Optional[int]
    status: Optional[Literal["resolved", "firing"]]
    commonAnnotations: Optional[Dict[str, str]]
    commonLabels: Optional[Dict[str, str]]
    groupLabels: Optional[Dict[str, str]]
    alerts: List[Alert]


class ActiveAlertStatus(BaseModel):
    """Active alert status"""
    inhibitedBy: List[Any]
    silencedBy: List[Any]
    state: str


class ActiveAlert(BaseAlert):
    """Active alert"""
    updatedAt: str
    receivers: List[Dict[str, str]]
    status: ActiveAlertStatus


class ActiveAlerts(BaseModel):
    """List of active alerts received from alertmanager api"""
    alerts: List[ActiveAlert]


class MuteMatcher(BaseModel):
    """Model for matchers in requests body for creating silences in alertmanager"""
    name: str
    value: str
    isRegex: Optional[bool] = True
    isEqual: Optional[bool] = True


class Mute(BaseModel):
    """Model for requests body for creating silences in alertmanager"""
    matchers: Optional[List[MuteMatcher]]
    createdBy: Optional[str] = ''
    comment: Optional[str] = ''

    # Today date by default
    startsAt: Optional[str] = datetime.now().isoformat(timespec="seconds")

    # Next day date by default
    endsAt: Optional[str] = (
        datetime.now() + timedelta(days=1)
    ).isoformat(timespec="seconds")


class Silence(BaseModel):
    """Model for alertmanager silences"""
    id: str
    status: Dict[str, str]
    updatedAt: str
    startsAt: str
    endsAt: str
    comment: str
    createdBy: str
    matchers: List[MuteMatcher]


class EnrichedActiveAlert(ActiveAlert):
    """Active alert enriched with information by alertmanager workers"""
    silences: Optional[List[Silence]] = []


class EnrichedActiveAlerts(BaseModel):
    """List of active alerts enriched with information by alertmanager workers"""
    alerts: List[EnrichedActiveAlert]
