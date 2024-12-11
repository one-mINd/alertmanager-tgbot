"""Main telegram bot base"""

from asyncio import new_event_loop
from telethon.sync import TelegramClient

from alertmanager_workers import AlertmanagerWorker
from grafana_workers import GrafanaWorker
from chanel_workers import ChanelWorker
from chat_bot import ChatBot
from cache import Cache


class TGBot(ChanelWorker, ChatBot):
    """
    Base class for working with telegram
    args:
        api_id: api id for telegram session
        api_hash: api hash for telegram session
        phone_number: phone number of telegram user account
        user_password: password of telegram user account
        client_name: name of telegram session
    """
    def __init__(
            self,
            api_id: int,
            api_hash: str,
            phone_number: str,
            user_password: str,
            alertmanager_worker: AlertmanagerWorker,
            grafana_worker: GrafanaWorker,
            client_name="tgbot",
            loop=new_event_loop()
        ) -> None:

        self.loop = loop
        self.cache = Cache()
        self.phone_number = phone_number
        self.user_password = user_password
        self.client = TelegramClient(
            "conf/"+client_name, 
            api_id=api_id,
            api_hash=api_hash,
            system_version="4.16.30-vxCUSTOM",
            loop=self.loop
        )

        ChanelWorker.__init__(
            self,
            client=self.client,
            cache=self.cache
        )

        ChatBot.__init__(
            self,
            client=self.client,
            cache=self.cache,
            grafana_worker=grafana_worker,
            alertmanager_worker=alertmanager_worker
        )


    def get_client(self) -> TelegramClient:
        """Get telegram client object"""
        return self.client


    def get_event_loop(self):
        """Get telegram client event loop"""
        return self.client.loop


    async def start(self):
        """Start telegram bot session"""
        await self.client.start(
            phone=self.phone_number,
            password=self.user_password
        )
