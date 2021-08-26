import json
from datetime import datetime, timedelta

import pika
from core.config import api_auth, consumer_key
from core.utils import send_message
from peewee import *
from users import utils

url = 'amqps://{}@api.chtwrs.com:5673'.format(api_auth)
params = pika.URLParameters(url)
params.socket_timeout = 5

connection = pika.BlockingConnection(params)
channel = connection.channel()


db = PostgresqlDatabase('ogwbot', user='ogw', password='kalavera')
db.connect()


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
            cw_id = payload.get('id')
            utils.create_token(user_id, token, cw_id)
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
            text = 'Сток обновил, можно сдавать. Открой @ChatWarsBot бота и напиши @OGWHelperbot после чего выбирай из списка.'

            keyboard = json.dumps({
                "inline_keyboard": [[
                    {
                        "text": "Deposit",
                        "switch_inline_query": " "}]]})

            data = {
                "chat_id": user_id,
                "parse_mode": "HTML",
                "text": text,
                "reply_markup": keyboard}

            send_message(user_id, text, data=data)
        elif action == 'guildInfo':
            old = utils.get_user_data(user_id, type='guildInfo')
            old_glory = 0
            if old:
                old = json.loads(old.data)
                old_glory = old.get('glory', 0)

            new_glory = payload.get('glory', 0)
            if new_glory != old_glory:
                text = '+{} гп'.format(new_glory - old_glory)
                send_message(user_id, text)
            utils.create_user_data(user_id, type='guildInfo', data=json.dumps(payload))
        elif action == 'requestGearInfo':
            gear = payload.get('gearInfo', {})
            utils.create_user_data(user_id, type='requestGearInfo', data=json.dumps(gear))
            broken = []
            for value in gear.values():
                if value.get('condition') == 'broken':
                    broken.append(value.get('name'))

            if len(broken):
                text = 'Похоже у тебя сломаны вещи \n' + '/n'.join(broken) + '\n\nГо чинить'
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
