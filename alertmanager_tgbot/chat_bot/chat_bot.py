"""Users interaction module"""

from telethon.sync import TelegramClient, events

from .logger import chatbot_logger
from conf import ALERTMANAGER_ADDRESS
from cache import Cache
from chat_bot.parsers import parse_mute_command
from request_senders import send_post_request


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
            cache: Cache
        ) -> None:

        self.client = client
        self.cache = cache

        self.client.add_event_handler(
            self.ping,
            event=events.NewMessage(
                pattern='/ping'
            )
        )

        self.client.add_event_handler(
            self.silence,
            event=events.NewMessage(
                pattern='/silence'
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


    async def silence(self, event: events.NewMessage):
        """
        Handle create silence command
        """
        try:
            command = event.message.message
            chatbot_logger.info("Handle silence command - %s", command)

            mute = parse_mute_command(command)
            response = await send_post_request(
                url=ALERTMANAGER_ADDRESS+"api/v2/silences",
                message=mute.dict()
            )

            chatbot_logger.info("Silence created, response is - %s", response)

            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silence created with id {response['silenceID']}"
            )

        except Exception as err:
            chatbot_logger.error("Silence create failed with error: \n%s", err)
            await self.client.send_message(
                entity=event.message.chat_id,
                reply_to=event.message.id,
                message=f"Silence create failed with error:\n{err}"
            )
