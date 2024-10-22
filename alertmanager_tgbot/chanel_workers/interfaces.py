"""Telegram client-bot interface with minimal functionality"""

from abc import abstractmethod

from data_models import BaseAlert, BaseAlerts, ActiveAlerts


class ChanelWorkerInterface():
    """Base interface for telegram bots"""
    @abstractmethod
    def get_client(self):
        """Get telegram client object"""


    def get_event_loop(self):
        """Get telegram client event loop"""


    @abstractmethod
    async def send_alert_to_chat(self, entity: int, alert: BaseAlert) -> None:
        """
        Send single alert to specific telegram chat
        args:
            entity: ID of target chat or group
            alert: Alert that will be sent to the entity
        """


    @abstractmethod
    async def send_alert_to_default_chats(self, alert: BaseAlert) -> None:
        """
        Send single alert to default telegram chats
        args:
            alert: Alert that will be sent to the entity
        """


    @abstractmethod
    async def send_alerts_to_chats(self, alerts: BaseAlerts) -> None:
        """
        Send alerts to telegram chats
        args:
            alerts: Alerts that will be sent to the relevant entity 
        """


    @abstractmethod
    async def delete_alerts_by_message_ids(self, entity: int, message_ids: list) -> None:
        """
        delete alerts by message ids
        args:
            entity: ID of target chat or group
            message_ids: list of message ids to delete
        """


    @abstractmethod
    async def delete_alerts_by_cache_keys(self, alerts_cache_keys: list) -> None:
        """
        delete alerts by cache keys
        args:
            alerts_cache_keys: List with cache keys
        """


    @abstractmethod
    async def update_alert(self, entity: int, alert: BaseAlerts) -> None:
        """
        Update text message for alert in chat
        args:
            entity: ID of target chat or group
            alerts: alert that will updated in entity
        """


    @abstractmethod
    async def update_alerts(self, alerts: BaseAlerts) -> None:
        """
        Update text message for alerts
        args:
            alerts: alerts that will updated in chats
        """


    @abstractmethod
    async def get_messages_ids_in_channel(self, entity: int) -> list:
        """
        Get all ids of messages in specified channel
        args:
            entity: ID of target chat or group
        """


    @abstractmethod
    async def sync_cache_with_chanel(self) -> None:
        """
        Sync cache with real messages in chanel
        """


    @abstractmethod
    async def sync_alerts(self, active_alerts: ActiveAlerts) -> None:
        """
        Sync alerts in group with realy active alerts in alertmanager
        args:
            active_alerts: curently active alerts from alertmanager
        """
