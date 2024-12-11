"""Alertmanager Worker main class"""

from os import remove, listdir
from asyncio import sleep
from uuid import uuid4
from textwrap import dedent
from request_senders import send_get_image_request, WrongResponseCode
from grafana_workers.logger import grafana_workers_logger


class GrafanaWorker():
    """
    Base class for working with Grafana.
    args:
        grafana_url: url to Grafana service
        grafana_auth_token: service authorization token
    """
    def __init__(
            self,
            grafana_url: str,
            grafana_auth_token: str
        ) -> None:

        self.grafana_url = grafana_url
        self.grafana_auth_token = grafana_auth_token
        self.grafana_renderer_url = self.grafana_url + "renderer"


    async def get_rendered_pane(self, pane_url: str) -> str:
        """
        Get rendered pane from grafana as image
        args:
            pane_url: url to pane
        """
        grafana_workers_logger.debug(dedent("""\
            get rendered pane request
            url is - %s
            """
            ),
            pane_url
        )
        panel_rendered = False
        timeout_count = 0
        while not panel_rendered:
            try:
                image_file_name = "images/" + str(uuid4()) + ".png"
                await send_get_image_request(
                    output_file_name = image_file_name,
                    url = pane_url,
                    authorization_header={"Authorization": f"Bearer {self.grafana_auth_token}"}
                )
                panel_rendered = True

            except WrongResponseCode as err:
                if err.status == 504:
                    timeout_count += 1
                    if timeout_count < 5:
                        grafana_workers_logger.warning(dedent("""\
                            Get rendered pane request timeout. Timeout count - %s
                            """
                            ), timeout_count
                        )
                        await sleep(5)
                        continue
                    else:
                        raise RenderPaneTimeOut from err
                else:
                    raise RenderPaneFailed from err

        return image_file_name


    async def delete_pane(self, pane_path: str):
        """
        Delete rendered pane from file system
        args:
            pane_path: path to pane
        """
        remove(pane_path)


    async def delete_all_panes(self):
        """
        Delete rendered panes from file system
        args:
            pane_path: path to pane
        """
        panes = listdir("images/")
        for pane_path in panes:
            await self.delete_pane("images/" + pane_path)


# Module Exceptions


class RenderPaneFailed(Exception):
    """
    Exception for cases when panel render failed by unknown reason
    """
    def __init__(self):
        super().__init__(
            dedent("""
                Pane render failed
            """)
        )

class RenderPaneTimeOut(Exception):
    """
    Exception for cases when panel render time out
    """
    def __init__(self):
        super().__init__(
            dedent("""
                Pane render time out
            """)
        )
