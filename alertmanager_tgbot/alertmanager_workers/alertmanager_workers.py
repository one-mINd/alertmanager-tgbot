"""Alertmanager Worker main class"""

import asyncio
from textwrap import dedent

from chanel_workers import ChanelWorkerInterface
from data_models import ActiveAlerts, EnrichedActiveAlerts, EnrichedActiveAlert, Silence, BaseAlert, MuteMatcher, Mute
from request_senders import send_get_request, send_post_request, send_delete_request
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
            alertmanager_address: str,
            chanel_worker: ChanelWorkerInterface = None,
            delay: int = 10
        ) -> None:

        self.chanel_worker = chanel_worker
        self.alertmanager_address = alertmanager_address
        self.alertmanager_alerts_address = self.alertmanager_address + "api/v2/alerts"
        self.alertmanager_silences_address = self.alertmanager_address + "api/v2/silences"
        self.alertmanager_silence_address = self.alertmanager_address + "api/v2/silence"
        self.delay = delay


    def set_chanel_worker(self, chanel_worker: ChanelWorkerInterface) -> None:
        """
        Set chanel worker 
        """
        self.chanel_worker = chanel_worker


    async def create_silence(self, mute: Mute) -> str:
        """
        Create silence in alertmanager
        args:
            silence: silence that will be created
        """
        response = await send_post_request(
            url=self.alertmanager_silences_address,
            message=mute.dict()
        )

        return response['silenceID']


    async def delete_silence(self, silence_id: str) -> None:
        """
        Delete silence by id
        args:
            silence: silence that will be created
        """
        await send_delete_request(
            url=self.alertmanager_silence_address+"/"+silence_id
        )


    async def mute_alert(
            self,
            alert: BaseAlert,
            ends_at: str = '',
            created_by: str = '',
            comment: str = ''
        ) -> None:
        """
        Create silence by all labels in specified alert
        args:
            alert: alert that will be muted
        """
        mute_matchers = []
        for label in alert.labels:
            mute_matchers.append(
                MuteMatcher(
                    name=label,
                    value=alert.labels[label]
                )
            )

        if ends_at != '':
            mute = Mute(
                matchers=mute_matchers,
                endsAt=ends_at,
                createdBy=created_by,
                comment=comment,
            )

        else:
            mute = Mute(
                matchers=mute_matchers,
                createdBy=created_by,
                comment=comment,
            )

        silence_id = await self.create_silence(mute)
        return silence_id


    async def unmute_alert(self, alert: EnrichedActiveAlert) -> None:
        """
        Unmute specified alert
        args:
            silence: silence that will be created
        """
        silence_id = alert.silences[0].id
        await self.delete_silence(silence_id)
        return silence_id


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
