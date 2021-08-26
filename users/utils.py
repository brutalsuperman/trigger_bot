import json

from peewee import IntegrityError
from users.models import *


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


def create_token(chat_id, token, cw_id=None):
    print(chat_id, token, cw_id)
    try:
        token = Token.create(token=token, chat_id=chat_id)
    except IntegrityError:
        pass
    if cw_id:
        user = Users.get_or_none(cw_id=cw_id)
        if user:
            user.telegram_id = chat_id
            user.save()
        user_settings = UserSettings.get_or_none(telegram_id=chat_id)
        if not user_settings:
            UserSettings.create(cw_id=cw_id, telegram_id=chat_id)


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


def get_stock(chat_id, type):
    stock = UserData.get_or_none(chat_id=chat_id, type=type)
    return stock


def create_duel(date, winner_id, *args, **kwargs):
    duel = Duels.insert(date=date, winner_id=winner_id,
        **kwargs).on_conflict(
        conflict_target=(Duels.date, Duels.winner_id),
        preserve=(Duels.date, Duels.winner_id),
        update={**kwargs}).execute()


def get_duels(chat_id, date, username=None):
    guild_tag = None
    if not username:
        user = UserData.get_or_none(chat_id=chat_id, type='requestProfile')
        if user:
            user = json.loads(user.data)
            username = user.get('userName')
            guild_tag = user.get('guild_tag', False)
        else:
            return False, None
    if guild_tag:
        duels = Duels.select().where(Duels.date >= date, (
            (
                (Duels.winner_name == username) & (Duels.winner_guild == guild_tag)) | (
                (Duels.loser_name == username) & (Duels.loser_guild == guild_tag))))
        return duels, username
    else:
        duels = Duels.select().where(Duels.date >= date, (
            (Duels.winner_name == username) | (Duels.loser_name == username)))
        return duels, username


def get_guild_duels(chat_id, date, guild=None):
    if not guild:
        user = UserData.get_or_none(chat_id=chat_id, type='requestProfile')
        if user:
            user = json.loads(user.data)
            guild = user.get('guild_tag')
        else:
            return False, None
    duels = Duels.select().where(Duels.date >= date, (
        (Duels.winner_guild == guild) | (Duels.loser_guild == guild)))
    return duels, guild


def update_user(castle, nick, guild='🤷', where=None, date=None, *args, **kwargs):
    data = kwargs
    created = False
    if 'cw_id' in data:
        cw_id = data.get('cw_id')
        del data['cw_id']

        user = Users.get_or_none(Users.cw_id == cw_id)
        if not user:
            try:
                user = Users.create(castle=castle, guild=guild, name=nick, where=where, last_seen=date, cw_id=cw_id, **kwargs)
                created = True
            except IntegrityError:
                user = Users.get_or_create(name=nick, guild=guild)
                user = user[0]
                user.cw_id = cw_id
    else:
        user = Users.get_or_none(name=nick, guild=guild)
        if not user:
            user = Users.create(castle=castle, guild=guild, name=nick, where=where, last_seen=date)
            created = True
    if not created:
        user.castle = castle
        user.where = where
        user.last_seen = date
        if data.get('level', 0) != 0:
            user.level = data.get('level')
        user.save()


def get_users(guild):
    users = Users.select().where(Users.guild == guild).order_by(Users.level.desc(), Users.last_seen.desc())
    return users


def update_guild(castle, guild, where=None, date=None):
    guild = Guilds.insert(castle=castle, name=guild, where=where, last_seen=date).on_conflict(
        conflict_target=(Guilds.name),
        preserve=(Guilds.name),
        update={'castle': castle, 'where': where, 'last_seen': date}).execute()


def get_guilds(castle):
    guilds = Guilds.select().where(Guilds.castle == castle).order_by(Guilds.last_seen.desc())
    return guilds


def find_report(chat_id, date, nickname=None, admin=False):
    if admin:
        if not nickname:
            reports = Report.select().where(Report.date == date).order_by(Report.nickname)
        else:
            reports = Report.select().where(Report.nickname == nickname).order_by(-Report.date)
        return reports
    elif chat_id:
        if not nickname:
            reports = Report.select().where(Report.chat_id == chat_id, Report.date == date).order_by(Report.nickname)
        else:
            reports = Report.select().where(Report.chat_id == chat_id, Report.nickname == nickname).order_by(-Report.date)
        return reports
    return None


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


def create_report(chat_id, nickname, text, date):
    try:
        report = Report.create(
            nickname=nickname, text=text, date=date, chat_id=chat_id)
    except IntegrityError:
        return False
    return report


def get_user_settings(chat_id):
    settings = UserSettings.get_or_none(telegram_id=chat_id)
    return settings


def update_settings(chat_id, value, type):
    user_settings = UserSettings.get_or_none(telegram_id=chat_id)
    if not user_settings:
        return False
    else:
        if type == 'sell_notification':
            user_settings.sell_notification = value
            user_settings.save()
        elif type == 'auto_spend_notification':
            user_settings.auto_spend_notification = value
            user_settings.save()


def create_sub_guild(guild_name, created_by):
    try:
        guild = GuildsGlory.create(name=guild_name, set_by=created_by)
    except IntegrityError:
        return False
    return guild


def delete_sub_guild(guild_name):
    guild = GuildsGlory.get_or_none(name=guild_name)
    if guild:
        guild.delete_instance()
        return True
    return False


def get_sub_guilds():
    guilds = GuildsGlory.select()
    return guilds


def update_guild_gp(castle, tag, glory):
    pass
