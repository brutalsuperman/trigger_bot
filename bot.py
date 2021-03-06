import logging
from datetime import datetime

import pytz
from config import TIMEZONE, TOKEN
from peewee import *
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
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
    if update.edited_message:
        return
    chat_id = update.message.chat_id
    trigger_name = update.message.text
    trigger = find_trigger(chat_id, trigger_name)
    if trigger:
        send_trigger(context, chat_id, trigger)


def send_trigger(context, chat_id, trigger):
    if trigger.trigger_type == 'text':
        context.bot.send_message(chat_id=chat_id, text=trigger.trigger_value)
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
    time = '{}:{}'.format(date.hour, date.minute)
    triggers = get_time_triggers(time)
    if triggers:
        for trigger in triggers:
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


def main():

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+time \d\d:\d\d'), add_time_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+deltime \d\d:\d\d'), del_time_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+listtime'), list_time_triggers))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+add [\s\w\/\d]+'), add_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+edit [\s\w\/\d]+'), edit_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+del [\s\w\/\d]+'), del_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+list'), list_triggers))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex('\+\+help'), help))
    dp.add_handler(MessageHandler(Filters.text, trigger_me))

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


def init_db():
    db.connect()
    db.create_tables([Trigger, TimeTrigger], safe=True)
    db.close()


updater = Updater(TOKEN, use_context=True)
job = updater.job_queue
db = SqliteDatabase('sqlite.db')


if __name__ == '__main__':
    init_db()
    start_time_triggers()
    main()
