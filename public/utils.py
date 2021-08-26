from core.utils import send_message
from peewee import IntegrityError
from public.models import Prices
from users.models import UserSettings


def create_prices(name, price):
    price = Prices.insert(name=name, prices=price).on_conflict(
        conflict_target=(Prices.name),
        preserve=(Prices.name),
        update={"prices": price}).execute()


def get_prices(code):
    price = Prices.get_or_none(code=str(code))
    return price


def update_resourse_code(name, code):
    res = Prices.get_or_none(name=name)
    if res:
        res.code = code
        res.save()


def send_to_seller(seller, buyer, item, qty, price):

    user_settings = UserSettings.get_or_none(cw_id=seller)
    if user_settings and user_settings.sell_notification:
        text = '⚖️Вы продали {} за {}💰 ({} x {}💰)\nПокупатель: {}'.format(item, qty * price, qty, price, buyer)
        send_message(user_settings.telegram_id, text)
