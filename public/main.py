import json
from datetime import datetime
from threading import Thread

import pytz
from core.config import TIMEZONE
from kafka import KafkaConsumer
from public.utils import *
from users.utils import create_duel, update_guild, update_user

topic = 'cw3-duels'


class PublicThread(Thread):
    def __init__(self, topic):
        Thread.__init__(self)
        self.topic = topic

    def run(self):
        if self.topic in ['cw3-sex_digest', 'cw3-deals']:
            offset = 'latest'
        else:
            offset = 'earliest'
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers="digest-api.chtwrs.com:9092",
            auto_offset_reset=offset,
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')))

        for message in consumer:

            if self.topic == 'cw3-duels':
                date = datetime.fromtimestamp(
                    int(message.timestamp / 1000)).replace(tzinfo=pytz.timezone('CET'))
                date = date.astimezone(pytz.timezone(TIMEZONE))
                msg = message.value
                loser = msg.get('loser')
                winner = msg.get('winner')
                if all([winner, loser]):
                    create_duel(
                        date=date,
                        winner_id=winner.get('id'), winner_castle=winner.get('castle'),
                        winner_name=winner.get('name'), winner_level=winner.get('level'),
                        winner_guild=winner.get('tag'),
                        loser_id=loser.get('id'), loser_castle=loser.get('castle'),
                        loser_name=loser.get('name'), loser_level=loser.get('level'),
                        loser_guild=loser.get('tag'))
                    if loser.get('tag'):
                        update_guild(castle=loser.get('castle'), guild=loser.get('tag'), where='duels', date=date)
                        update_user(
                            cw_id=loser.get('id'), nick=loser.get('name'), castle=loser.get('castle'),
                            guild=loser.get('tag'), level=loser.get('level'), where='duel', date=date)
                    if winner.get('tag'):
                        update_guild(castle=winner.get('castle'), guild=winner.get('tag'), where='duels', date=date)
                        update_user(
                            cw_id=winner.get('id'), nick=winner.get('name'), castle=winner.get('castle'),
                            guild=winner.get('tag'), where='duel', level=winner.get('level'), date=date)
                print('{} '.format(msg))

            elif self.topic == 'cw3-sex_digest':
                date = datetime.fromtimestamp(
                    int(message.timestamp / 1000)).replace(tzinfo=pytz.timezone('CET'))
                date = date.astimezone(pytz.timezone(TIMEZONE))
                msg = message.value
                for item in msg:
                    create_prices(item.get('name'), item.get('prices'))

                print('{} '.format(msg))
            elif self.topic == 'cw3-deals':
                print(2222)
                date = datetime.fromtimestamp(
                    int(message.timestamp / 1000)).replace(tzinfo=pytz.timezone('CET'))
                date = date.astimezone(pytz.timezone(TIMEZONE))
                print(date)
                msg = message.value

                # {
                #     'sellerId': 'd9494c26009545329aa372b20cbfd7e3',
                #     'sellerName': 'spektor 23',
                #     'sellerCastle': '🦇',
                #     'buyerId': '12455c95e61d453bb08064ff937da2db',
                #     'buyerName': 'Я ВЕГАН',
                #     'buyerCastle': '🍆', 'item': 'Coke', 'qty': 10, 'price': 4}

                update_user(cw_id=msg.get('sellerId'), nick=msg.get('sellerName'),
                            castle=msg.get('sellerCastle'), where='deals', date=date)
                update_user(cw_id=msg.get('buyerId'), nick=msg.get('buyerName'),
                            castle=msg.get('buyerCastle'), where='deals', date=date)
                send_to_seller(
                    seller=msg.get('sellerId'), buyer=msg.get('buyerCastle') + msg.get('buyerName'),
                    item=msg.get('item'), qty=msg.get('qty'), price=msg.get('price'))


topics = ['cw3-deals']#, 'cw3-duels', 'cw3-sex_digest']
print(1111)
for topic in topics:
    thread = PublicThread(topic=topic)
    thread.start()
