"""Users interaction module"""

from asyncio import sleep
from textwrap import dedent
from telethon.sync import TelegramClient, events

from .logger import chatbot_logger
from .acl import is_operation_permitted
from conf import CHATS_IDS
from cache import Cache
from chat_bot.parsers import parse_silence_command, parse_mute_command, get_help
from alertmanager_workers import AlertmanagerWorker, AlertHasntSilence


class ChatBot():
    """
    Base class for working with users
    args:
        client: Telegram client that will work with chats
        cache: Object of Cache class, where cache will stored
    """
    def __init__(
            self,
            client: TelegramClient,
            cache: Cache,
            alertmanager_worker: AlertmanagerWorker
        ) -> None:

        self.client = client
        self.cache = cache
        self.alertmanager_worker = alertmanager_worker
        self.forwards_stack = {}

        self.client.add_event_handler(
            self.ping,
            event=events.NewMessage(
                pattern='/ping'
            )
        )

        self.client.add_event_handler(
            self.help,
            event=events.NewMessage(
                pattern='/help'
            )
        )

        self.client.add_event_handler(
            self.silence,
            event=events.NewMessage(
                pattern='/silence'
            )
        )

        self.client.add_event_handler(
            self.mute,
            event=events.NewMessage(
                pattern='/mute'
            )
        )

        self.client.add_event_handler(
            self.unmute,
            event=events.NewMessage(
                pattern='/unmute'
            )
        )

        self.client.add_event_handler(
            self.forward,
            event=events.NewMessage(
                forwards=True
            )
        )


    async def ping(self, event: events.NewMessage):
        """
        Debug ping-pong handler
        """
        msg = event.message

        await self.client.send_message(
            entity=msg.chat_id,
            reply_to=msg.id,
            message="pong"
        )


    async def help(self, event: events.NewMessage):
        """
        Send help message
        """
        msg = event.message
        help_message = get_help()
        help_header = dedent("""
        All commands start with the **"/"** symbol. 
        Please note that some commands require forwarding alert messages from chats that the bot works with. 
        Attention, forwarding messages from chats that the bot does not work with or forwarding from the current chat here will not work!
        """)
        help_message = help_header + "\n\n" + help_message

        await self.client.send_message(
            entity=msg.chat_id,
            message=help_message
        )


    async def silence(self, event: events.NewMessage):
        """
        Handle create silence command
        """
        try:
            command = event.message.message
            sender = await event.get_sender()
            chatbot_logger.info(
                "Handle silence command from user %s command is - %s",
                sender.username, command
            )

            if not is_operation_permitted(sender.username, "mute"):
                raise PermissionDenied(sender.username)

            mute = parse_silence_command(command)
            silence_id = await self.alertmanager_worker.create_silence(mute)
            chatbot_logger.info("Silence created, response is - %s", silence_id)

            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silence created with id {silence_id}"
            )

        except Exception as err:
            chatbot_logger.error("Silence create failed with error: \n%s", err)
            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silence create failed with error:\n{err}"
            )


    async def mute(self, event: events.NewMessage):
        """
        Handle mute alerts command
        """
        try:
            await sleep(2)

            sender = await event.get_sender()
            command = event.message.message
            chatbot_logger.info(
                "Handle mute command from user %s command is - %s",
                sender.username, command
            )

            if not is_operation_permitted(sender.username, "mute"):
                raise PermissionDenied(sender.username)

            if not event.chat_id in self.forwards_stack \
                or len(self.forwards_stack[event.chat_id]) == 0:
                raise AlertsNotSpecified()

            silences_ids = []
            alerts = self.forwards_stack.pop(event.chat_id)
            for alert in alerts:
                if not alert.message.forward.chat_id in CHATS_IDS:
                    raise ForwardFromUnknownChat(alert.message.forward.chat_id)

                alert_cache_keys = self.cache.get_keys_by_entity_messageids(
                    entity=alert.message.forward.chat_id,
                    messsages_ids=[alert.message.forward.channel_post]
                )
                alert_cache_key = alert_cache_keys[0]
                alert = self.cache.get_cache_by_key(alert_cache_key)
                alert = alert.get('alert')
                mute = parse_mute_command(command, alert)
                mute.createdBy = sender.username
                silence_id = await self.alertmanager_worker.create_silence(mute)
                silences_ids.append(silence_id)

                chatbot_logger.info(
                    "Alert muted with silence id - %s",
                    silence_id
                )

            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silences created with ids - {silences_ids}"
            )

        except ForwardFromUnknownChat:
            chatbot_logger.error(
                "Chat unknown with id %s",
                alert.message.forward.chat_id
            )
            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=dedent("""
                    Forward from unknown chat
                    You should only send alerts from chats that the bot works with
                """)
            )

        except Exception as err:
            chatbot_logger.error("Silence create failed with error: \n%s", err)
            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silence create failed with error:\n{err}"
            )


    async def unmute(self, event: events.NewMessage):
        """
        Handle unmute alerts command
        """
        try:
            await sleep(2)

            sender = await event.get_sender()
            command = event.message.message
            chatbot_logger.info(
                "Handle mute command from user %s command is - %s",
                sender.username, command
            )

            if not is_operation_permitted(sender.username, "mute"):
                raise PermissionDenied(sender.username)

            if not event.chat_id in self.forwards_stack \
                or len(self.forwards_stack[event.chat_id]) == 0:
                raise AlertsNotSpecified()

            silences_ids = []
            alerts = self.forwards_stack.pop(event.chat_id)
            for alert_forward in alerts:
                alert_cache_keys = self.cache.get_keys_by_entity_messageids(
                    entity=alert_forward.message.forward.chat_id,
                    messsages_ids=[alert_forward.message.forward.channel_post]
                )
                alert_cache_key = alert_cache_keys[0]
                alert = self.cache.get_cache_by_key(alert_cache_key)
                alert = alert.get('alert')
                silences_id = await self.alertmanager_worker.unmute_alert(
                    alert
                )
                silences_ids.append(silences_id)

                chatbot_logger.info(
                    "Alert unmuted with silence id - %s",
                    silences_id
                )

            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silences deleted with ids - {silences_ids}"
            )

        except AlertHasntSilence:
            chatbot_logger.error("Alert not muted")
            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=alert_forward.message.id,
                message="The alert silence is not removed because the alert is not muted yet."
            )

        except Exception as err:
            chatbot_logger.error("Silence delete failed with error: \n%s", err)
            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silence delete failed with error:\n{err}"
            )


    async def forward(self, event: events.NewMessage):
        """
        Handle all forwards
        """
        try:
            if not event.chat_id in self.forwards_stack:
                self.forwards_stack[event.chat_id] = []
            self.forwards_stack[event.chat_id].append(event)

        except Exception as err:
            chatbot_logger.error("Silence create failed with error: \n%s", err)
            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silence create failed with error:\n{err}"
            )


# Module Exceptions


class PermissionDenied(Exception):
    """
    Exception for cases when a user attempts to perform a prohibited operation
    args:
        username: who get permission denied
    """
    def __init__(self, username: str):
        self.username = username
        super().__init__(
            dedent(f"""
                The user {self.username} is prohibited from performing the desired operation
            """)
        )


class AlertsNotSpecified(Exception):
    """
    Exception for cases when a user attempts to mute without alerts
    """
    def __init__(self):
        super().__init__(
            dedent("""
                You must forward alerts to this chat to use /mute command
            """)
        )


class ForwardFromUnknownChat(Exception):
    """
    Exception for cases when a user attempts to work with messages from unknown chat
    """
    def __init__(self, chat_id):
        self.chat_id = chat_id
        super().__init__(
            dedent(f"""
                Chat unknown with id {self.chat_id}
            """)
        )
