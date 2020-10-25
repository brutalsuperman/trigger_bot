from models import (Alliance, GoldRules, Report, Request, TimeTrigger, Token,
                    Trigger, UserData, WtbLogs)
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
    try:
        spot = Alliance.create(
            name=name, code=code, spot_type=spot_type, chat_id=chat_id)
    except IntegrityError:
        return False
    return spot


def get_all_ali_spots(chat_id=None):
    if chat_id:
        spots = Alliance.select().where(Alliance.chat_id == chat_id)
    return spots or None


def delete_ali_spot(chat_id, code_spot):
    spot = Alliance.get_or_none(chat_id=chat_id, code=code_spot)
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


def find_report(chat_id, date):
    if chat_id:
        reports = Report.select().where(Report.chat_id == chat_id, Report.date == date).order_by(Report.nickname)
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


def get_user_data(chat_id, type):
    user_data = UserData.get_or_none(chat_id=chat_id, type=type)
    return user_data


def create_rules(chat_id, rules):
    gr = GoldRules.insert(chat_id=chat_id, rules=rules).on_conflict(
        conflict_target=(GoldRules.chat_id),
        preserve=(GoldRules.chat_id),
        update={"rules": rules}).execute()


def get_gold_rules(chat_id):
    gr = GoldRules.get_or_none(chat_id=chat_id)
    return gr


def get_all_rules():
    gr = GoldRules.select()
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


def delete_log(chat_id, status):
    log = WtbLogs.get_or_none(chat_id=chat_id)
    if log:
        log.delete_instance()
        return True
    return False


def get_stock(chat_id, type):
    stock = UserData.get_or_none(chat_id=chat_id, type=type)
    return stock
