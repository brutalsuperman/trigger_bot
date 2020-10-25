
import pika
import json
import utils
from peewee import *
from config import api_auth, consumer_key, TOKEN
from datetime import datetime, timedelta

url = 'amqps://{}@api.chtwrs.com:5673'.format(api_auth)
params = pika.URLParameters(url)
params.socket_timeout = 5


connection = pika.BlockingConnection(params)
channel = connection.channel()


db = SqliteDatabase('sqlite.db')
db.connect()


def send_message(chat_id, text):
    import requests
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    data = {
        'chat_id': chat_id,
        'text': text
    }
    resp = requests.post(url, data)


def callback(ch, method, properties, body):
    response = json.loads(body)
    action = response.get('action')
    payload = response.get('payload', {})
    user_id = payload.get('userId')
    if response.get('result', None) == 'Forbidden':
        need_auth = response.get('payload', {}).get('requiredOperation')
        if need_auth == 'GetStock':
            text = 'Мне нужен доступ к стоку, дать доступ /auth_stock'
            send_message(user_id, text)
        print('need_auth {}'.format(need_auth))
    elif response.get('result', None) == 'Ok':
        request_id = response.get('uuid', '')
        operation = payload.get('operation', '')
        user_id = payload.get('userId')
        if action == 'grantToken':
            token = payload.get('token')
            utils.create_token(user_id, token)
            text = 'Авторизация прошла успешно.'
            send_message(user_id, text)
        elif action == 'authAdditionalOperation':
            utils.create_request(user_id, action, request_id, operation)
        elif action == 'createAuthCode':
            utils.create_request(user_id, action)
        elif action == 'grantAdditionalOperation':
            request = utils.find_request(int(user_id))
            text = 'Доступ получен'
            if request and request.operation == 'TradeTerminal':
                text += '\n Еще 1 шаг дай доступ до голды /profile'
            send_message(user_id, text)
        elif action == 'requestProfile':
            profile = payload.get('profile', {})
            utils.create_user_data(user_id, type='requestProfile', data=json.dumps(profile))
        elif action == 'requestStock':
            stock = payload.get('stock')
            item_codes = payload.get('itemCodes')
            not_deposited = [
                'Gris murky potion', 'Azure murky potion',
                'Crimson murky potion', 'Wrapping', 'Pouch of gold']
            new_dict = {}
            for key, value in item_codes.items():
                if value not in not_deposited:
                    new_dict[key] = {
                        'value': stock.get(value, 0),
                        'name': value}

            utils.create_user_data(user_id, type='requestStock', data=json.dumps(new_dict))
            text = 'Сток обновил, можно сдавать'
            send_message(user_id, text)

    if action == 'wantToBuy':
        user_id = payload.get('userId')
        date = datetime.utcnow() - timedelta(hours=3)
        quantity = payload.get('quantity', 0)
        utils.update_wtb_log(chat_id=user_id, date=date, status=response.get('result', None), quantity=quantity)

    print('Recived {}'.format(body))


channel.basic_consume(consumer_key, callback, auto_ack=True)


channel.start_consuming()  # start consuming (blocks)
connection.close()
