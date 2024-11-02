"""Module provides uvicorn server with FastAPI endpoints"""

from uvicorn import Server, Config
from fastapi import FastAPI, Response, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi_versioning import VersionedFastAPI, version

from chanel_workers import SendAlertFailed, ChanelWorkerInterface
from data_models import Alerts
from api.logger import api_logger
from api.metrics import metrics


app = FastAPI()
bot = ChanelWorkerInterface()


async def process_alerts(alerts: Alerts):
    """
    Function that processes alerts in the background to avoid /alert endpoint overload
    args:
        alerts: Incoming alerts
    """
    api_logger.info("accept incoming alerts - status: %s common labels: %s",
        alerts.status, alerts.commonLabels)
    api_logger.debug("accept incoming alerts - %s", alerts)

    try:
        await bot.send_alerts_to_chats(alerts)
    except SendAlertFailed as err:
        raise HTTPException(status_code=500, detail="Failed send alerts message") from err


@app.post("/alert")
@version(1)
async def alert(alerts: Alerts, background_tasks: BackgroundTasks):
    """
    Endpoint that catches alerts messages from alertmanager
    args:
        alerts: Incoming alerts
        background_tasks: FastAPI defined arg
    """
    # background_tasks.add_task(process_alerts, alerts=alerts)

    return Response(content="Alerts accepted")


@app.get("/health")
@version(1)
async def healthcheck():
    """Status code 200 on every request for healthchecks"""
    api_logger.debug("Response on /health request")
    return Response(content="Ok")


@app.get("/metrics")
@version(1)
async def get_metrics():
    """Return service metrics"""
    api_logger.debug("Response on /metrics request")
    result_metrics = await metrics()
    return PlainTextResponse(content=result_metrics)


app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}')


def get_server(event_loop, host="0.0.0.0", port=8000) -> Server:
    """
    Return uvicorn server with FastAPI object as app in specified asyncio event loop
    args:
        event_loop: Asincio event loop, where uvicorn will work
        host: The interface on which the server will run
        port: The port on which the server will run
    """
    api_logger.debug("Get uvicorn server")
    return Server(Config(app=app, host=host, port=port, loop=event_loop))


def set_bot(new_bot: ChanelWorkerInterface) -> None:
    """
    Set telegram client object as alert bot
    args:
        new_bot: New telethon client bot object that api will use
    """
    global bot
    api_logger.debug("FastAPI will use specified tgbot")
    bot = new_bot
