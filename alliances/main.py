import re
from datetime import datetime

import pytz
from alliances.utils import *
from core.config import TIMEZONE, bot_name
from core.texts import *


def find_spot(update, context):
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/spot', '').strip()
    if extra:
        spot = get_spot_by_name(extra)
        if spot:
            text = '{} {} {} `/ga_atk_{}`'.format(spot.name, spot.code, spot.spot_type, spot.code)
            context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')


def del_spot(update, context):
    chat_id = update.message.chat_id
    if update.message.reply_to_message:
        message = update.message.reply_to_message
        if message.to_dict().get('from', {}).get('username', None) == bot_name:
            text = message.to_dict().get('text')
            spot_code_reg = r'/ga_atk_(?P<code>.*)'
            spot = re.search(spot_code_reg, text)
            if spot:
                spot_code = spot.groupdict().get('code')
                spot_name_reg = r'(?P<name>[\w\d\s.]+) {} '.format(spot_code)
                spot = re.search(spot_name_reg, text)
                if spot:
                    spot_name = spot.groupdict().get('name')
                    delete_ali_spot(chat_id, spot_code)
                    deleted = del_spot_by_name(spot_name)
                    if deleted:
                        context.bot.send_message(
                            chat_id=chat_id, text='{} deleted'.format(spot_name), parse_mode='Markdown')


def a_guilds(update, context):
    extra = update.message.text.replace('/a_guilds', '').strip()
    chat_id = update.message.chat_id

    all_guilds = get_all_alliances(alliance=extra, type='guilds')
    temp_data = {}
    for guild in all_guilds:
        alli_name_code = guild.alliance + ' ' + '<code>' + guild.extra.code + '</code>'
        if not temp_data.get(alli_name_code):
            temp_data[alli_name_code] = []
        temp_data[alli_name_code].append('{} last_seen {}:00'.format(
            guild.name, guild.date.astimezone(pytz.timezone(TIMEZONE)).strftime("%d.%m %H")))

    text = ''
    for key, value in temp_data.items():
        text += '\n{}\n{}\n'.format(key, '\n'.join(value))

    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')


def a_spots(update, context):
    extra = update.message.text.replace('/a_spots', '').strip()
    chat_id = update.message.chat_id

    all_spots = get_all_alliances(alliance=extra, type='spots')
    temp_data = {}
    for spot in all_spots:
        alli_name_code = spot.alliance + ' ' + '`' + spot.extra.code + '`'
        if not temp_data.get(alli_name_code):
            temp_data[alli_name_code] = []

        activate = ''
        diff = datetime.utcnow() - spot.date
        days, seconds = diff.days, diff.seconds
        hours = days * 24 + seconds // 3600
        if hours < 8:
            activate = '🕡'

        if days > 7:
            delete_spot(spot.alliance, spot.name)
            continue

        if 'Mine' in spot.name:
            spot_type = '📦'
        elif 'Fort' in spot.name or 'Outpost' in spot.name or 'Tower' in spot.name:
            spot_type = '🎖'
        elif 'Ruins' in spot.name:
            spot_type = '✨'
        else:
            spot_type = '❔'
        temp_data[alli_name_code].append('{}{} captured {}:00 {}'.format(
            spot_type, spot.name, spot.date.astimezone(pytz.timezone(TIMEZONE)).strftime("%d.%m %H"), activate))

    text = ''
    for key, value in temp_data.items():
        text += '\n{}\n{}\n'.format(key, '\n'.join(value))

    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')


def list_ali_spots(update, context):
    chat_id = update.message.chat_id
    ali_spots = get_all_ali_spots(chat_id)
    text = ''
    if ali_spots:
        ali, res, mag, glo = [], [], [], []
        for spot in ali_spots:
            if spot.spot_type == 'Alliance':
                ali.append('<b>{}</b> <code>{}</code>'.format(spot.name, spot.code))
            elif spot.spot_type == 'Resources':
                res.append('<b>{}</b> <code>{}</code>'.format(spot.name, spot.code))
            elif spot.spot_type == 'Magic':
                mag.append('<b>{}</b> <code>{}</code>'.format(spot.name, spot.code))
            elif spot.spot_type == 'Glory':
                glo.append('<b>{}</b> <code>{}</code>'.format(spot.name, spot.code))
        if not any([ali, res, mag, glo]):
            context.bot.send_message(chat_id=chat_id, text=no_ali_text, parse_mode='html')
        else:
            text = all_ali_spot_text.format(
                '\n'.join(ali), '\n'.join(res), '\n'.join(glo), '\n'.join(mag))
            context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    else:
        context.bot.send_message(chat_id=chat_id, text=no_ali_text, parse_mode='html')


def del_ali_spot(update, context):
    chat_id = update.message.chat_id
    code_spot = update.message.text.replace('++delali ', '')
    deleted = delete_ali_spot(chat_id, code_spot)
    if deleted:
        context.bot.send_message(
            chat_id=chat_id,
            text=del_spot_text.format(code_spot))
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=del_none_spot_text.format(code_spot))
