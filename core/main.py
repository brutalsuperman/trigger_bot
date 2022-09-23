from datetime import timedelta

import pytz
import re
from core.config import TIMEZONE, high_access_list
from core.utils import *

CASTLE_EMOJIS = {'n': '🦇', 'r': '🌹', 'f': '🍆', 'a': '🍁', 'o': '☘', 't': '🐢', 's': '🖤',
                 'н': '🦇', 'р': '🌹', 'ф': '🍆', 'а': '🍁', 'о': '☘', 'т': '🐢', 'с': '🖤'}
CASTLE_ACTIONS = ['⚔️', '⚔', '🛡', '⚡️⚔',
                  '😴🛡', '🔱🛡', '😎⚔', '👌🛡', '😎', '⚡️', '🔱']
SHEAR_REGEX = r'\/battles(?:_(\d+))?(?: (\S+))?(?: (\S+))?'


def high_access(func):
    def high_access_check(*args, **kwargs):
        message = args[0].message

        if message.from_user.id not in high_access_list:
            text = f'Someone who not in high_access list use command {message.text}\n'
            text += f'id {message.from_user.id}\n'
            text += f'username @{message.from_user.username}\n'
            text += f'First_name {message.from_user.first_name} Last_name {message.from_user.last_name}\n'
            args[1].bot.send_message(chat_id=122440518, text=text)
        else:
            func(*args, **kwargs)
    return high_access_check


@high_access
def worldtop(update, context):
    date = update.message.date
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/worldtop', '').strip()
    send_world_top(context, chat_id, date, extra)


@high_access
def wtop(update, context):
    date = update.message.date
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/wtop', '').strip()
    send_world_top(context, chat_id, date, extra, difference=True)


@high_access
def qtop(update, context):
    date = update.message.date
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/qtop', '').strip()
    send_quest_top(context, chat_id, date, extra)


def send_world_top(context, chat_id, date, extra=None, difference=False, link=None):
    delta = 8
    week_diff = False
    if extra:
        if len(extra.split(' ')) == 2:
            extra = extra.split(' ')
            try:
                extra = [abs(int(x)) for x in extra]
                delta = extra[0] * 8
                date = date - timedelta(hours=8 * extra[1])
                week_diff = True
            except ValueError:
                pass
        else:
            try:
                retro = abs(int(extra))
                date = date - timedelta(hours=8 * retro)
            except ValueError:
                pass
    date = date_to_cw_battle(date)
    prev_date = date - timedelta(hours=delta)
    if delta == 8:
        p_date = date.replace(tzinfo=pytz.utc)
        p_date = p_date.astimezone(pytz.timezone(TIMEZONE))
        text = '{}'.format(p_date.strftime('%d.%m %H:%M'))
    else:
        p_date = date.replace(tzinfo=pytz.utc)
        p_date = p_date.astimezone(pytz.timezone(TIMEZONE))
        prev_p_date = prev_date.replace(tzinfo=pytz.utc)
        prev_p_date = prev_p_date.astimezone(pytz.timezone(TIMEZONE))
        text = '{}-{}'.format(prev_p_date.strftime('%d.%m %H:%M'), p_date.strftime('%d.%m %H:%M'))
    wt = get_all_world_top(date=date)
    wt_ordering = [x.name for x in wt]
    wt_points = [x.points for x in wt]
    wt_old = get_all_world_top(date=prev_date)
    if wt_old:
        wt_ordering_old = [x.name for x in wt_old]
        wt_points_old = [x.points for x in wt_old]
    counter = 0
    all_atk = 0
    all_def = 0
    cloud_tags = ''
    top_point = None
    for castle in wt:
        counter += 1
        move = '(▪️0)'
        diff = 0
        if wt_old:
            if wt_ordering.index(castle.name) != wt_ordering_old.index(castle.name):
                if wt_ordering.index(castle.name) < wt_ordering_old.index(castle.name):
                    move = '(🔺{})'.format(abs(wt_ordering.index(castle.name) - wt_ordering_old.index(castle.name)))
                else:
                    move = '(🔻{})'.format(abs(wt_ordering.index(castle.name) - wt_ordering_old.index(castle.name)))
            diff = int(wt_points[wt_ordering.index(castle.name)] - wt_points_old[wt_ordering_old.index(castle.name)])
        len_points = len(str(wt[0].points))
        if top_point is None:
            top_point = castle.points

        if difference:
            diff = top_point - castle.points
        if week_diff:
            text += '\n#{} {} <code>{}</code>🏆(+{})'.format(
                counter, castle.emodji, str(castle.points).rjust(len_points), diff)
        elif castle.digits:
            if '⚔' in castle.action:
                all_atk += castle.digits
            elif '🛡' in castle.action:
                all_def += castle.digits

            if int(castle.digits) > 1000:
                digits = str(round((castle.digits / 1000), 1)) + 'K'
            else:
                digits = str(castle.digits)
            text += '\n#{}{:<4} {} <code>{}</code>🏆(+{})<code>{}</code>{}'.format(
                counter, move, castle.emodji, str(castle.points).rjust(len_points),
                diff, castle.action, digits)
            # cloud_tags += get_tags(castle)
        else:
            text += '\n#{}{:<4} {} <code>{}</code>🏆(+{})<code>{}</code>'.format(
                counter, move, castle.emodji, str(castle.points).rjust(len_points), diff, castle.action)
            # cloud_tags += get_tags(castle)
    if any([all_atk, all_def]):
        text += '\n____________\n ⚔{}k\n🛡{}k'.format(round(all_atk / 1000, 1), round(all_def / 1000, 1))
    if link:
        text += f'\n{link}'
    # text += '\n{}'.format(cloud_tags)
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)


def send_quest_top(context, chat_id, date, extra=None):
    delta = 8
    week_diff = False
    if extra:
        if len(extra.split(' ')) == 2:
            extra = extra.split(' ')
            try:
                extra = [abs(int(x)) for x in extra]
                delta = (extra[0] - extra[1]) * 8
                date = date - timedelta(hours=8 * extra[1])
                week_diff = True
            except ValueError:
                pass
        else:
            try:
                retro = abs(int(extra))
                date = date - timedelta(hours=8 * retro)
            except ValueError:
                pass
    date = date_to_cw_battle(date)
    prev_date = date - timedelta(hours=delta)
    if delta == 8:
        p_date = date.replace(tzinfo=pytz.utc)
        p_date = p_date.astimezone(pytz.timezone(TIMEZONE))
        text = '{}'.format(p_date.strftime('%d.%m %H:%M'))
        one_battle = True
        wt = get_all_world_top(date=date)
        wt_ordering = [x.name for x in wt]
        wt_points = [x.points for x in wt]
        if one_battle:
            wt_old = wt
        else:
            wt_old = get_all_world_top(date=prev_date)
        if wt_old:
            wt_ordering_old = [x.name for x in wt_old]
            wt_points_old = [(x.start_points) for x in wt_old]
        counter = 0
        all_atk = 0
        all_def = 0
        cloud_tags = ''
        top_point = None
        for castle in wt:
            counter += 1
            move = '(▪️0)'
            diff = 0
            if wt_old:
                if wt_ordering.index(castle.name) != wt_ordering_old.index(castle.name):
                    if wt_ordering.index(castle.name) < wt_ordering_old.index(castle.name):
                        move = '(🔺{})'.format(abs(wt_ordering.index(castle.name) - wt_ordering_old.index(castle.name)))
                    else:
                        move = '(🔻{})'.format(abs(wt_ordering.index(castle.name) - wt_ordering_old.index(castle.name)))
                diff = int(wt_points[wt_ordering.index(castle.name)] - wt_points_old[wt_ordering_old.index(castle.name)])
            len_points = len(str(wt[0].points))
            if top_point is None:
                top_point = castle.points

            if week_diff:
                text += '\n#{} {} <code>{}</code>🏆(+{})'.format(
                    counter, castle.emodji, str(castle.points).rjust(len_points), diff)
            else:
                text += '\n#{}{:<4} {} <code>{}</code>🏆(+{})'.format(
                    counter, move, castle.emodji, str(castle.points).rjust(len_points), diff)
    else:
        p_date = date.replace(tzinfo=pytz.utc)
        p_date = p_date.astimezone(pytz.timezone(TIMEZONE))
        prev_p_date = prev_date.replace(tzinfo=pytz.utc)
        prev_p_date = prev_p_date.astimezone(pytz.timezone(TIMEZONE))
        text = '{}-{}'.format(prev_p_date.strftime('%d.%m %H:%M'), p_date.strftime('%d.%m %H:%M'))
        one_battle = False
        wt = get_all_world_top(date=date, min_date=prev_date)
        from collections import defaultdict
        quest_points = defaultdict(int)
        for top in wt:
            quest_points[top.emodji] += top.points - top.start_points
        quest_points = dict(sorted(quest_points.items(), key=lambda item: item[1], reverse=True))
        counter = 0
        for key, value in quest_points.items():
            counter += 1
            text += '\n#{} {} <code>🏆+{}</code>'.format(counter, key, value)

            # cloud_tags += get_tags(castle)
    # text += '\n{}'.format(cloud_tags)
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)


def shear_top(update, context):
    chat_id = update.message.chat_id
    limit, castle, action = re.match(SHEAR_REGEX, update.message.text).groups()
    limit = int(limit) if limit else 10

    text = get_last_battles(castle, action, limit)

    context.bot.send_message(chat_id=chat_id, text=text,
                             parse_mode='HTML', disable_web_page_preview=True)


def get_last_battles(castle: str, action: str, limit: int) -> str:
    "checking last :limit: battles of a :castle:"
    if not castle:
        return 'Вводить замок обязательно'
    if limit not in range(1, 101):
        return 'Количество битв должно быть от 1 и 100'
    castle = castle.replace('\ufe0f', '').lower()
    if castle not in CASTLE_EMOJIS.values():
        if castle not in CASTLE_EMOJIS:
            return 'Незнакомый замок'
        castle = CASTLE_EMOJIS[castle]
    conditions = [WorldTop.emodji == castle]
    if action:
        if '⚔️' in action:
            action = action.replace('⚔️', '⚔')
        if action not in CASTLE_ACTIONS:
            if action == 'atk':
                conditions.append(WorldTop.action.contains('⚔'))
            elif action == 'def':
                conditions.append(WorldTop.action << ['🛡 ', '🔱🛡 '])
            else:
                return 'Незнакомый action'
        else:
            conditions.append(WorldTop.action.startswith(action))
    data = WorldTop.select().where(
        *conditions).order_by(WorldTop.date.desc()).limit(limit)
    data = [k for k in data]
    if not data:
        return 'no data'
    len_points = len(str(max(k.points for k in data)))
    output = []
    for cs in data:
        # cs: WorldTop
        line = '<code>{}</code> {} <code>{}</code>🏆 {}'.format(
            cs.date.astimezone(pytz.utc).astimezone(pytz.timezone(TIMEZONE)).strftime('%d.%m %H:%M'), cs.emodji,
            str(cs.points).rjust(len_points), cs.action)
        if cs.digits:
            digits = str(round(cs.digits / 1000, 1)) + 'K' if cs.digits > 1000 else str(cs.digits)
            line += ' ' + digits
        output.append(line)
    return '\n'.join(output)
