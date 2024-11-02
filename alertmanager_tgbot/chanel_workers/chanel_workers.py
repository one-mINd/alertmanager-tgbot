"""Telegram bot for working with alert chats"""

from textwrap import dedent
from telethon.sync import TelegramClient

from conf import CHATS, DEFAULT_CHATS
from data_models import BaseAlert, BaseAlerts, ActiveAlerts, EnrichedActiveAlerts
from chanel_workers.logger import tgbot_logger
from chanel_workers.interfaces import ChanelWorkerInterface
from cache import Cache
from chanel_workers.formatters import format_alert_allow_undefined


class ChanelWorker(ChanelWorkerInterface):
    """
    Base class for working with alerts chats
    args:
        client: Telegram client that will work with chats
        cache: Object of Cache class, where cache will stored
    """
    def __init__(
            self,
            client: TelegramClient,
            cache: Cache
        ) -> None:

        self.client = client
        self.cache = cache


    def _split_alerts_by_chats(self, alerts: BaseAlerts) -> dict:
        """
        Determine which chats alerts will be sent to
        By match alert labels with specified in confs chat labels
        If alert has none related chats it will be sent to all default chats
        Result is dict with following structure:
        {
            chat_id: [
                BaseAlert,
                ...
            ]
            ...
        }
        args:
            alerts: alerts that will be assigned to the corresponding chats 
        """
        try:
            result = {}
            for chat in CHATS:
                chat_id = chat["id"]
                result[chat_id] = []

                # Skip alerts without labels
                if "labels" not in chat:
                    continue

                for alert in alerts.alerts:
                    # Alerts will send if its labels is subset of chats labels
                    if chat.get("labels").items() <= alert.labels.items():
                        result[chat_id].append(alert)

            # Get all alerts with defined chats
            alerts_with_chats = [
                alert
                for alerts in result.values()
                    for alert in alerts
            ]

            # Get alerts that don't have a corresponding chat
            alerts_without_chats = [
                alert
                for alert in alerts.alerts
                    if alert not in alerts_with_chats
            ]

            # If the alert was not defined for a chat, it will be sent to all default chats
            alerts_without_chats = {
                chat_id: alerts_without_chats
                for chat_id in DEFAULT_CHATS
            }

            for chat in alerts_without_chats:
                if not chat in result:
                    result[chat] = []
                result[chat] += alerts_without_chats[chat]

            result = {int(key): value for key, value in result.items()}

            return result

        except KeyError as err:
            tgbot_logger.error(dedent("""\
                failed sending alerts messages to provided chat%s"""),
                chat)
            raise ChatHasNotID(chat) from err

        except ValueError as err:
            tgbot_logger.error(dedent("""\
                Wrong type of chat id. It must be int or one of predefined string."""))
            raise WrongChatID() from err


    async def send_alert_to_chat(self, entity: str, alert: BaseAlert) -> None:
        """
        Send single alert to specific telegram chat
        args:
            entity: ID of target chat or group
            alert: Alert that will be sent to the entity
        """
        try:
            message = await self.client.send_message(
                entity=entity,
                message=format_alert_allow_undefined(alert)
            )
            self.cache.cache_alert(alert=alert, entity=entity, message_id=message.id)

            tgbot_logger.debug(dedent("""\
                Alert was sent to chat 
                Alert labels is - %s
                chat id is - %s
                """),
                alert.labels, entity)

        except Exception as err:
            tgbot_logger.exception(dedent("""\
                failed sending alerts message to %s
                Original message- %s"""
                ),
                entity, alert)
            raise SendAlertFailed(entity, alert) from err


    async def send_alert_to_default_chats(self, alert: BaseAlert) -> None:
        """
        Send single alert to default telegram chats
        args:
            alert: Alert that will be sent to the entity
        """
        if len(DEFAULT_CHATS) > 0:
            for chat_id in DEFAULT_CHATS:
                try:
                    await self.send_alert_to_chat(entity=chat_id, alert=alert)
                except SendAlertFailed:
                    continue

        else:
            tgbot_logger.warning(dedent("""\
                failed sending alerts message to default chats
                Original message- %s"""),
                alert)
            raise NoDefaultChats(DEFAULT_CHATS)


    async def send_alerts_to_chats(self, income_alerts: BaseAlerts) -> None:
        """
        Send alerts to telegram chats
        args:
            alerts: Alerts that will be sent to the relevant entity 
        """
        chat_id_alerts = self._split_alerts_by_chats(income_alerts)
        for chat_id, alerts in chat_id_alerts.items():
            for alert in alerts:
                try:
                    await self.send_alert_to_chat(chat_id, alert)
                except SendAlertFailed:
                    continue


    async def delete_alerts_by_message_ids(self, entity: int, message_ids: list) -> None:
        """
        delete alerts by message ids
        args:
            entity: ID of target chat or group
            message_ids: list of message ids to delete
        """
        try:
            await self.client.delete_messages(
                entity=entity,
                message_ids=message_ids
            )

        except Exception:
            tgbot_logger.error(dedent("""\
                failed to delete alerts messages by message ids %s
                Entity is - %s
                Message IDs is - %s
                """
                ),
                entity, message_ids)


    async def delete_alerts_by_cache_keys(self, alerts_cache_keys: list) -> None:
        """
        delete alerts by cache keys
        args:
            alerts_cache_keys: List with cache keys
        """
        for key in alerts_cache_keys:
            try:
                cache = self.cache.get_cache_by_key(key)
                await self.client.delete_messages(
                    entity=cache.get("entity"),
                    message_ids=[cache.get("message_id")]
                )
                self.cache.delete_alert_by_key(key)

            except Exception:
                tgbot_logger.error(dedent("""\
                    failed to delete alerts message by its cache key %s
                    Original key is - %s"""
                    ),
                    key)
                continue


    async def update_alert(self, entity: str, alert: BaseAlert) -> None:
        """
        Update text message for alert in chat
        args:
            entity: ID of target chat or group
            alerts: alert that will updated in entity
        """
        try:
            alert_cache_key = self.cache.generate_key(alert, entity)
            alert_cache = self.cache.get_cache_by_key(alert_cache_key)
            message_id = alert_cache.get("message_id")

            original_message = await self.client.get_messages(
                entity=entity,
                ids=message_id
            )
            updated_message = format_alert_allow_undefined(alert)

            if original_message.text != updated_message:
                message = await self.client.edit_message(
                    entity=entity,
                    message=message_id,
                    text=updated_message
                )
                self.cache.delete_alert(alert, entity)
                self.cache.cache_alert(alert, entity, message.id)

                tgbot_logger.debug(dedent("""\
                    Alert was updated in chat 
                    Alert labels is - %s
                    chat id is - %s
                    """),
                    alert.labels, entity)
            else:
                tgbot_logger.debug(dedent("""\
                    Trying to update alert, but nothing to update
                    """
                    )
                )

        except Exception as err:
            tgbot_logger.exception(dedent("""\
                failed to update alerts message in %s
                Original message- %s"""
                ),
                entity, alert)
            raise UpdateAlertFailed(entity, alert) from err


    async def update_alerts(self, income_alerts: BaseAlerts) -> None:
        """
        Update text message for alerts
        args:
            alerts: alerts that will updated in chats
        """
        chat_id_alerts = self._split_alerts_by_chats(income_alerts)
        for chat_id, alerts in chat_id_alerts.items():
            for alert in alerts:
                await self.update_alert(chat_id, alert)


    async def get_messages_ids_in_channel(self, entity: int) -> list:
        """
        Get all ids of messages in specified channel
        args:
            entity: ID of target chat or group
        """
        ids = []
        async for message in self.client.iter_messages(entity):
            if message.id != 1:
                ids.append(message.id)
        return ids


    async def sync_cache_with_chanel(self) -> None:
        """
        Sync cache with real messages in chanel
        """
        tgbot_logger.info("Start to sync cache with chanels")
        cached_ids = [cache.get("message_id") for cache in self.cache.get_alerts().values()]
        cached_ids = set(cached_ids)
        for chat in CHATS:
            chat_id = chat["id"]
            if chat_id == "blackhole":
                continue
            chat_id = int(chat_id)

            messages_ids = await self.get_messages_ids_in_channel(chat_id)
            messages_ids = set(messages_ids)

            # Defining messages in chanel, but not in cache
            alerts_to_delete = messages_ids - cached_ids
            await self.delete_alerts_by_message_ids(chat_id, alerts_to_delete)
            tgbot_logger.info(dedent(f"""\
                            Alerts not in cache - {len(alerts_to_delete)}
                            """))

            # Defining messages in cache, but not in chanel
            cache_to_delete = cached_ids - messages_ids
            cache_to_delete = self.cache.get_keys_by_entity_messageids(chat_id, cache_to_delete)
            self.cache.delete_alerts_by_key(cache_to_delete)
            tgbot_logger.info(dedent(f"""\
                            Cache without messages in chanel - {len(cache_to_delete)}
                            """))


    async def sync_alerts(self, active_alerts: EnrichedActiveAlerts) -> None:
        """
        Sync alerts in chat with realy active alerts in alertmanager
        args:
            active_alerts: curently active alerts from alertmanager
        """
        tgbot_logger.info("Start to sync alerts")
        # Generate cache keys in one list for all income active alerts
        chat_id_alerts = self._split_alerts_by_chats(active_alerts)
        cache_keys_active_alerts = {}
        for chat_id, alerts in chat_id_alerts.items():
            for alert in alerts:
                cache_key = self.cache.generate_key(alert, chat_id)
                cache_keys_active_alerts[cache_key] = alert

        # Generate set of cache keys for income active alerts
        cache_keys = cache_keys_active_alerts.keys()
        cache_keys = set(cache_keys)

        # Get set of cache keys for alerts in cache
        cached_keys = self.cache.get_alerts()
        cached_keys = cached_keys.keys()
        cached_keys = set(cached_keys)

        # Defining alerts to delete
        alerts_to_delete = cached_keys - cache_keys
        await self.delete_alerts_by_cache_keys(alerts_to_delete)
        tgbot_logger.info(dedent(f"""\
                            Alerts to delete - {len(alerts_to_delete)}
                            """))

        # Defining alerts to send
        alerts_to_create = cache_keys - cached_keys
        alerts_to_create = [cache_keys_active_alerts[al] for al in alerts_to_create]
        await self.send_alerts_to_chats(ActiveAlerts(alerts=alerts_to_create))
        tgbot_logger.info(dedent(f"""\
                            Alerts to create - {len(alerts_to_create)}
                            """))

        # Defining alerts to update
        alerts_to_update = cache_keys & cached_keys
        alerts_to_update = [cache_keys_active_alerts[al] for al in alerts_to_update]
        await self.update_alerts(ActiveAlerts(alerts=alerts_to_update))
        tgbot_logger.info(dedent(f"""\
                            Existing alerts - {len(alerts_to_update)}
                            """))

        await self.sync_cache_with_chanel()


# Module Exceptions


class SendAlertFailed(Exception):
    """
    Exception for cases when sending alerts suddenly fails
    args:
        entity: ID of target chat or group
        message: The string that will be sent to the entity
    """
    def __init__(self, entity: str, message: str):
        self.entity = entity
        self.message = message
        super().__init__(
            dedent(f"""failed sending alerts message to {self.entity}
            Original message- {self.message}""")
        )


class DeleteAlertFailed(Exception):
    """
    Exception for cases when deleting alerts suddenly fails
    args:
        entity: ID of target chat or group
        message: The string that will be sent to the entity
    """
    def __init__(self, entity: str, message: str):
        self.entity = entity
        self.message = message
        super().__init__(
            dedent(f"""failed sending alerts message to {self.entity}
            Original message- {self.message}""")
        )


class UpdateAlertFailed(Exception):
    """
    Exception for cases when updating alerts suddenly fails
    args:
        entity: ID of target chat or group
        message: The string that will be sent to the entity
    """
    def __init__(self, entity: str, message: str):
        self.entity = entity
        self.message = message
        super().__init__(
            dedent(f"""failed sending alerts message to {self.entity}
            Original message- {self.message}""")
        )


class NoDefaultChats(Exception):
    """
    Exception for cases when no default chats is provided
    args:
        chats: list of all possible chats
    """
    def __init__(self, chats: list):
        self.chats = chats
        super().__init__(
            dedent(f"""Tried sending a message to default chats but none provided.
                Original chats list - {chats}""")
        )


class ChatHasNotID(Exception):
    """
    Exception for cases when chat has not chat id
    args:
        chat: chat without specified id
    """
    def __init__(self, chat: dict):
        self.chat = chat
        super().__init__(
            dedent(f"""Tried sending a message to chat but its id is not provided.
                Original chat is - {chat}""")
        )


class WrongChatID(Exception):
    """
    Exception for cases when chat has wrong type
    """
    def __init__(self):
        super().__init__(
            dedent("""Wrong type of chat id. It must be int or one of predefined string.""")
        )
