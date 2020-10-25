import json
import logging
import random
import re
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import cw_api
import pytz
from config import TIMEZONE, TOKEN, api_login
from peewee import *
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      InlineQueryResultArticle, InputTextMessageContent)
from telegram.ext import (CallbackQueryHandler, ChosenInlineResultHandler,
                          CommandHandler, Filters, InlineQueryHandler,
                          MessageHandler, Updater)
from texts import *
from utils import *

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


def admin_decorator(func):
    def inner(*args, **kwargs):
        user = args[1].bot.get_chat_member(
            args[0].message.chat_id,
            args[0].message.from_user.id)
        if user.status not in ['creator', 'administrator']:
            args[1].bot.send_message(
                chat_id=args[0].message.chat_id,
                text=not_admin_text)
            return
        func(*args, **kwargs)
    return inner


def start(update, context):
    """Send a message when the command /start is issued."""
    help(update, context)


@admin_decorator
def add_trigger(update, context, edit=None):
    trigger = update.message.text.replace('++add ', '') if not edit else update.message.text.replace('++edit ', '')
    chat_id = update.message.chat_id
    value = None

    if update.message.reply_to_message:
        if update.message.reply_to_message.text:
            trigger_type = 'text'
            value = update.message.reply_to_message.text
        elif update.message.reply_to_message.sticker:
            trigger_type = 'sticker'
            value = update.message.reply_to_message.sticker.file_id
        elif update.message.reply_to_message.photo:
            trigger_type = 'photo'
            value = [x.file_id for x in update.message.reply_to_message.photo]
            value = value[0]  # ??????
        elif update.message.reply_to_message.animation:
            trigger_type = 'animation'
            value = update.message.reply_to_message.animation.file_id
        elif update.message.reply_to_message.video_note:
            trigger_type = 'video_note'
            value = update.message.reply_to_message.video_note.file_id
        elif update.message.reply_to_message.video:
            trigger_type = 'video'
            value = update.message.reply_to_message.video.file_id
        elif update.message.reply_to_message.voice:
            trigger_type = 'voice'
            value = update.message.reply_to_message.voice.file_id
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text='Что это вообще???')
        if value and not edit:
            saved = save_trigger(chat_id, trigger, trigger_type, value)
            if saved:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=new_trigger_text.format(trigger, trigger, trigger))
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=not_uniq_text)
        elif value and edit:
            edited = update_trigger(chat_id, trigger, trigger_type, value)
            if edited:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=edit_trigger_text.format(trigger, trigger, trigger))
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=edit_none_text)
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=add_on_replay_text)


def list_triggers(update, context):
    chat_id = update.message.chat_id
    all_triggers = get_all_triggers(chat_id)
    text = ''
    if all_triggers:
        for trigger in all_triggers:
            text += '📣 {} [{}] \n'.format(trigger.trigger_name, trigger.trigger_type)
    context.bot.send_message(
        chat_id=chat_id,
        text=list_trigger_text.format(text))


@admin_decorator
def del_trigger(update, context):
    chat_id = update.message.chat_id
    trigger = update.message.text.replace('++del ', '')
    deleted = delete_trigger(chat_id, trigger)
    if deleted:
        context.bot.send_message(
            chat_id=chat_id,
            text=del_trigger_text.format(trigger))
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=del_none_text.format(trigger))


def trigger_me(update, context):
    svodki_channel = -1001401627995  # -1001486183416
    order_of_grey_wolf = -1001168950089  # -394357133

    if update.message.forward_from and update.message.forward_from.id == 265204902:
        if re.search(r'Code \d+ to authorize {}'.format(api_login), update.message.text):
            user_id = update.message.from_user.id
            code = re.search(r'Code (\d+) to authorize {}'.format(api_login), update.message.text).groups()[0]
            process_code(user_id, code)

    if update.channel_post and update.channel_post.chat.id == svodki_channel:
        report = update._effective_message.text
        if not context.chat_data.get('top', False):
            context.chat_data['top'] = []

        top = []  # 🦇🐺[OGW]Альрия
        guilds = ['OGW', 'SIF', 'STG']
        for guild in guilds:
            best = []
            best = re.findall(r'\[{}\]([\w\d\s\-\_]+)[ |,|\n]'.format(guild), report)
            if best:
                top += best
        if top:
            context.chat_data['top'] += top

        if 'По итогам сражений замкам начислено' in report:
            if context.chat_data.get('top', []):
                text = 'Вот они наши звёзды {}'.format(', '.join(context.chat_data.get('top', [])))
                context.bot.send_message(chat_id=order_of_grey_wolf, text=text, parse_mode='html')
            else:
                text = 'Увы, никто не попал в топ'
                context.bot.send_message(chat_id=order_of_grey_wolf, text=text, parse_mode='html')
            context.chat_data['top'] = []
            context.chat_data['users'] = []
        return

    if update.edited_message:
        return
    chat_id = update.message.chat_id
    trigger_name = update.message.text
    trigger = find_trigger(chat_id, trigger_name)
    if trigger:
        send_trigger(context, chat_id, trigger)

    # alliance
    if update.message.forward_from and update.message.forward_from.id == 265204902:
        reg_name = r'You found hidden location ([\w\s\d]+.\d\d)'
        reg_code = r'То remember the route you associated it with simple combination: ([\w\d]+)'
        reg_alli = r'You found hidden headquarter (\w+\s+\w+)'
        name = re.search(reg_name, update.message.text)
        code = None
        spot_type = None
        if not name:
            name = re.search(reg_alli, update.message.text)
        if name:
            name = name.group(1)
            code = re.search(reg_code, update.message.text)
            if code:
                code = code.group(1)
        if 'headquarter' in update.message.text:
            spot_type = 'Alliance'
        elif 'Mine' in update.message.text:
            spot_type = 'Resources'
        elif 'Fort' in update.message.text or 'Outpost' in update.message.text or 'Tower' in update.message.text:
            spot_type = 'Glory'
        elif 'Ruins' in update.message.text:
            spot_type = 'Magic'

        if all([name, code, spot_type]):
            new_spot = create_spot(name, code, spot_type, chat_id)
            if new_spot:
                context.bot.send_message(chat_id=chat_id, text=new_spot_text, parse_mode='html')
            else:
                context.bot.send_message(chat_id=chat_id, text=old_spot_text, parse_mode='html')

    # - gold
    if update.message.forward_from and update.message.forward_from.id == 265204902:
        reg_gold = r'💰Gold: -(\d+)'
        if 'Твои результаты в бою:' in update.message.text:
            gold = re.search(reg_gold, update.message.text)
            if gold:
                gold = int(gold.group(1))
                texts = []
                if gold >= 1:
                    texts.append('Ой, всё, отдал деньги врагу, несите Маше валерьянку!')
                    texts.append('Я тебя записал! Пока только карандашом')
                    texts.append('Помощь пришла, откуда не ждали')
                    texts.append('Опять ножик лагал? Давай оправдывай себя, лентяй.')
                if gold > 2:
                    texts.append('А мог бы купить травы. Совсем себя не бережешь')
                    texts.append('Не слитая голда? Чо там у нас дальше по гештальтам')
                if gold > 10:
                    texts.append('Резко уходи в закат')
                if gold > 15:
                    texts.append('Гуляйте на все, чо! Отряд OGW может себе это позволить!')

                # text = 'Атата. Ты знаешь сколько всего можно было купить на {}'.format(gold)
                context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')
        if 'Твои результаты в бою:' in update.message.text and ('🏅Enraged' in update.message.text or '🏅Peacekeeping' in update.message.text):
            text = 'Ого, грац с медалькой'
            context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')

    # корован
    if update.message.forward_from and update.message.forward_from.id == 265204902:
        if 'Он пытается ограбить КОРОВАН' in update.message.text:
            context.bot.send_message(chat_id=chat_id, text='/go', parse_mode='html')
        elif 'Ты задержал ' in update.message.text:
            texts = [
                'молодец, волчара, так держать',
                'хорош, теперь отгрызи ему голову',
                'мы в тебе не сомневались']
            context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')
        elif 'Ты пытался остановить' in update.message.text:
            texts = [
                'не расстраивайся, мы его еще догоним',
                'ну 10 гп, это 10 гп',
                'тренируйся дальше, он ещё не раз вернется']
            context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')

    # reports
    if update.message.forward_from and update.message.forward_from.id == 265204902:
        if 'Твои результаты в бою:' in update.message.text and 'Встреча' not in update.message.text:
            date = update.message.forward_date
            if date.hour >= 6 and date.hour < 14:
                date = date.replace(hour=6, minute=0, second=0)
            elif date.hour >= 14 and date.hour < 22:
                date = date.replace(hour=14, minute=0, second=0)
            else:
                if date.hour >= 22:
                    date = date.replace(hour=22, minute=0, second=0)
                elif date.hour < 6:
                    date = date.replace(day=date.day - 1, hour=22, minute=0, second=0)
            reg_nick = r'🦇.\[\w+\]([\w\s_-]+)⚔|🦇([\w\s_-]+)⚔|🦇\[\w+\]([\w\s_-]+)⚔'
            nickname = re.match(reg_nick, update.message.text)
            if any(nickname.groups()):
                nickname = [x.strip() for x in nickname.groups() if x is not None][0]
            new_report = create_report(chat_id, nickname, update.message.text, date)
            if not new_report:
                context.bot.send_message(chat_id=chat_id, text=old_report_text, parse_mode='html')


def send_button(context, chat_id):
    if context.chat_data:
        context.chat_data['users'] = set()
        context.chat_data['usernames'] = set()
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Готов!', callback_data='тык')]])
    context.bot.send_message(
        chat_id=chat_id,
        text=button_text,
        reply_markup=reply_markup)


def inline_button(update, context):
    who = update.callback_query.to_dict().get('from', {}).get('id')
    if not context.chat_data.get('users', []):
        context.chat_data['users'] = set()
        context.chat_data['usernames'] = set()
    clicked = len(context.chat_data.get('users', []))
    context.chat_data['users'].add(who)
    if update.callback_query.to_dict().get('from', {}).get('username'):
        name = update.callback_query.to_dict().get('from', {}).get('username', None)
    else:
        name = '{} {}'.format(
            update.callback_query.to_dict().get('from', {}).get('first_name', None),
            update.callback_query.to_dict().get('from', {}).get('last_name', None))
    context.chat_data['usernames'].add(name)
    if (datetime.utcnow().replace(tzinfo=timezone.utc) - update.callback_query.message.date).seconds > 1200:
        context.bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            show_alert=True,
            text='Уже не актуально')
        update.callback_query.edit_message_text(
            text=button_text + "\n\nВолков в стае {}".format(len(context.chat_data.get('users', 0))))
        context.chat_data['users'] = set()
    else:
        if len(context.chat_data.get('users', [])) == clicked:
            texts = ['Ты уже тыкал', 'Будешь много тыкать сломаешь', 'Я записал, записал', 'Лучше разбуди Стёпу', 'БЕСИШЬ!', 'Репорт сдал?']
            if who == 597266304:
                texts.append('С тебя нюдес.')
                texts.append('А ты плохая девочка, отшлёпаю.')
            elif who == 252167939:
                texts.append('Доктора потыкай')
                texts.append('Мам, ну хватит.')
            context.bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                show_alert=True,
                text=random.choice(texts))
        else:
            texts = [
                'Молодец, теперь можно и банок выпить', 'Проверь не сломан ли шмот',
                'Голду слил?', 'Сток сдал? Вдруг в нас вышли?', 'Лучший']
            if who in [597266304, 252167939, 186909576, 312082400, 622090635, 40660570, 240737677, 199077972]:  # katya, ra, rick, loli, did, bosmer, jazz, bazarov
                texts.append('А стрелы есть??')
            elif who == 384808946:  # gera
                texts.append('Ну, можно и курей покормить')
            elif who == 217906579:  # wilhelm
                texts.append('Когда ап?')
            elif who == 431456872:  # ruda
                texts.append('Предсказание: ты найдешь тот рецепт.')
            context.bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                show_alert=True,
                text=random.choice(texts))
            update.callback_query.edit_message_text(
                text=button_text + "\n\nВолков в стае {} \n\n{}".format(
                    len(context.chat_data.get('users', 0)),
                    ', '.join(context.chat_data['usernames'])),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text='Готов!', callback_data='тык')]]))


def send_trigger(context, chat_id, trigger):
    if trigger.trigger_type == 'text':
        context.bot.send_message(chat_id=chat_id, text=trigger.trigger_value, parse_mode='html')
    elif trigger.trigger_type == 'sticker':
        context.bot.send_sticker(chat_id=chat_id, sticker=trigger.trigger_value)
    elif trigger.trigger_type == 'photo':
        context.bot.send_photo(chat_id=chat_id, photo=trigger.trigger_value)
    elif trigger.trigger_type == 'animation':
        context.bot.send_animation(chat_id=chat_id, animation=trigger.trigger_value)
    elif trigger.trigger_type == 'video_note':
        context.bot.send_video_note(chat_id=chat_id, video_note=trigger.trigger_value)
    elif trigger.trigger_type == 'video':
        context.bot.send_video(chat_id=chat_id, video=trigger.trigger_value)
    elif trigger.trigger_type == 'voice':
        context.bot.send_voice(chat_id=chat_id, voice=trigger.trigger_value)


@admin_decorator
def edit_trigger(update, context):
    add_trigger(update, context, edit=True)


def send_time_trigger(context):
    utcmoment_naive = datetime.utcnow()
    utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)
    date = utcmoment.astimezone(pytz.timezone(TIMEZONE))
    if date.hour < 10:
        hour = '0' + str(date.hour)
    else:
        hour = date.hour
    if date.minute < 10:
        minute = '0' + str(date.minute)
    else:
        minute = date.minute
    time = '{}:{}'.format(hour, minute)
    triggers = get_time_triggers(time)
    if triggers:
        for trigger in triggers:
            if trigger.trigger_value == 'button':
                send_button(context, trigger.chat_id)
            else:
                send_trigger(context, trigger.chat_id, trigger)


@admin_decorator
def add_time_trigger(update, context):
    chat_id = update.message.chat_id
    time = update.message.text.replace('++time ', '')
    if not len(time.split(':')) == 2:
        context.bot.send_message(
            chat_id=chat_id,
            text=bad_time_format_text)
        return
    if update.message.reply_to_message:
        if update.message.reply_to_message.text:
            trigger_type = 'text'
            value = update.message.reply_to_message.text
        elif update.message.reply_to_message.sticker:
            trigger_type = 'sticker'
            value = update.message.reply_to_message.sticker.file_id
        elif update.message.reply_to_message.photo:
            trigger_type = 'photo'
            value = [x.file_id for x in update.message.reply_to_message.photo]
            value = value[0]  # ??????
        elif update.message.reply_to_message.animation:
            trigger_type = 'animation'
            value = update.message.reply_to_message.animation.file_id
        elif update.message.reply_to_message.video_note:
            trigger_type = 'video_note'
            value = update.message.reply_to_message.video_note.file_id
        elif update.message.reply_to_message.video:
            trigger_type = 'video'
            value = update.message.reply_to_message.video.file_id
        elif update.message.reply_to_message.voice:
            trigger_type = 'voice'
            value = update.message.reply_to_message.voice.file_id
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text='Что это вообще???')
        if value:
            saved = save_time_trigger(chat_id, time, trigger_type, value)
            if saved:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=new_time_trigger_text.format(time))

                hours = int(time.split(':')[0])
                minutes = int(time.split(':')[1])

                utcmoment_naive = datetime.utcnow()
                utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)
                now = utcmoment.astimezone(pytz.timezone(TIMEZONE))

                trigger_time = now.replace(hour=hours, minute=minutes, second=0)
                first = (trigger_time - now).seconds
                job.run_repeating(send_time_trigger, interval=86400, first=first)
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=not_uniq_text)
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=add_on_replay_text)


@admin_decorator
def del_time_trigger(update, context):
    chat_id = update.message.chat_id
    time = update.message.text.replace('++deltime ', '')
    if not len(time.split(':')) == 2:
        context.bot.send_message(
            chat_id=chat_id,
            text=bad_time_format_text)
        return
    deleted = delete_time_trigger(chat_id, time)
    if deleted:
        context.bot.send_message(
            chat_id=chat_id,
            text=del_trigger_text.format(time))
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=del_none_text.format(time))


def list_time_triggers(update, context):
    chat_id = update.message.chat_id
    all_triggers = get_all_time_triggers(chat_id)
    text = ''
    if all_triggers:
        for trigger in all_triggers:
            text += '📣 {} [{}] \n'.format(trigger.time, 'time')
    context.bot.send_message(
        chat_id=chat_id,
        text=list_trigger_text.format(text))


def help(update, context):
    chat_id = update.message.chat_id
    context.bot.send_message(
        chat_id=chat_id,
        text=help_text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


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


def reports(update, context):
    date = update.message.date
    chat_id = update.message.chat_id
    guild, nickname, retro = None, None, None
    extra = update.message.text.replace('/reports', '').strip()
    if extra:
        try:
            retro = abs(int(extra))
            date = date - timedelta(hours=8 * retro)
        except ValueError:
            pass
        if '[' in extra and ']' in extra:
            guild = extra
        else:
            nickname = extra
    if date.hour >= 6 and date.hour < 14:
        date = date.replace(hour=6, minute=0, second=0)
    elif date.hour >= 14 and date.hour < 22:
        date = date.replace(hour=14, minute=0, second=0)
    else:
        if date.hour >= 22:
            date = date.replace(hour=22, minute=0, second=0)
        elif date.hour < 6:
            date = date.replace(day=date.day - 1, hour=22, minute=0, second=0)
    prev_date = date - timedelta(hours=8)
    reports = find_report(chat_id, date)
    prev_reports = find_report(chat_id, prev_date)
    if guild:
        prev_reports = [x for x in prev_reports if guild in x.text]
    prev_nicks = [x.nickname for x in prev_reports]
    date = date.astimezone(pytz.timezone(TIMEZONE))
    text = 'Битва за ' + date.strftime('%H:%M %d.%m.%Y')
    exp, gold, stock, hp, atk = 0, 0, 0, 0, 0
    if reports:
        text += '\nРепорты сдали: \n'

        for report in reports:
            if report.nickname in prev_nicks:
                prev_nicks.remove(report.nickname)

            if guild:
                if guild not in report.text:
                    continue

            if '🏅' in report.text:
                text += '🏅' + report.nickname + '\n'
            elif '🔥Exp' not in report.text:
                text += '🚧' + report.nickname + '\n'
            else:
                text += report.nickname + '\n'
            re_exp = r'🔥Exp: ([-\d]+)'
            re_gold = r'💰Gold: ([-\d]+)'
            re_stock = r'📦Stock: ([-\d]+)'
            re_hp = r'❤️Hp: ([-\d]+)'
            re_atk = r'⚔:(\d+) 🛡|⚔:(\d+)\([+\-\d]+\)'

            if re.search(re_exp, report.text):
                exp += int(re.search(re_exp, report.text).groups()[0])
            if re.search(re_gold, report.text):
                gold += int(re.search(re_gold, report.text).groups()[0])
            if re.search(re_stock, report.text):
                stock += int(re.search(re_stock, report.text).groups()[0])
            if re.search(re_hp, report.text):
                hp += int(re.search(re_hp, report.text).groups()[0])
            if re.search(re_atk, report.text):
                atk += int(
                    [x.strip() for x in re.search(re_atk, report.text).groups() if x is not None][0])

    else:
        text += '\nРепортов нет'
    text += '\n ⚔{} 🔥{} 💰{} 📦{} ❤️{}'.format(atk, exp, gold, stock, hp)
    context.bot.send_message(chat_id=chat_id, text=text)
    if prev_nicks:
        text = 'Судя по прошлой битве репорты еще не сдали {}'.format(', '.join(prev_nicks))
        context.bot.send_message(chat_id=chat_id, text=text)


def me(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.request_action(token=token.token, action='requestProfile')


def auth(update, context):
    user_id = update.message.from_user.id
    cw_api.createAuthCode(user_id)


def wtb(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='TradeTerminal')


def profile(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='GetUserProfile')


def process_code(user_id, code):
    request = find_request(user_id)
    if request:
        if request.action == 'createAuthCode':
            cw_api.grantToken(user_id, code)
        elif request.action == 'authAdditionalOperation':
            token = find_token(user_id)
            cw_api.grantAdditionalOperation(token.token, request.req_id, code)


def auto_spend_gold(context):
    print(1)
    gr = get_all_rules()
    for rule in gr:
        print(rule.chat_id)
        spend_gold(rule.chat_id, rule, context)


def spend_my_gold(update, context):
    chat_id = update.message.from_user.id
    rule = get_my_rules(chat_id)
    spend_gold(chat_id, rule, context)


def spend_gold(chat_id, rule, context):
    if not rule:
        context.bot.send_message(chat_id, text=no_rules_text)
    delete_log(rule.chat_id, None)
    token = find_token(rule.chat_id)
    cw_api.request_action(token.token, action='requestProfile')
    time.sleep(3)
    user = get_user_data(rule.chat_id, type='requestProfile')
    if user:
        data = json.loads(user.data)
        user_gold = data.get('gold', 0)
        rules = [x.split(' ') for x in rule.rules.split('\n')]
        tmp_range = 2
        while user_gold > 0 and len(rules):
            date = datetime.now() - timedelta(hours=1)
            log = get_wtb_log(rule.chat_id, date)
            if not log:
                r = rules[0]
                price = int(r[1]) - tmp_range
                if price <= 0:
                    tmp_range -= 1
                    continue
                quantity = user_gold // price
                if quantity > 0:
                    create_wtb(rule.chat_id, quantity, price, item=r[0])
                    cw_api.wantToBuy(token.token, item_code=r[0], quantity=quantity, price=price)
                else:
                    rules.pop(0)
            if log:
                if log.status == 'Ok':
                    user_gold -= log.quantity * log.price
                    if not context.user_data.get('m_id', False):
                        message = context.bot.send_message(
                            rule.chat_id,
                            text='Купил {}x{} по {}'.format(log.item, log.quantity, log.price))
                        context.user_data['m_id'] = message.message_id
                        context.user_data['m_text'] = message.text

                    else:
                        text = context.user_data.get('m_text', False)
                        text += '\nКупил {}x{} по {}'.format(log.item, log.quantity, log.price)
                        context.bot.edit_message_text(
                            chat_id=rule.chat_id,
                            message_id=context.user_data.get('m_id', False),
                            text=text)
                    rules.pop(0)
                    delete_log(chat_id=rule.chat_id, status='Ok')
                elif log.status == 'NoOffersFoundByPrice':
                    if tmp_range > 0:
                        tmp_range -= 1
                    else:
                        rules.pop(0)
                    delete_log(chat_id=rule.chat_id, status='NoOffersFoundByPrice')
                elif log.status == 'BattleIsNear':
                    delete_log(chat_id=rule.chat_id, status='BattleIsNear')
                    break
                else:
                    time.sleep(1)
        context.user_data['m_id'] = False
        context.user_data['m_text'] = False
        context.bot.send_message(chat_id=rule.chat_id, text='Слив окончен')


def gold_rules(update, context):
    user_id = update.message.from_user.id
    text = update.message.text
    if not re.search(r'/gs[\n\s]+', text) or len(text.split('\n')) <= 1:
        print(text)
        context.bot.send_message(chat_id=user_id, text=gold_rules_bad_format_text)
    else:
        rules = '\n'.join([x for x in text.split('\n') if re.search(r'\d+ \d+', x)])
        create_rules(user_id, rules)
        context.bot.send_message(chat_id=user_id, text=gold_rules_save_text)


def stock(update, context):
    chat_id = update.message.from_user.id
    token = find_token(chat_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.request_action(token.token, action='requestStock')


def auth_stock(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='GetStock')


def inlinequery(update, context):
    query = update.inline_query.query
    user_id = update.inline_query.from_user.id
    stock = get_stock(chat_id=user_id, type='requestStock')
    stock = json.loads(stock.data)
    results = []
    for key, value in stock.items():
        if query != 'b':
            results.append(
                InlineQueryResultArticle(
                    id=key,
                    title='{} x {}'.format(value.get('name'), value.get('value')),
                    input_message_content=InputTextMessageContent('/g_deposit {} {}'.format(
                        key, value.get('value')))))
        else:
            results.append(
                InlineQueryResultArticle(
                    id=key,
                    title='{} x {}'.format(value.get('name'), value.get('value')),
                    input_message_content=InputTextMessageContent('/wts_{}_{}_2500'.format(
                        key, value.get('value')))))
    results = results[:50]
    if not len(results):
        results.append(InlineQueryResultArticle(
            id=uuid4(),
            title='No item for deposit',
            input_message_content=InputTextMessageContent('shrug')))

    update.inline_query.answer(results, cache_time=1)


def on_result_chosen(update, context):
    user_id = update.chosen_inline_result.from_user.id
    choosen = update.chosen_inline_result.result_id
    stock = get_stock(chat_id=user_id, type='requestStock')
    stock = json.loads(stock.data)
    del stock[choosen]

    create_user_data(user_id, type='requestStock', data=json.dumps(stock))


def main():

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("reports", reports))
    dp.add_handler(CommandHandler("me", me))
    dp.add_handler(CommandHandler("auth", auth))
    dp.add_handler(CommandHandler("wtb", wtb))
    dp.add_handler(CommandHandler("profile", profile))
    dp.add_handler(CommandHandler("gs", gold_rules))
    dp.add_handler(CommandHandler("spend", spend_my_gold))
    dp.add_handler(CommandHandler("stock", stock))
    dp.add_handler(CommandHandler("auth_stock", auth_stock))

    dp.add_handler(InlineQueryHandler(inlinequery))
    dp.add_handler(ChosenInlineResultHandler(on_result_chosen))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+time \d\d:\d\d'), add_time_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+deltime \d\d:\d\d'), del_time_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+listtime'), list_time_triggers))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+add [\s\w\/\d]+'), add_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+edit [\s\w\/\d]+'), edit_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+del [\s\w\/\d]+'), del_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+list'), list_triggers))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+help'), help))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+ali'), list_ali_spots))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+delali [\s\w\/\d]+'), del_ali_spot))
    dp.add_handler(MessageHandler(Filters.text, trigger_me))
    dp.add_handler(CallbackQueryHandler(inline_button))

    # log all errors
    dp.add_error_handler(error)

    # job.run_repeating(mailing_task, interval=300, first=0)
    # Start the Bot
    updater.start_polling()
    updater.idle()


def start_time_triggers():
    all_triggers = get_all_time_triggers()
    if all_triggers:
        for trigger in all_triggers:

            utcmoment_naive = datetime.utcnow()
            utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)
            now = utcmoment.astimezone(pytz.timezone(TIMEZONE))

            hours = int(trigger.time.split(':')[0])
            minutes = int(trigger.time.split(':')[1])
            trigger_time = now.replace(hour=hours, minute=minutes, second=0)
            first = (trigger_time - now).seconds
            job.run_repeating(send_time_trigger, interval=86400, first=first)

    # spend gold
    utcmoment_naive = datetime.utcnow()
    utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)
    now = utcmoment.astimezone(pytz.timezone(TIMEZONE))
    if now.hour > 9 and now.hour < 17:
        trigger_time = now.replace(hour=16, minute=45, second=0)
    elif now.hour > 1 and now.hour < 9:
        trigger_time = now.replace(hour=8, minute=45, second=0)
    else:
        trigger_time = now.replace(hour=0, minute=45, second=0)

    first = (trigger_time - now).seconds
    job.run_repeating(auto_spend_gold, interval=28800, first=first)


def init_db():
    db.connect()
    from models import Report, Token, Request, UserData, GoldRules, WtbLogs
    db.create_tables(
        [Trigger, TimeTrigger, Alliance, Report, Token, Request,
         UserData, GoldRules, WtbLogs], safe=True)
    db.close()


updater = Updater(TOKEN, use_context=True)
job = updater.job_queue
db = PostgresqlDatabase('ogwbot', user='ogw')


if __name__ == '__main__':
    init_db()
    start_time_triggers()
    main()
