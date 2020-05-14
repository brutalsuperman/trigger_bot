from models import TimeTrigger, Trigger
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
