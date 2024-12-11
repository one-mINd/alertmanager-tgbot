"""Project entrypoint"""

from asyncio import new_event_loop, sleep
from conf import (
    conf,
    init_conf,
    ConfValidationError,
    ConfFileNotFound
)
from api.api import get_server, set_bot
from tgbot import TGBot
from alertmanager_workers import AlertmanagerWorker
from grafana_workers import GrafanaWorker
from project_logging import root_logger


async def run(loop):
    """Run"""
    root_logger.info("Starting alertmanager-tgbot")
    running = True
    while running:
        try:
            init_conf()

            grafna_worker = GrafanaWorker(
                grafana_url=conf.GRAFANA_ADDRESS,
                grafana_auth_token=conf.GRAFANA_AUTH_TOKEN
            )

            alertmanager_worker = AlertmanagerWorker(
                grafana_worker=grafna_worker,
                alertmanager_address=conf.ALERTMANAGER_ADDRESS,
                loop=loop
            )

            bot = TGBot(
                api_id=conf.API_ID,
                api_hash=conf.API_HASH,
                phone_number=conf.PHONE_NUMBER,
                user_password=conf.USER_PASSWORD,
                client_name=conf.CLIENT_NAME,
                alertmanager_worker=alertmanager_worker,
                grafana_worker=grafna_worker,
                loop=loop
            )

            set_bot(bot)
            alertmanager_worker.set_chanel_worker(bot)

            loop.create_task(alertmanager_worker.sync_alerts())
            loop.create_task(bot.start())
            await get_server(bot.get_event_loop()).serve()

        except(
            ConfValidationError,
            ConfFileNotFound
        )as err:
            root_logger.error(err)
            await sleep(5)
            continue

        except Exception as err:
            running = False
            raise err


if __name__ == "__main__":
    loop = new_event_loop()
    loop.run_until_complete(run(loop))
