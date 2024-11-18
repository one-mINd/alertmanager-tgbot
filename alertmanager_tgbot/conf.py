"""Service configuration"""
from os import getenv
from textwrap import dedent
from pydantic import ValidationError
import yaml

from data_models import Conf, ConfFile


conf = Conf()


def init_conf():
    """Init common variables"""
    # Telegram client vars
    api_id = getenv("API_ID")
    api_hash = getenv("API_HASH")
    phone_number = getenv("PHONE_NUMBER")
    user_password = getenv("USER_PASSWORD")
    client_name = getenv("CLIENT_NAME")

    # Load configuration files
    try:
        with open("conf/conf.yml", encoding="utf-8") as confs:
            confs = yaml.safe_load(confs)
    except FileNotFoundError as err:
        raise ConfFileNotFound() from err

    confs = {
        k.upper(): v
        for k, v in confs.items()
    }

    # Chats list
    chats = confs.get("CHATS")

    if not chats is None:
        default_chats = []
        for chat in chats:
            if chat.get("default", False):
                chat_id = int(chat["id"])
                default_chats.append(chat_id)

        chats_ids = [id.get("id") for id in chats]

    else:
        default_chats = None
        chats_ids = None

    # Services communication
    alertmanager_address = getenv("ALERTMANAGER_ADDRESS")

    # Permissions
    acl = confs.get("ACL")

    # Bot messages templates
    alert_template = confs.get("ALERT_TEMPLATE")
    resolve_template = confs.get("ALERT_TEMPLATE")

    try:
        global conf
        conf.API_ID=api_id
        conf.API_HASH=api_hash
        conf.PHONE_NUMBER=phone_number
        conf.USER_PASSWORD=user_password
        conf.CLIENT_NAME=client_name
        conf.CONFS=ConfFile(**confs)
        conf.CHATS=chats
        conf.DEFAULT_CHATS=default_chats
        conf.CHATS_IDS=chats_ids
        conf.ALERTMANAGER_ADDRESS=alertmanager_address
        conf.ACL=acl
        conf.ALERT_TEMPLATE=alert_template
        conf.RESOLVE_TEMPLATE=resolve_template

    except ValidationError as err:
        err_type = err.errors()[0].get("type")
        loc = err.errors()[0].get("loc")
        msg = err.errors()[0].get("msg")
        raise ConfValidationError(
            var_name=loc,
            info=msg,
            err_type=err_type
        ) from err


# Module Exceptions


class ConfValidationError(Exception):
    """
    Exception for cases when configuration validation failed
    """
    def __init__(self, var_name: tuple, info: str, err_type: str):
        location = [str(i) for i in var_name]
        self.var_name = '->'.join(location)
        self.info = info
        self.err_type = err_type
        super().__init__(
            dedent(f"""Configuration invalid.
                Reason: {self.err_type}
                Variable name: {self.var_name}
                Details: {self.info}
            """)
        )


class ConfFileNotFound(Exception):
    """
    Exception for cases when configuration file not found
    """
    def __init__(self):
        super().__init__(
            dedent("""Configuration file not found. Make sure it is located in conf/conf.yml""")
        )
