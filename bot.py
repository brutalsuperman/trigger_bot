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
from keyboards import menu_markup

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING)

logger = logging.getLogger(__name__)
user_data = {}


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
    update.message.reply_text(text="Бот отряда OGW", reply_markup=menu_markup())


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
    svodki_channel = -1001486183416  # -1001401627995
    order_of_grey_wolf = -394357133   # -1001168950089
    if update.message:
        if update.message.forward_from and update.message.forward_from.id == 265204902:
            if re.search(r'Code \d+ to authorize {}'.format(api_login), update.message.text):
                user_id = update.message.from_user.id
                code = re.search(r'Code (\d+) to authorize {}'.format(api_login), update.message.text).groups()[0]
                process_code(user_id, code)
        elif update.message.text.startswith("💰"):
            gs(update, context)
        elif update.message.text.startswith("📦"):
            stock(update, context)

    if update.channel_post and update.channel_post.chat.id == svodki_channel:
        report = update._effective_message.text
        if '🤝Headquarters news:' in update._effective_message.text:
            text = update._effective_message.text
            alli_reg = r'\n(?P<alliance>[\w\s]+) was (.*\n){1,3}🎖Defense:(.*)'
            alli_def = re.findall(alli_reg, text)
            if alli_def:
                for alli in alli_def:
                    alliance = alli[0].strip()
                    guilds = re.findall(r'(?P<castle>☘️|🍆|🌹|🐢|🖤|🍁|🦇)(?P<guild>.?\[\w+\])', alli[-1])
                    if guilds:
                        guilds = [x[0] + x[1] for x in guilds]
                        for guild in guilds:
                            last_seen = update.channel_post.forward_date
                            create_alliances_spot(alliance, guild, last_seen, type='guilds')

        elif '🗺State of map:' in update._effective_message.text:
            text = update._effective_message.text
            alli_reg = r'(?:\n|$)(?P<spot_name>[\w\d\s.]+)belongs to (?P<alliance_name>.*)\.'
            alli_spot = re.findall(alli_reg, text)
            if alli_spot:
                for spot in alli_spot:
                    last_seen = update.channel_post.forward_date
                    create_alliances_spot(spot[1].strip(), spot[0].strip(), last_seen, type='spots')

        elif 'Результаты сражений:' in update._effective_message.text and 'По итогам сражений замкам начислено:' in update._effective_message.text:
            text = update._effective_message.text

            repl = r'По итогам сражений замкам начислено:([\d\D]+)'
            worldtop = re.findall(repl, text)
            if worldtop:

                reg_action = r'(?P<emoj>.*)(?:В битве у ворот |Защитники )(?P<castle>.)'
                reg_gold = r'(?:🏆Атакующие разграбили замок на |🏆У атакующих отобрали )(?P<gold>\d+) золотых монет'

                gold_map = {}
                for castle in text.split('\n\n'):
                    gold = 0
                    mobj = re.search(reg_action, castle)
                    if mobj:
                        extra_emo = ''
                        if 'скучали, на них никто не напал.' in castle:
                            extra_emo = '😴'
                        elif 'со значительным преимуществом' in castle:
                            extra_emo = '😎'
                        elif 'защитники легко отбились' in castle:
                            extra_emo = '👌'
                        elif 'разыгралась настоящая бойня' in castle:
                            extra_emo = '⚡️'
                        temp_castle = mobj['castle']
                        gold_map[temp_castle] = {'emoj': extra_emo + mobj['emoj']}
                        mobj = re.search(reg_gold, castle)
                        if mobj:
                            if mobj['gold']:
                                gold_map[temp_castle]['gold'] = mobj['gold']
                            else:
                                gold_map[temp_castle]['gold'] = 0

                reg = r'\n(.)([\D\s]+)\+(?P<points>\d+)'
                mobj = re.findall(reg, worldtop[0])
                if mobj:
                    date = date_to_cw_battle(update.channel_post.forward_date)
                    old_date = date - timedelta(hours=8)
                    for castle in mobj:
                        add_world_top(
                            emodji=castle[0], name=castle[1], points=castle[2], old_date=old_date,
                            date=date, action=gold_map[castle[0]].get('emoj'), gold=gold_map[castle[0]].get('gold'))
                    send_world_top(context, mid_id, date, extra=None)

        if not context.chat_data.get('top', False):
            context.chat_data['top'] = []
            context.chat_data['worst'] = []

        top = []  # 🦇🐺[OGW]Альрия
        top_worst = []
        guilds = ['OGW', 'SIF', 'STG']
        temp_worst = re.findall(r'🛡 В битве у ворот (☘️|🍆|🌹|🐢|🖤|🍁)(.*)\n🎖Лидеры атаки:(.*)\n🎖Лидеры защиты:', report)
        for guild in guilds:
            best = []
            worst = []

            if temp_worst:
                for castle in temp_worst:
                    if re.findall(r'\[{}]([\w\d\s\-\_]+)[ |,|\n]'.format(guild), castle[2]):
                        worst += (castle[0], re.findall(r'\[{}]([\w\d\s\-\_]+)[ |,|\n]'.format(guild), castle[2]))
            best = re.findall(r'\[{}]([\w\d\s\-\_]+)[ |,|\n]'.format(guild), report)
            if worst:
                top_worst.append(worst)
            if best:
                if top_worst:
                    for castle in top_worst:
                        for vtik in castle[1]:
                            if vtik in best:
                                best.remove(vtik)
                top += best
        if top or top_worst:
            context.chat_data['top'] += top
            context.chat_data['worst'] += top_worst

        if 'По итогам сражений замкам начислено' in report:
            text = ''
            if context.chat_data.get('top', []) or context.chat_data.get('worst', []):
                if context.chat_data.get('top', []):
                    text = '💪⭐️Вот они наши звёзды {}'.format(', '.join(context.chat_data.get('top', [])))
                if context.chat_data.get('worst', []):
                    text += '\n\n🙈😱Анти топ:\n'.format()
                    for hero in context.chat_data.get('worst', []):
                        hero[1] = ', '.join(hero[1])
                        if hero[0] == '🐢':
                            text += 'Как там говорят он на этом <s>собаку</s> черепаху съел, так вот это про {}'.format(hero[1])
                        elif hero[0] == '🌹':
                            text += '{} если ты хотел нарвать девочкам цветов, не обязательно было топтать всю клумбу'.format(hero[1])
                        elif hero[0] == '🍁':
                            text += '{} давно хотел оладушек с кленовым сиропом'.format(hero[1])
                        elif hero[0] == '🍆':
                            text += '{} эти баклажаны на закрутки?'.format(hero[1])
                        elif hero[0] == '🖤':
                            text += '{}, зачем тебе это чёрное сердечко, лучше вот тебе наше❤️'.format(hero[1])
                        elif hero[0] == '☘️' or hero[0] == '☘':
                            text += '{}, пока ты ищешь клевер с четырьмя лепестками, удача тихонько проходит мимо.'.format(hero[1])
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
            date = date_to_cw_battle(update.message.forward_date)
            reg_nick = r'🦇.\[\w+\]([\w\s_-]+)⚔|🦇([\w\s_-]+)⚔|🦇\[\w+\]([\w\s_-]+)⚔'
            nickname = re.match(reg_nick, update.message.text)
            if any(nickname.groups()):
                nickname = [x.strip() for x in nickname.groups() if x is not None][0]
            new_report = create_report(chat_id, nickname, update.message.text, date)
            if not new_report:
                context.bot.send_message(chat_id=chat_id, text=old_report_text, parse_mode='html')

    # update top
    if update.message.forward_from and update.message.forward_from.id == 265204902:
        castles = ['🐢Тортуга', '🌹Замок Рассвета', '🍁Амбер', '🦇Ночной Замок', '🖤Скала', 'очков']
        date = date_to_cw_battle(update.message.forward_date)

        if all([x in update.message.text for x in castles]):
            reg = r'#\s\d\s(?P<emodji>.)(?P<name>[\D\s]+)(?P<points>\d+)'
            mobj = re.findall(reg, update.message.text)
            if mobj:
                for obj in mobj:
                    update_world_top(emodji=obj[0], name=obj[1], points=obj[2], date=date)


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
    castles = ['🦇', '☘️', '🍁', '🍆', '🌹', '🖤', '🐢']
    if update.callback_query.data in castles:
        emodji = update.callback_query.data
        if emodji == '☘️':
            emodji = '☘'
        user_id = update._effective_user.id
        u_data = user_data[user_id]['calc']
        rep = get_castle_gold(emodji=emodji, date=u_data.get('date', None))
        if rep:
            if '🛡' in rep.action:
                action = '🛡'
                digits = int(int(u_data.get('def', 0)) / int(u_data.get('gold', 0)) * int(rep.gold))
            elif '⚔' in rep.action:
                action = '⚔'
                digits = int(int(u_data.get('atk', 0)) / int(u_data.get('gold', 0)) * int(rep.gold))

            if digits:
                rep.digits = digits
                rep.save()

                update.callback_query.edit_message_text(
                    text="{}{}{}".format(update.callback_query.data, action, digits))
        return

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
    re_exp = r'🔥Exp: ([-\d]+)'
    re_gold = r'💰Gold: ([-\d]+)'
    re_stock = r'📦Stock: ([-\d]+)'
    re_hp = r'❤️Hp: ([-\d]+)'
    re_atk = r'⚔:(\d+) 🛡|⚔:(\d+)\([+\-\d]+\)'
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
    if nickname:
        if update.message.from_user.id in [252167939, 122440518, 217906579, 467638790, 837889450]:
            reports = find_report(-1001168950089, date, nickname)
        else:
            reports = find_report(chat_id, date, nickname)
        text = ''
        if reports:
            text += 'Статистика репортов {}'.format(reports[0].nickname)
            prev_date = None
            for report in reports[:21]:
                exp, gold, stock, hp, atk = 0, 0, 0, 0, 0
                date = report.date  # 2020-10-18 06:00:00+00:00
                date = date + timedelta(hours=3)  # report.date + timedelta(hours=3)
                if prev_date:
                    while True:
                        diff = prev_date - date
                        days, seconds = diff.days, diff.seconds
                        hours = days * 24 + seconds // 3600
                        if hours > 8:
                            prev_date = prev_date - timedelta(hours=8)
                            text += '\n{}🚧'.format(prev_date.strftime('%H:%M %d.%m.%Y'))
                        else:
                            break
                prev_date = date
                if re.search(re_exp, report.text):
                    exp = int(re.search(re_exp, report.text).groups()[0])
                if re.search(re_gold, report.text):
                    gold = int(re.search(re_gold, report.text).groups()[0])
                if re.search(re_stock, report.text):
                    stock = int(re.search(re_stock, report.text).groups()[0])
                if re.search(re_hp, report.text):
                    hp = int(re.search(re_hp, report.text).groups()[0])
                if re.search(re_atk, report.text):
                    atk = int(
                        [x.strip() for x in re.search(re_atk, report.text).groups() if x is not None][0])
                text += '\n{} ⚔{} 🔥{} 💰{} 📦{} ❤️{}'.format(date.strftime('%H:%M %d.%m.%Y'), atk, exp, gold, stock, hp)
            context.bot.send_message(chat_id=chat_id, text=text)
        else:
            text += '\nРепортов нет'
            context.bot.send_message(chat_id=chat_id, text=text)

    else:
        date = date_to_cw_battle(date)
        prev_date = date - timedelta(hours=8)
        if update.message.from_user.id in [252167939, 122440518, 217906579, 467638790, 837889450]:
            reports = find_report(-1001168950089, date, nickname)
            prev_reports = find_report(-1001168950089, prev_date)
        else:
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


def auth_guild(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='GuildInfo')


def guild(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.request_action(token.token, action='guildInfo')


def glory_update(context):
    user_data = get_user_data(chat_id=None, type='guildInfo')
    for user in user_data:
        token = find_token(user.chat_id)
        cw_api.request_action(token.token, action='guildInfo')


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


from threading import Thread


class SpendThread(Thread):
    def __init__(self, chat_id, rule, context):
        Thread.__init__(self)
        self.chat_id = chat_id
        self.rule = rule
        self.context = context

    def run(self):
        spend_gold(self.chat_id, self.rule, self.context)


def auto_spend_gold(context):
    print('start auto spend')
    gr = get_all_rules()
    for rule in gr:
        thread = SpendThread(rule.chat_id, rule, context)
        thread.start()
        print('start for {}'.format(rule.chat_id))
    #     logger.warning('spending gold for {}'.format(rule.chat_id))
    #     try:
    #         spend_gold(rule.chat_id, rule, context)
    #     except:
    #         print('need start bot {}'.format(rule.chat_id))


def gs_enable(update, context):
    chat_id = update.message.from_user.id
    update_rules(chat_id, True)
    context.bot.send_message(chat_id, text=auto_enabled)
    pass


def gs_disable(update, context):
    chat_id = update.message.from_user.id
    logger.warning('spending gold for {}'.format(chat_id))
    update_rules(chat_id, False)
    context.bot.send_message(chat_id, text=auto_disable)
    pass


def spend_my_gold(update, context):
    chat_id = update.message.from_user.id
    rule = get_my_rules(chat_id)
    spend_gold(chat_id, rule, context)


def gs(update, context):
    chat_id = update.message.from_user.id
    rule = get_my_rules(chat_id)
    if rule:
        if rule.auto:
            a = '✅'
        else:
            a = '❌'

        text = '{} Автослив\n'.format(a)
        text += '\nПравила слива: \n{}\n\n'.format(rule.rules.replace('/gs ', ''))
        text += '/spend Слить сейчас\n'
        text += '/gs_enable Включить автослив\n'
        text += '/gs_disable Выключить автослив\n'
        context.bot.send_message(chat_id, text=text)
    else:
        token = find_token(chat_id)
        if not token:
            text = 'Надо пройти авторизацию /auth, мне нужен доступ к /wtb чтобы покупать и /profile чтобы знать сколько у тебя голды'
            context.bot.send_message(chat_id, text=text)
        else:
            context.bot.send_message(chat_id, text=no_rules_text)


def spend_gold(chat_id, rule, context):
    global user_data
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
                    if not user_data.get(rule.chat_id) or not user_data.get(rule.chat_id).get('m_id', False):
                        message = context.bot.send_message(
                            rule.chat_id,
                            text='Купил {}x{} по {}'.format(log.item, log.quantity, log.price),
                            disable_notification=True)
                        user_data[rule.chat_id] = {}
                        user_data[rule.chat_id]['m_id'] = message.message_id
                        user_data[rule.chat_id]['m_text'] = message.text

                    else:
                        text = user_data[rule.chat_id].get('m_text', '')
                        text += '\nКупил {}x{} по {}'.format(log.item, log.quantity, log.price)
                        context.bot.edit_message_text(
                            chat_id=rule.chat_id,
                            message_id=user_data[rule.chat_id].get('m_id', False),
                            text=text)
                    rules.pop(0)
                    delete_log(chat_id=rule.chat_id, status='Ok')
                elif log.status == 'NoOffersFoundByPrice':
                    if tmp_range > 0:
                        tmp_range -= 1
                    else:
                        rules.pop(0)
                    delete_log(chat_id=rule.chat_id, status='NoOffersFoundByPrice')
                # elif log.status == 'BattleIsNear':
                #     delete_log(chat_id=rule.chat_id, status='BattleIsNear')
                #     break
                elif log.status:
                    context.bot.send_message(
                        chat_id=rule.chat_id, text='Error: {}'.format(log.status), disable_notification=True)
                    delete_log(chat_id=rule.chat_id)
                    break
                else:
                    time.sleep(1)
        if user_data.get(rule.chat_id, False):
            user_data[rule.chat_id]['m_id'] = False
            user_data[rule.chat_id]['m_text'] = False
        context.bot.send_message(
            chat_id=rule.chat_id, text='Слив окончен, осталось {}'.format(user_gold), disable_notification=True)


def gold_rules(update, context):
    user_id = update.message.from_user.id
    text = update.message.text
    if not re.search(r'/gs[\n\s]+', text) or len(text.split('\n')) <= 1:
        context.bot.send_message(chat_id=user_id, text=gold_rules_bad_format_text)
    else:
        rules = '\n'.join([x.strip() for x in text.split('\n') if re.search(r'\d+ \d+', x)])
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
    global user_data
    query = update.inline_query.query
    user_id = update.inline_query.from_user.id
    if not user_data.get(user_id):
        user_data[user_id] = {}
        user_data[user_id]['stock'] = {}
    stock = get_stock(chat_id=user_id, type='requestStock')
    user_data[user_id]['stock'] = json.loads(stock.data)
    stock = user_data[user_id]['stock']
    results = []
    if query in ['-', '+']:
        if query == '-':
            stock = sorted(stock.items(), key=lambda x: x[1].get('value', 0))
        elif query == '+':
            stock = sorted(stock.items(), key=lambda x: x[1].get('value', 0), reverse=True)
        for key, value in stock:
            results.append(
                InlineQueryResultArticle(
                    id=key,
                    title='{} x {}'.format(value.get('name'), value.get('value')),
                    input_message_content=InputTextMessageContent('/g_deposit {} {}'.format(
                        key, value.get('value')))))
    else:
        for key, value in stock.items():
            if query != 'b':
                results.append(
                    InlineQueryResultArticle(
                        id=key,
                        title='{} x {}'.format(value.get('name'), value.get('value')),
                        input_message_content=InputTextMessageContent('/g_deposit {} {}'.format(
                            key, value.get('value')))))
            elif query == 'b':
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


def worldtop(update, context):
    date = update.message.date
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/worldtop', '').strip()
    send_world_top(context, chat_id, date, extra)


def send_world_top(context, chat_id, date, extra=None):
    retro = None
    if extra:
        try:
            retro = abs(int(extra))
            date = date - timedelta(hours=8 * retro)
        except ValueError:
            pass
    date = date_to_cw_battle(date)
    prev_date = date - timedelta(hours=8)
    wt = get_all_world_top(date=date)
    wt_ordering = [x.name for x in wt]
    wt_points = [x.points for x in wt]
    wt_old = get_all_world_top(date=prev_date)
    if wt_old:
        wt_ordering_old = [x.name for x in wt_old]
        wt_points_old = [x.points for x in wt_old]
    text = ''
    counter = 0
    all_atk = 0
    all_def = 0
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

        if castle.digits:
            if '⚔' in castle.action:
                all_atk += castle.digits
            elif '🛡' in castle.action:
                all_def += castle.digits

            if int(castle.digits) > 1000:
                digits = str(round((castle.digits / 1000), 1)) + 'K'
            else:
                digits = str(castle.digits)
            text += '\n#{}{:<4} {} `{}`🏆(+{})`{}`{}'.format(
                counter, move, castle.emodji, str(castle.points).rjust(len_points),
                diff, castle.action, digits)
        else:
            text += '\n#{}{:<4} {} `{}`🏆(+{})`{}`'.format(
                counter, move, castle.emodji, str(castle.points).rjust(len_points), diff, castle.action)
    if any([all_atk, all_def]):
        text += '\n____________\n ⚔{}k\n🛡{}k'.format(round(all_atk / 1000, 1), round(all_def / 1000, 1))
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')


def calculate_atak(update, context):
    global user_data
    message = update.message
    chat_id = update.message.chat_id
    if update.message.reply_to_message:
        message = update.message.reply_to_message
        if message.forward_from and message.forward_from.id == 265204902 and 'Твои результаты в бою:' in message.text:
            m_text = message.text
            m_date = date_to_cw_battle(message.forward_date)
            re_atk = r'⚔:(?P<atk>\d+).* 🛡:(?P<def>\d+)'
            re_gold = r'💰Gold: (?P<gold>[-\d]+)'

            e = re.search(re_atk, m_text)
            x = re.search(re_gold, m_text)
            if not user_data.get(update.message.from_user.id, False):
                user_data[update.message.from_user.id] = {}
            user_data[update.message.from_user.id]['calc'] = dict(e.groupdict(), **x.groupdict(), **{"date": m_date})
        else:
            date = date_to_cw_battle(message.date)
            reg = r'(?P<digit>\d+) (?P<gold>\d+)'
            find = re.search(reg, message.text)
            if find:
                temp_dict = find.groupdict()
                temp_dict['atk'] = temp_dict['def'] = temp_dict['digit']
                del temp_dict['digit']
                if not user_data.get(update.message.from_user.id, False):
                    user_data[update.message.from_user.id] = {}
                user_data[update.message.from_user.id]['calc'] = dict(temp_dict, **{"date": date})
            else:
                return

        castles = ['🦇', '☘️', '🍁', '🍆', '🌹', '🖤', '🐢']
        keyboard = []
        row = []
        for castle in castles:
            if len(row) > 3:
                keyboard.append(row)
                row = []

            row.append(InlineKeyboardButton(text=castle, callback_data=castle))
        keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        text = 'Для кого считаем?'
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup)
    else:
        text = 'Не вижу куда, сделай reply'
        context.bot.send_message(chat_id=chat_id, text=text)


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
    dp.add_handler(CommandHandler("gs_enable", gs_enable))
    dp.add_handler(CommandHandler("gs_disable", gs_disable))
    dp.add_handler(CommandHandler("auth_guild", auth_guild))
    dp.add_handler(CommandHandler("guild", guild))
    dp.add_handler(CommandHandler("a_guilds", a_guilds))
    dp.add_handler(CommandHandler("a_spots", a_spots))
    dp.add_handler(CommandHandler("worldtop", worldtop))
    dp.add_handler(CommandHandler("calc", calculate_atak))

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
    print('first will be in {} sec'.format(first))
    job.run_repeating(auto_spend_gold, interval=28800, first=first)

    job.run_repeating(glory_update, interval=360, first=0)


def init_db():
    db.connect()
    from models import Report, Token, Request, UserData, GoldRules, WtbLogs, Alliances, WorldTop
    db.create_tables(
        [Trigger, TimeTrigger, Spot, Report, Token, Request,
         UserData, GoldRules, WtbLogs, Alliances, WorldTop], safe=True)
    db.close()


updater = Updater(TOKEN, use_context=True)
job = updater.job_queue
db = PostgresqlDatabase('ogwbot', user='ogw', password='kalavera', autorollback=True)


if __name__ == '__main__':
    init_db()
    start_time_triggers()
    main()
