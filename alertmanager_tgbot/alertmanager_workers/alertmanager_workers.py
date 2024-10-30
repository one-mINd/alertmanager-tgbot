"""Alertmanager Worker main class"""

import asyncio
from textwrap import dedent

from chanel_workers import ChanelWorkerInterface
from data_models import ActiveAlerts, EnrichedActiveAlerts, EnrichedActiveAlert, Silence
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


    def alerts_filter(self, alerts: ActiveAlerts) -> ActiveAlerts:
        """
        Filter alerts and remove unnecessary ones 
        args:
            alerts: active alerts list
        """
        result = []
        for alert in alerts.alerts:
            if len(alert.status.inhibitedBy) != 0:
                continue

            if len(alert.receivers) == 0:
                continue

            if len(alert.receivers) == 1 and \
                alert.receivers[0].get("name") == "blackhole":
                continue

            result.append(alert)

        result = {"alerts": result}
        return ActiveAlerts(**result)


    async def enrich_alerts_silences(self, alerts: ActiveAlerts) -> EnrichedActiveAlerts:
        """
        Add silences information to existed active alerts
        args:
            alerts: active alerts list
        """
        result = []
        for alert in alerts.alerts:
            alert = EnrichedActiveAlert(**alert.dict())

            if len(alert.status.silencedBy) > 0:
                for silence_id in alert.status.silencedBy:
                    silence = await send_get_request(
                        self.alertmanager_address \
                        + "api/v2/silence/" \
                        + silence_id
                    )

                    silence = Silence(**silence)
                    alert.silences.append(silence)

            result.append(alert)

        result = {"alerts": result}
        return EnrichedActiveAlerts(**result)


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
            alerts = self.alerts_filter(alerts)
            alerts = await self.enrich_alerts_silences(alerts)
            await self.chanel_worker.sync_alerts(alerts)
            await asyncio.sleep(self.delay)
