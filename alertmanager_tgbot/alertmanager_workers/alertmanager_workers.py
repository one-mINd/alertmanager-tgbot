"""Alertmanager Worker main class"""

import asyncio
from textwrap import dedent

from chanel_workers import ChanelWorkerInterface
from data_models import ActiveAlerts
from request_senders import send_get_request
from alertmanager_workers.logger import alertmanager_workers_logger


class AlertmanagerWorker():
    """
    Base class for working with alertmanager.
    args:
        chanel_worker: telegram chanel worker object
        alertmanager_address: address of alertmanager with http/https protocol
        delay: sleep time in seconds for requests to alertmanager
    """
    def __init__(
            self,
            chanel_worker: ChanelWorkerInterface,
            alertmanager_address: str,
            delay: int = 10
        ) -> None:

        self.chanel_worker = chanel_worker
        self.alertmanager_address = alertmanager_address
        self.alertmanager_alerts_address = self.alertmanager_address + "api/v2/alerts"
        self.delay = delay


    async def sync_alerts(self) -> None:
        """
        Sync alerts in chats with alerts in alertmanager.
        This method use get-request to alertmanager, get all alerts
        for a curent moment and send that to specified chanel worker. 
        """
        while True:
            alertmanager_workers_logger.debug(dedent("""\
                                Request active alerts from alertmanager and sync them in chats
                                """))
            alerts = await send_get_request(self.alertmanager_alerts_address)
            alerts = {"alerts": alerts}
            alerts = ActiveAlerts(**alerts)
            await self.chanel_worker.sync_alerts(alerts)
            await asyncio.sleep(self.delay)
