import json

from models import (Alliances, Duels, GoldRules, Report, Request, Spot,
                    TimeTrigger, Token, Trigger, UserData, WorldTop, WtbLogs)
from peewee import IntegrityError


def save_trigger(chat_id, trigger_name, trigger_type, value):
    try:
        trigger = Trigger.create(
            chat_id=chat_id, trigger_name=trigger_name.lower(),
            trigger_type=trigger_type, trigger_value=value)
    except IntegrityError:
        return False
    return trigger


def get_all_triggers(chat_id):
    triggers = Trigger.select().where(Trigger.chat_id == chat_id).order_by(Trigger.trigger_name)
    return triggers or None


def delete_trigger(chat_id, trigger_name):
    trigger = Trigger.get_or_none(chat_id=chat_id, trigger_name=trigger_name)
    if trigger:
        trigger.delete_instance()
        return True
    return False


def find_trigger(chat_id, trigger_name):
    trigger = Trigger.get_or_none(chat_id=chat_id, trigger_name=trigger_name.lower())
    return trigger or None


def update_trigger(chat_id, trigger_name, trigger_type, value):
    trigger = Trigger.get_or_none(chat_id=chat_id, trigger_name=trigger_name.lower())
    if trigger:
        trigger.trigger_type = trigger_type
        trigger.trigger_value = value
        trigger.save()
        return True
    return False


def save_time_trigger(chat_id, time, trigger_type, value):
    try:
        trigger = TimeTrigger.create(
            chat_id=chat_id, time=time,
            trigger_type=trigger_type, trigger_value=value)
    except IntegrityError:
        return False
    return trigger


def get_time_triggers(time):
    triggers = TimeTrigger.select().where(TimeTrigger.time == time)
    return triggers or None


def delete_time_trigger(chat_id, time):
    trigger = TimeTrigger.get_or_none(chat_id=chat_id, time=time)
    if trigger:
        trigger.delete_instance()
        return True
    return False


def get_all_time_triggers(chat_id=None):
    if chat_id:
        triggers = TimeTrigger.select().where(TimeTrigger.chat_id == chat_id)
    else:
        triggers = TimeTrigger.select()
    return triggers or None


def create_spot(name, code, spot_type, chat_id):
    chat_id = -1001168950089
    try:
        spot = Spot.create(
            name=name, code=code, spot_type=spot_type, chat_id=chat_id)
    except IntegrityError:
        return False
    return spot


def get_all_ali_spots(chat_id=None):
    chat_id = -1001168950089
    if chat_id:
        spots = Spot.select().where(Spot.chat_id == chat_id)
    return spots or None


def get_spot_by_name(name):
    spot = Spot.get_or_none(name=name)
    return spot


def delete_ali_spot(chat_id, code_spot):
    chat_id = -1001168950089
    spot = Spot.get_or_none(chat_id=chat_id, code=code_spot)
    if spot:
        spot.delete_instance()
        return True
    return False


def del_spot_by_name(spot_name):
    spot = Alliances.get_or_none(name=spot_name)
    if spot:
        spot.delete_instance()
        return True
    return False


def create_report(chat_id, nickname, text, date):
    try:
        report = Report.create(
            nickname=nickname, text=text, date=date, chat_id=chat_id)
    except IntegrityError:
        return False
    return report


def find_report(chat_id, date, nickname=None):
    if chat_id:
        if not nickname:
            reports = Report.select().where(Report.chat_id == chat_id, Report.date == date).order_by(Report.nickname)
        else:
            reports = Report.select().where(Report.chat_id == chat_id, Report.nickname == nickname).order_by(-Report.date)
        return reports
    return None


def find_token(chat_id):
    token = Token.get_or_none(chat_id=chat_id)
    if not token:
        return False
    else:
        return token


def create_request(chat_id, action, request_id='', operation=''):
    request = Request.insert(
        chat_id=chat_id, action=action, req_id=request_id, operation=operation).on_conflict(
        conflict_target=(Request.chat_id),
        preserve=(Request.chat_id),
        update={
            "action": action,
            "req_id": request_id,
            "operation": operation}).execute()


def find_request(chat_id):
    request = Request.get_or_none(chat_id=chat_id)
    return request


def create_token(chat_id, token):
    try:
        token = Token.create(token=token, chat_id=chat_id)
    except IntegrityError:
        pass


def create_user_data(chat_id, type, data):
    ud = UserData.insert(chat_id=chat_id, type=type, data=data).on_conflict(
        conflict_target=(UserData.chat_id, UserData.type),
        preserve=(UserData.chat_id, UserData.type),
        update={"data": data}).execute()


def get_user_data(chat_id=None, type=None):
    if chat_id:
        user_data = UserData.get_or_none(chat_id=chat_id, type=type)
    else:
        user_data = UserData.select().where(UserData.type == type)
    return user_data


def create_rules(chat_id, rules):
    gr = GoldRules.insert(chat_id=chat_id, rules=rules).on_conflict(
        conflict_target=(GoldRules.chat_id),
        preserve=(GoldRules.chat_id),
        update={"rules": rules}).execute()


def update_rules(chat_id, auto=True):
    rules = GoldRules.select().where(GoldRules.chat_id == chat_id).get()
    rules.auto = auto
    rules.save()


def get_gold_rules(chat_id):
    gr = GoldRules.get_or_none(chat_id=chat_id)
    return gr


def get_all_rules():
    gr = GoldRules.select().where((GoldRules.auto == True) | (GoldRules.auto == None))
    return gr


def get_my_rules(chat_id):
    rules = GoldRules.get_or_none(chat_id=chat_id)
    if not rules:
        return False
    return rules


def create_wtb(chat_id, quantity, price, item=None):
    wtb = WtbLogs.create(chat_id=chat_id, quantity=quantity, price=price, item=item)


def get_wtb_log(chat_id, date):
    wtb_logs = WtbLogs.get_or_none(WtbLogs.chat_id == chat_id, WtbLogs.date >= date)
    return wtb_logs


def update_wtb_log(chat_id, date, status, quantity):
    wtb_logs = WtbLogs.select().where(
        WtbLogs.chat_id == chat_id).get()
    wtb_logs.status = status
    wtb_logs.save()


def delete_log(chat_id, status=None):
    log = WtbLogs.get_or_none(chat_id=chat_id)
    if log:
        log.delete_instance()
        return True
    return False


def get_stock(chat_id, type):
    stock = UserData.get_or_none(chat_id=chat_id, type=type)
    return stock


def create_alliances_spot(alliance, guild, date, type=None):
    created = Alliances.insert(name=guild, alliance=alliance, date=date, type=type).on_conflict(
        conflict_target=(Alliances.name),
        preserve=(Alliances.name),
        update={
            "alliance": alliance,
            "date": date}).execute()

    return created


def get_all_alliances(alliance=None, type=None):
    alliance_guilds = None
    if alliance:
        alliance_guilds = Alliances.select(Alliances, Spot).join(
            Spot, on=(Alliances.alliance == Spot.name), attr='extra').where(
                Alliances.alliance == alliance, Alliances.type == type).order_by(
                    Alliances.date.desc())
    else:
        alliance_guilds = Alliances.select(Alliances, Spot).join(
            Spot, on=(Alliances.alliance == Spot.name), attr='extra').where(
                Alliances.type == type).order_by(
                    Alliances.date.desc())
    return alliance_guilds


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
            date = date.replace(day=date.day - 1, hour=22, minute=0, second=0)
    return date


def delete_spot(alliance, name, type='spot'):
    spot = Alliances.get_or_none(alliance=alliance, name=name, type=type)
    if spot:
        spot.delete_instance()
        return True
    return False


def create_duel(date, winner_id, *args, **kwargs):
    duel = Duels.insert(date=date, winner_id=winner_id,
        **kwargs).on_conflict(
        conflict_target=(Duels.date, Duels.winner_id),
        preserve=(Duels.date, Duels.winner_id),
        update={**kwargs}).execute()


def get_duels(chat_id, date, username=None):
    if not username:
        user = UserData.get_or_none(chat_id=chat_id, type='requestProfile')
        if user:
            user = json.loads(user.data)
            username = user.get('userName')
        else:
            return False, None
    duels = Duels.select().where(Duels.date >= date, (
        (Duels.winner_name == username) | (Duels.loser_name == username)))
    return duels, username
