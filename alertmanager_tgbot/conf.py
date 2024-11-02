"""Service configuration"""
from os import getenv
import yaml

# Telegram client vars
API_ID = int(getenv("API_ID", "0"))
API_HASH = getenv("API_HASH", None)
PHONE_NUMBER = getenv("PHONE_NUMBER", None)
USER_PASSWORD = getenv("USER_PASSWORD", None)
CLIENT_NAME = getenv("CLIENT_NAME", "telegram_bot")

# Load configuration files
with open("conf/conf.yml", encoding="utf-8") as confs:
    CONFS = yaml.safe_load(confs)

# Chats list
CHATS = CONFS.get("chats", [])
DEFAULT_CHATS = []
for chat in CHATS:
    if chat.get("default", False):
        chat_id = int(chat["id"])
        DEFAULT_CHATS.append(chat_id)
CHATS_IDS = [id.get("id") for id in CHATS]

# Services communication
ALERTMANAGER_ADDRESS = getenv("ALERTMANAGER_ADDRESS", "")
if not ALERTMANAGER_ADDRESS.endswith('/'):
    ALERTMANAGER_ADDRESS = ALERTMANAGER_ADDRESS + "/"

# Permissions
ACL = CONFS.get("acl", {})

# Bot messages templates
ALERT_TEMPLATE = CONFS.get("alert_template",
"""
{%- if silences|length > 0 -%}
[**MUTED** until {{ silences[0].endsAt | format_date('%b %d %Y %H:%M:%S') }}] 
{% endif -%}
**Alert Created** 😱
**Host**: {{ labels.dns_hostname }}
**Alert Name**: {{ labels.alertname }}
**Status**: {{ labels.severity }} ❗️
**Summary**: {{ annotations.summary }}
**Started**: {{ startsAt | format_date('%b %d %Y %H:%M:%S') }}
""")

RESOLVE_TEMPLATE = CONFS.get("alert_template",
"""
**Alert Resolved** 😍
**Environment**: {{ labels.env }}
**Host**: {{ labels.dns_hostname }}
**Alert Name**: {{ labels.alertname }}
**Status**: OK 👍
**Summary**: {{ annotations.summary }}
**Ended**: {{ startsAt | format_date('%b %d %Y %H:%M:%S') }}
""")
