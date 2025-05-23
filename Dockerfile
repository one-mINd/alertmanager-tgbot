FROM python:3.9

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "alertmanager_tgbot"]
