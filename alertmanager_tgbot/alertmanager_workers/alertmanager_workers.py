"""Alertmanager Worker main class"""

import asyncio
from textwrap import dedent

from chanel_workers import ChanelWorkerInterface
from data_models import ActiveAlerts, EnrichedActiveAlerts, EnrichedActiveAlert, Silence, Mute
from request_senders import send_get_request, send_post_request, send_delete_request
from alertmanager_workers.logger import alertmanager_workers_logger
from grafana_workers import GrafanaWorker


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
            grafana_worker: GrafanaWorker,
            alertmanager_address: str,
            chanel_worker: ChanelWorkerInterface = None,
            delay: int = 10
        ) -> None:

        self.grafana_worker = grafana_worker
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


    async def unmute_alert(self, alert: EnrichedActiveAlert) -> None:
        """
        Unmute specified alert
        args:
            silence: silence that will be created
        """
        if len(alert.silences) == 0:
            raise AlertHasntSilence()

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


    async def enrich_alerts(self, alerts: ActiveAlerts) -> EnrichedActiveAlerts:
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

            alert_labels_panes = [l for l in alert.labels if "pane-" in l]
            if len(alert_labels_panes) > 0:
                for pane in alert_labels_panes:
                    pane = alert.labels.get(pane)
                    pane_image_path = await self.grafana_worker.get_rendered_pane(pane)
                    alert.panes.append(pane_image_path)

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
            try:
                alertmanager_workers_logger.debug(dedent("""\
                                    Request active alerts from alertmanager and sync them in chats
                                    """))
                alerts = await send_get_request(self.alertmanager_alerts_address)
                alerts = {"alerts": alerts}
                alerts = ActiveAlerts(**alerts)
                alerts = self.alerts_filter(alerts)
                alerts = await self.enrich_alerts(alerts)
                await self.chanel_worker.sync_alerts(alerts)
                await self.grafana_worker.delete_all_panes()
                await asyncio.sleep(self.delay)

            except Exception as err:
                alertmanager_workers_logger.error(dedent("""\
                                    Sync alerts failed. Reason is - %s
                                    """), str(err))
                continue


# Module Exceptions


class AlertHasntSilence(Exception):
    """
    Exception for cases when alert has not any related silence
    """
    def __init__(self):
        super().__init__(
            dedent("""
                Alert does not have any silences
            """)
        )
