import json
from functools import wraps

import pika
from core.config import api_auth, exchange_key, routing_key


def connection_decorator(func):
    @wraps(func)
    def wrapper(*args, **kw):
        url = 'amqps://{}@api.chtwrs.com:5673'.format(api_auth)
        params = pika.URLParameters(url)
        params.socket_timeout = 5

        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        try:
            body = func(*args, **kw)
            channel.basic_publish(exchange=exchange_key, routing_key=routing_key, body=json.dumps(body))
        finally:
            connection.close()
        return body
    return wrapper


additional_operations = [
    'GetUserProfile', 'GetBasicInfo', 'GetGearInfo',
    'GetStock', 'GuildInfo', 'TradeTerminal']

request_actions = [
    'requestProfile', 'requestBasicInfo', 'requestGearInfo',
    'requestStock', 'guildInfo']


@connection_decorator
def createAuthCode(userId):
    body = {
        "action": "createAuthCode",
        "payload": {
            "userId": userId
        }
    }
    return body


@connection_decorator
def grantToken(userId, authCode):
    body = {
        "action": "grantToken",
        "payload": {
            "userId": userId,
            "authCode": authCode
        }
    }
    return body


@connection_decorator
def authAdditionalOperation(token, operation):
    body = {
        "token": token,
        "action": "authAdditionalOperation",
        "payload": {
            "operation": operation
        }
    }
    return body


@connection_decorator
def grantAdditionalOperation(token, requestId, authCode):
    body = {
        "token": token,
        "action": "grantAdditionalOperation",
        "payload": {
            "requestId": requestId,
            "authCode": authCode
        }
    }
    return body


@connection_decorator
def request_action(token, action):
    body = {
        "token": token,
        "action": action
    }
    return body


@connection_decorator
def wantToBuy(token, item_code, quantity, price):
    body = {
        "token": token,
        "action": "wantToBuy",
        "payload": {
            "itemCode": item_code,
            "quantity": quantity,
            "price": price,
            "exactPrice": True
        }
    }
    return body

# request_action(token='b6f33610105ff6451772e5ded311d869', action='requestProfile')
# wantToBuy()
# grantAdditionalOperation(
#     token='b6f33610105ff6451772e5ded311d869', requestId='bu9aa6log3ca13ku6bbg', authCode='664883')
