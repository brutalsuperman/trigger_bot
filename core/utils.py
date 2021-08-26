import requests
from core.config import TOKEN
from core.models import WorldTop
from peewee import IntegrityError


def update_world_top(emodji, name, points, date, action=None, gold=None):

    data = {"points": points, "emodji": emodji, "name": name, "date": date}
    update = {"points": points}
    if action:
        data['action'] = action
        update['action'] = action
    if gold:
        data['gold'] = gold
        update['gold'] = gold

    wt = WorldTop.insert(
        **data).on_conflict(
        conflict_target=(WorldTop.date, WorldTop.name, WorldTop.emodji),
        preserve=(WorldTop.date, WorldTop.name, WorldTop.emodji),
        update={**update}).execute()


def get_all_world_top(date):
    wt = WorldTop.select().where(WorldTop.date == date).order_by(WorldTop.points.desc())
    return wt


def add_world_top(emodji, name, points, old_date, date, action=None, gold=None):
    wt = WorldTop.get_or_none(WorldTop.emodji == emodji, WorldTop.name == name, WorldTop.date == old_date)
    if wt:
        update_world_top(wt.emodji, wt.name, wt.points + int(points), date, action, gold)
    return wt


def get_castle_gold(emodji, date):
    castle = WorldTop.get_or_none(WorldTop.emodji == emodji, WorldTop.date == date)
    return castle or None


def date_to_cw_battle(date):
    if date.hour >= 6 and date.hour < 14:
        date = date.replace(hour=6, minute=0, second=0)
    elif date.hour >= 14 and date.hour < 22:
        date = date.replace(hour=14, minute=0, second=0)
    else:
        if date.hour >= 22:
            date = date.replace(hour=22, minute=0, second=0)
        elif date.hour < 6:
            from datetime import timedelta
            date = date.replace(hour=22, minute=0, second=0) - timedelta(days=1)
    return date


def send_message(chat_id, text=None, data=None):
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    if data is None:
        data = {
            'chat_id': chat_id,
            'text': text,
            'disable_notification': True
        }
    else:
        data = data
    resp = requests.post(url, data)
