"""Project entrypoint"""

import conf
from api.api import get_server, set_bot
from tgbot import TGBot
from alertmanager_workers import AlertmanagerWorker
from project_logging import root_logger


async def run(bot):
    """Start alertmanager_tgbot"""
    await get_server(bot.get_event_loop()).serve()


if __name__ == "__main__":
    root_logger.info("Starting alertmanager-tgbot")

    alertmanager_worker = AlertmanagerWorker(
        alertmanager_address=conf.ALERTMANAGER_ADDRESS
    )

    bot = TGBot(
        api_id=conf.API_ID,
        api_hash=conf.API_HASH,
        phone_number=conf.PHONE_NUMBER,
        user_password=conf.USER_PASSWORD,
        client_name=conf.CLIENT_NAME,
        alertmanager_worker=alertmanager_worker
    )

    set_bot(bot)
    loop = bot.get_event_loop()

    alertmanager_worker.set_chanel_worker(bot)
    loop.create_task(alertmanager_worker.sync_alerts())

    loop.run_until_complete(run(bot))
