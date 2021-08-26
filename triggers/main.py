from datetime import datetime

import pytz
from bot import job
from core.config import TIMEZONE
from core.texts import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from triggers.utils import *
from users.main import *


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


def send_button(context, chat_id):
    if context.chat_data:
        context.chat_data['users'] = set()
        context.chat_data['usernames'] = set()
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Готов!', callback_data='тык')]])
    context.bot.send_message(
        chat_id=chat_id,
        text=button_text,
        reply_markup=reply_markup)


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
