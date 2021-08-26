import json
from datetime import datetime

import pytz
from config import TIMEZONE, LOCAL_TIMEZONE
from kafka import KafkaConsumer
from utils import create_prices

topic = 'cw3-sex_digest'

consumer = KafkaConsumer(
    topic,
    bootstrap_servers="digest-api.chtwrs.com:9092",
    auto_offset_reset='latest',
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode('utf-8')))

for message in consumer:
    date = datetime.fromtimestamp(
        int(message.timestamp / 1000)).replace(tzinfo=pytz.timezone(LOCAL_TIMEZONE))
    date = date.astimezone(pytz.timezone(TIMEZONE))
    msg = message.value
    for item in msg:
        create_prices(item.get('name'), item.get('prices'))

    print('{} '.format(msg))
