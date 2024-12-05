
# Alertmanager telegram bot

This project is designed to work with alerts from alertmanager. It extends the basic functionality of the original telegram bot available in alertmanager. With this project, you can see only currently active alerts in the telegram channel and create silences without leaving telegram. **Attention** - the project works exclusively on a full-fledged telegram account, and is not able to work through bots created in BotFather

## Configuration
The project is configured in two ways at once: using environment variables and a configuration file.

### environment variables
The project requires the following environment variables:

 - API_ID/API_HASH - You can get these values ​​using the following link - https://core.telegram.org/api/obtaining_api_id
 - PHONE_NUMBER - The phone number to which the account is linked
 - USER_PASSWORD (Optional) - Account password
 - CLIENT_NAME - The name of the client that will be used to create session file names.
 - ALERTMANAGER_ADDRESS - Alertmanager URL
 - GRAFANA_AUTH_TOKEN - Token for authorization in grafana for rendering panels
 #### The following variables are required if you want to run the project in a docker container
 - IMAGE_TAG - Project image tag. You can find all possible tags here - https://github.com/one-mINd/alertmanager-tgbot/tags 
 - CONF_DIR - The directory on host where the configuration file is located and session files will be stored
 - LISTENING_ADDR/LISTENING_PORT - the address at which the project will be available

### Configuration file
The file is in yaml format. It must be called **conf.yml** and stored in the project's **conf** directory, or in the **CONF_DIR** variable path if you are running the project in a docker container.

```yaml
# A variable that specifies the chats where alerts will be sent
chats:
    # id - a field that specifies the chat or channel id
    - id: -0000000000000
    # Alerts for which no chats were found will be sent to all chats that have this field
      default: True
    - id: -0000000000001
    # Defining which alerts with which labels will be sent to this chat. 
    # For example, only alerts with labels env with the value production 
    # and db_type with the value postgres will be sent to this chat.
      labels:
          env: production
          db_type: postgres

# Access Control List determines which Telegram users are allowed to perform what actions.
acl:
  some_user:
    - mute # the right to create and delete silences

# Jinja2 template that will format incoming alerts. 
# It is possible to use any fields from the data model, which will be presented below
# Please note that the format_date function is unique to this project.
alert_template: |
  {%- if silences|length > 0 -%}
  [**MUTED** until {{ silences[0].endsAt | format_date('%b %d %Y %H:%M:%S') }}] 
  {% endif -%}
  **Alert Created** 😱
  **Environment**: {{ labels.env }}
  **Host**: {{ labels.dns_hostname }}
  **Alert Name**: {{ labels.alertname }}
  **Status**: {{ labels.severity }} ❗️
  **Summary**: {{ annotations.summary }}
  **Started**: {{ startsAt | format_date('%b %d %Y %H:%M:%S') }}
```

#### Alert datamodel

```yaml
    annotations: Dict[str, str]
    labels: Dict[str, str] = {}
    endsAt: str
    startsAt: str
    fingerprint: str
    generatorURL: str
    updatedAt: str
    receivers: List[Dict[str, str]]
    status:
        inhibitedBy: List[Any]
        silencedBy: List[Any]
        state: str
    silences:
    -   id: str
        status: Dict[str, str]
        updatedAt: str
        startsAt: str
        endsAt: str
        comment: str
        createdBy: str
        matchers: List[MuteMatcher]
```

## Rendering grafana panes
The bot is able to attach panels from Grafana dashboards to alerts. To do this, the bot only needs to specify the GRAFANA_AUTH_TOKEN variable. This is a token with which the bot will log in to Grafana and work with it using the API.
Panels in Grafana are rendered using the configured grafana-image-renderer service. Therefore, make sure that the service is working correctly and Grafana is able to render panels with its help.
In order for the bot to attach panels to alerts, they must have labels whose name matches the `pane-*` mask, and the content must contain a valid URL with a request to Grafana.
You can use the form below to generate a URL:
```
http://<grafana_host>/render/d-solo/<dashboard_id>?orgId=<orgId>&from=<from_timestamp_millis>&to=<to_timestamp_millis>&panelId=<panelId>&width=600&height=448&tz=Europe%2FZurich&theme=light
```

Example of labels with panels in alerts
```
pane-cpu: "http://grafana/render/d-solo/aaaaaaaaaaaaaa?orgId=1&panelId=83&width=1366&height=768&tz=Europe%2FMoscow&theme=light&var-dns_hostname=somehost&var-domainname=somedomain"
pane-memory: "http://grafana/render/d-solo/aaaaaaaaaaaaaa?orgId=2&panelId=2&width=1366&height=768&tz=Europe%2FMoscow&theme=light&var-dns_hostname=somehost&var-domainname=somedomain"
```

## Startup
The first launch on a new server will be very different from all subsequent ones. The fact is that during the first launch you need to log the bot in Telegram, after that the created session file will be used and you will not have to repeat this procedure.

Start the container manually using the command:
```bash
sudo docker run -it -v PATH_TO_CONF_DIR:/app/conf \ 
-e API_ID='your-api-id' \
-e API_HASH='your-api-hash' \
-e PHONE_NUMBER='bot-phone-number' \
-e USER_PASSWORD='bot-password' \ # optional
onemind914/alertmanager-tgbot:latest bash
```

After that, run the bot inside the container with the command below and follow the instructions:
```bash
python3 alertmanager_tgbot
```

After successful authorization, exit the container and run it with the `docker compose up -d` command
