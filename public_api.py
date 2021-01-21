import json
from datetime import datetime

import pytz
from config import TIMEZONE, LOCAL_TIMEZONE
from kafka import KafkaConsumer
from utils import create_duel

topic = 'cw3-duels'

consumer = KafkaConsumer(
    topic,
    bootstrap_servers="digest-api.chtwrs.com:9092",
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode('utf-8')))

for message in consumer:
    date = datetime.fromtimestamp(
        int(message.timestamp / 1000)).replace(tzinfo=pytz.timezone(LOCAL_TIMEZONE))
    date = date.astimezone(pytz.timezone(TIMEZONE))
    msg = message.value
    loser = msg.get('loser')
    winner = msg.get('winner')
    if all([winner, loser]):
        print(date)
        create_duel(
            date=date,
            winner_id=winner.get('id'), winner_castle=winner.get('castle'),
            winner_name=winner.get('name'), winner_level=winner.get('level'),
            winner_guild=winner.get('tag'),
            loser_id=loser.get('id'), loser_castle=loser.get('castle'),
            loser_name=loser.get('name'), loser_level=loser.get('level'),
            loser_guild=loser.get('tag'))
    # collection.insert_one(message)
    print('{} '.format(msg))
