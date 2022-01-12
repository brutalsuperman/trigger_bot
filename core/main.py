from datetime import timedelta

import pytz
from core.config import TIMEZONE
from core.utils import *


def worldtop(update, context):
    date = update.message.date
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/worldtop', '').strip()
    send_world_top(context, chat_id, date, extra)


def wtop(update, context):
    date = update.message.date
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/wtop', '').strip()
    send_world_top(context, chat_id, date, extra, difference=True)


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