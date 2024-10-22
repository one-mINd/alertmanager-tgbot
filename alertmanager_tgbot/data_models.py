"""Module with pydantic validation models for FastAPI endpoints"""

from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel


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
