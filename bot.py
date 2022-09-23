import json
import logging
import random
import re
from datetime import datetime, timedelta, timezone
from datetime import date as datetimedate
from uuid import uuid4

from alliances.main import *
from core.base import db
from core.config import TOKEN, api_login, svodki_channel, main_svodki_channel, order_of_grey_wolf, mid_id, cwbot_id, castle_emoji, castle_full
from core.main import *
from core.texts import *
from keyboards import menu_markup
from mobu.main import *
from playhouse.postgres_ext import *
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      InlineQueryResultArticle, InputTextMessageContent)
from telegram.ext import (CallbackQueryHandler, ChosenInlineResultHandler,
                          CommandHandler, Filters, InlineQueryHandler,
                          MessageHandler, Updater)
from triggers.main import *
from users.main import *
from wordle.main import *

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
    if update.message.chat.type == 'private':

        """Send a message when the command /start is issued."""
        update.message.reply_text(text=hello_text, reply_markup=menu_markup())


def trigger_me(update, context):
    if update.message:
        if update.message.forward_from and update.message.forward_from.id == cwbot_id:
            if re.search(r'Code \d+ to authorize {}'.format(api_login), update.message.text):
                user_id = update.message.from_user.id
                code = re.search(r'Code (\d+) to authorize {}'.format(api_login), update.message.text).groups()[0]
                process_code(user_id, code)
        elif update.message.text.startswith("💰"):
            gs(update, context)
        elif update.message.text.startswith("📦"):
            stock(update, context)
        elif update.message.text.startswith("🔔"):
            user_settings(update, context)
    if update.channel_post and update.channel_post.chat.id == svodki_channel:

        update_guilds(update)
        link = ''
        report = update._effective_message.text
        if '🤝Headquarters news:' in update._effective_message.text:
            text = update._effective_message.text
            alli_reg = r'\n(?P<alliance>[\w\s]+) was (.*\n){1,3}🎖Defense:(.*)'
            alli_def = re.findall(alli_reg, text)
            if alli_def:
                for alli in alli_def:
                    alliance = alli[0].strip()
                    guilds = re.findall(r'(?P<castle>' + '|'.join(castle_emoji) + ')(?P<guild>.?\[\w+\])', alli[-1])
                    if guilds:
                        guilds = [x[0] + x[1] for x in guilds]
                        for guild in guilds:
                            last_seen = update.channel_post.forward_date
                            create_alliances_spot(alliance, guild, last_seen, type='guilds')

        elif '🗺State of map:' in update._effective_message.text:
            text = update._effective_message.text
            alli_reg = r'(?:\n|$)(?P<spot_name>[\w\d\s.]+)belongs to (?P<alliance_name>[\w\s]+).'
            alli_spot = re.findall(alli_reg, text)
            if alli_spot:
                for spot in alli_spot:
                    last_seen = update.channel_post.forward_date
                    create_alliances_spot(spot[1].strip(), spot[0].strip(), last_seen, type='spots')

        elif ('Результаты сражений:' in update._effective_message.text or 'Battle reports:' in update._effective_message.text) and (
                'По итогам сражений замкам начислено:' in update._effective_message.text or 'Scores' in update._effective_message.text):
            text = update._effective_message.text

            if update.channel_post.forward_from_chat.id == main_svodki_channel:
                mes_id = update.channel_post.forward_from_message_id

                # link = f'<a href="https://t.me/ChatWarsDigest/{mes_id}">Сводка</a>'
                link = f'<a href="https://t.me/chtwrsReports/{mes_id}">Сводка</a>'
            repl = r'Scores:\s([\d\D]+)'
            worldtop = re.findall(repl, text)
            if worldtop:

                reg_action = r'(?P<emoj>.*)(?:At )(?P<castle>.)'
                reg_gold = r'(?:🏆Attackers have pillaged the castle for |🏆Attackers have lost )(?P<gold>\d+) gold'

                gold_map = {}
                for castle in text.split('\n\n'):
                    gold = 0
                    mobj = re.search(reg_action, castle)
                    if mobj:
                        extra_emo = ''
                        if 'were bored - no one has attacked them' in castle:
                            extra_emo = '😴'
                        elif 'wiped out by a horde' in castle:
                            extra_emo = '😎'
                        elif 'have easily fought off' in castle:
                            extra_emo = '👌'
                        elif 'was a bloody massacre' in castle:
                            extra_emo = '⚡️'
                        elif 'had a slight edge' in castle:
                            extra_emo = '⚡️'
                        temp_castle = mobj['castle']
                        gold_map[temp_castle] = {'emoj': extra_emo + mobj['emoj']}
                        mobj = re.search(reg_gold, castle)
                        if mobj:
                            if mobj['gold']:
                                gold_map[temp_castle]['gold'] = mobj['gold']
                            else:
                                gold_map[temp_castle]['gold'] = 0

                reg = r'(.)([\D\s]+)\+(?P<points>\d+) 🏆 points'
                mobj = re.findall(reg, worldtop[0])
                if mobj:
                    date = date_to_cw_battle(update.channel_post.forward_date)
                    old_date = date - timedelta(hours=8)
                    for castle in mobj:
                        add_world_top(
                            emodji=castle[0], name=castle[1], points=castle[2], old_date=old_date,
                            date=date, action=gold_map[castle[0]].get('emoj'), gold=gold_map[castle[0]].get('gold'))
                    send_world_top(context, mid_id, date, extra=None, link=link)

        if not context.chat_data.get('top', False):
            context.chat_data['top'] = []
            context.chat_data['worst'] = []

        top = []  # 🦇🐺[OGW]Альрия
        top_worst = []
        guilds = ['OGW', 'SIF', 'STG', 'MAG']
        temp_worst = re.findall(r'🛡 At ({})(.*)\n🎖Attack leaders:(.*)\n🎖Defense leaders:'.format('|'.join(castle_emoji)), report)
        for guild in guilds:
            best = []
            worst = []

            if temp_worst:
                for castle in temp_worst:
                    if re.findall(r'\[{}]([\w\d\-\_🎗 ]+)[ |,|\n]'.format(guild), castle[2]):
                        worst += (castle[0], re.findall(r'\[{}]([\w\d\s\-\_]+)[ |,|\n]'.format(guild), castle[2]))
            best = re.findall(r'\[{}]([\w\d\-\_🎗 ]+)[ |,|\n]'.format(guild), report)
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
        if 'Scores' in report:
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
                        else:
                            text += 'Для {} я еще не придумал текст, {} предложи свой'.format(hero[0], hero[1])
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

    # mobu
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        if '/fight' in update.message.text.lower():
            create_mobu(update, context)

    # update resorce codes
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        if 'Guild Warehouse' in update.message.text:
            for row in update.message.text.split('\n'):
                mobj = re.search(r'(\w\d+|\d+) ([\w\s]+) x', row)
                if mobj:
                    code, name = mobj.groups()
                    update_resourse_code(name, code)


    if update.message.forward_from and update.message.forward_from.id == 5265011919:
        if 'Почти!' in update.message.text or '🎉 Шикарно' in update.message.text:
            solved = re.search(r'Шикарно, .*\n\s([\s\w⬛️🟨🟩]+)Получно', update.message.text)
            if solved:
                words = [x.replace(' ', '') for x in solved.group(1).strip().split('\n')]
                add_new_words(words[::2])
            guessing = re.search(r'Попробуй угадать!.*\n\s([\s\w⬛️🟨🟩]+)Количество попыток', update.message.text)
            if guessing:
                words = [x.replace(' ', '') for x in guessing.group(1).strip().split('\n')]
                add_new_words(words[::2])
                words_chunks = ([words[i:i + 2] for i in range(0, len(words), 2)])

                black_letter, yellow_letter, green_letter = [], {}, {}
                for chunk in words_chunks:
                    counter = 0
                    for symbol in chunk[1].replace(' ', ''):
                        if symbol in ['\u2B1B', '🟨', '🟩']:
                            if symbol == '\u2B1B':
                                black_letter.append(chunk[0][counter])
                            elif symbol == '🟩':
                                green_letter[counter] = chunk[0][counter]
                            elif symbol == '🟨':
                                if yellow_letter.get(counter):
                                    yellow_letter[counter].append(chunk[0][counter])
                                else:
                                    yellow_letter[counter] = [chunk[0][counter]]
                            counter += 1
                black_letter = set(black_letter)
                acceptable_words = word_examples(black_letter, green_letter, yellow_letter)
                if acceptable_words:
                    text = 'Попробуй {}'.format(', '.join(acceptable_words))
                    context.bot.send_message(chat_id=chat_id, text=text)
                else:
                    context.bot.send_message(chat_id=chat_id, text='Нет вариантов😢')


    # alliance
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
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
        if update.message.forward_date < datetime(year=2022, month=9, day=1, hour=13, minute=0, second=0).replace(tzinfo=timezone.utc):
            text = 'Я тебе что шутка? Ищи новые.'
            context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
        else:

            if all([name, code, spot_type]):
                new_spot = create_spot(name, code, spot_type, chat_id)
                if new_spot:
                    context.bot.send_message(chat_id=chat_id, text=new_spot_text, parse_mode='html')
                else:
                    context.bot.send_message(chat_id=chat_id, text=old_spot_text, parse_mode='html')

    # - gold
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        reg_gold = r'💰Gold: -(\d+)'
        if 'Твои результаты в бою:' in update.message.text or 'Your result on the battlefield:' in update.message.text:
            gold = re.search(reg_gold, update.message.text)
            if gold:
                gold = int(gold.group(1))
                texts = []
                if gold >= 1:
                    texts.append('Ой, всё, отдал деньги врагу, несите Маше валерьянку!')
                    texts.append('Я тебя записал! Пока только карандашом')
                    texts.append('Помощь пришла, откуда не ждали')
                    texts.append('Опять ножик лагал? Давай оправдывай себя, лентяй.')
                    texts.append('А лучше бы в гильдию')
                if gold > 2:
                    texts.append('А мог бы купить травы. Совсем себя не бережешь')
                    texts.append('Не слитая голда? Чо там у нас дальше по гештальтам')
                    texts.append('Твоя лень - халява для противника')
                    texts.append('Вот змей, откуда золото лишнее?😑')
                if gold > 10:
                    texts.append('Резко уходи в закат')
                    texts.append('Ну да, мы же миллионеры, нам терять нечего')
                if gold > 15:
                    texts.append('Гуляйте на все, чо! Отряд OGW может себе это позволить!')

                # text = 'Атата. Ты знаешь сколько всего можно было купить на {}'.format(gold)
                context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')
        if ('Твои результаты в бою:' in update.message.text or 'Your result on the battlefield:' in update.message.text) and ('🏅Enraged' in update.message.text or '🏅Peacekeeping' in update.message.text):
            texts = ['Ого, грац с медалькой', 'Талантливого человека видно сразу', 'Так ты ещё и талантлив🥰']
            context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')

    # корован
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        if 'Он пытается ограбить КОРОВАН' in update.message.text or 'trying to pillage a local village' in update.message.text:
            context.bot.send_message(chat_id=chat_id, text='/go', parse_mode='html')
        elif 'Ты задержал ' in update.message.text or 'You successfully defeated ' in update.message.text:
            texts = [
                'молодец, волчара, так держать',
                'хорош, теперь отгрызи ему голову',
                'мы в тебе не сомневались',
                'Мамкин Робин Гуд',
                'Хах! Поймал',
                'Вижу в ДПС пошел?']
            context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')
        elif 'Ты пытался остановить' in update.message.text or 'You tried stopping' in update.message.text:
            texts = [
                'не расстраивайся, мы его еще догоним',
                'ну 10 гп, это 10 гп',
                'тренируйся дальше, он ещё не раз вернется',
                'В следующий раз далеко не убежит',
                'Запомнил его?']
            context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')

    # суслик
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        if 'Ты пошел чесать своего суслика' in update.message.text:
            texts = [
                'У суслика нет цели. Только путь.',
                'Суслики правят миром, и тот сильнее, у кого их больше!', 'Когда ты суслик - ты неотразим.',
                'Суслик - это как волк. Только не волк.',
                'Гнев суслика не удержим, любовь неповторима, верность бесконечна...',
                'Падают слезы\nКак капли дождя\nСуслик карает',
                'Тихую безлунную ночь\nПрерывают крики и слёзы \nСуслик вышел на охоту']
            if '🐎' in update.message.text:
                texts.append('Все, чего достиг?\nИзвозив коня в грязи\nСуслик прилег.')
                texts.append('Тихая лунная ночь\nСлышно, как в замке Розы\nплачет обиженный конь.')
            elif '🐢' in update.message.text:
                texts.append('Мокр суслик.\nТрепещи черепаха.\nОн зол.')
            elif '🖤' in update.message.text:
                texts.append('Замок затих и спит\nСуслик на охоту вышел\nЧерное сердце дрожи')
            elif '🐭' in update.message.text:
                texts.append('Суслик на Ферме.\nОбиду мышь затаила.\nНе кродеться.')
            elif '🐪' in update.message.text:
                texts.append('Какая грусть!\nСусликом  нагло обижен,\nтужит верблюд.')
            elif '🐷' in update.message.text:
                texts.append('Смотри-ка суслик,\nЛегко смог свинью обидеть.\nДовольный какой!')
            elif '🕷' in update.message.text:
                texts.append('Как хорош суслик!\nПаука приструнил он.\nПусть не кусается.')
            elif '👻' in update.message.text:
                texts.append('Даже призрак\nОт страха дрожит.\nСуслик резвится.')
            # elif '🐾🐭🐜' in update.message.text:
            #     texts.append('Смотри-ка суслик,\nЛегко смог свинью обидеть.\nДовольный какой!')

            if random.randint(1, 100) < 20:
                photos = [
                    'https://faunistics.com/wp-content/uploads/2020/06/1.jpg',
                    'https://lh3.googleusercontent.com/proxy/6auisi0otSFtQRzz3RGq8d-xC9_3TiqarGzV48bK4IFYgLp4_gvRtpcjOTgYDKFjZhuEEsbI5vKKhR2_gr5oQfA04PVYhAE',
                    'https://avatars.mds.yandex.net/get-zen_doc/95163/pub_5b07f7a1799d9d0c5f4d6181_5b08011f1410c3b18bef406c/scale_1200',
                    'https://stihi.ru/pics/2013/04/08/7880.jpg']
                context.bot.send_photo(chat_id=chat_id, photo=random.choice(photos))
            else:
                context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')

    # обижен сусликом
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        if 'Обижен' in update.message.text or 'Измазан в грязи' in update.message.text:
            castle = None
            mobj = re.search('Обижен 🐾\w+ воина (?P<castle>.)\w+', update.message.text)
            if mobj:
                castle = mobj['castle']

            texts = [
                'Во тьме ночи, при свете дня\nЗлу не укрыться от меня!\nПадут все те, в чьих душах тьма!\nВперёд все суслики! Ура-аа!',
                'Око за око\nЗуб за зуб\nСуслики Ночи\nМесть несут',
                'Во тьме ночной при свете дня!\nЗлу не укрыться от меня!\nНас не обидят кто подряд!\nВперёд же сусликов отряд!',
                'Чтоб явить злодею  - лоботрясу\nКузькину маманю в полный рост,\nСуслики выходят по приказу\nМстить по замкам, охраняя свой блокпост',
                'Мы пришли из ниоткуда\nИ уйдем вновь в никуда\nБудет месть тебе, поскуда,\nНе ходи к нам никогда',
                'В темной ночи, сверкая резцами\nК неприятелю обиженный суслик (кродёться)\nЧто б месть холодную свершить\nИ спиздить кукурузку'
            ]
            if castle:
                texts.append('@shovkovytsya @lliyami @Ra18Ra @Wilhe_lm Внеплановый сбор отряда сусликов, атакуем {}'.format(castle))

            context.bot.send_message(chat_id=chat_id, text=random.choice(texts), parse_mode='html')

    # reports
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        if ('Твои результаты в бою:' in update.message.text or 'Your result on the battlefield:' in update.message.text) and ('Встреча' not in update.message.text and 'Encounter' not in update.message.text):
            date = date_to_cw_battle(update.message.forward_date)
            reg_nick = r'('+ '|'.join(castle_emoji) +').\[\w+\]([\w\s_-]+)⚔|('+ '|'.join(castle_emoji) +')([\w\s_-]+)⚔|(' + '|'.join(castle_emoji) + ')\[\w+\]([\w\s_-]+)⚔'
            nickname = re.match(reg_nick, update.message.text)
            if any(nickname.groups()):
                nickname = [x.strip() for x in nickname.groups() if x is not None][1]
            new_report = create_report(chat_id, nickname, update.message.text, date)
            if not new_report:
                context.bot.send_message(chat_id=chat_id, text=old_report_text, parse_mode='html')

    # update top
    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        # castles = ['🐢Тортуга', '🌹Замок Рассвета', '🍁Амбер', '🦇Ночной Замок', '🖤Скала', 'Past battles']
        
        castles = castle_full + ['Past battles']
        date = date_to_cw_battle(update.message.forward_date)

        if all([x in update.message.text for x in castles]):
            reg = r'#\s\d\s(?P<emodji>.)(?P<name>[\D\s]+)🚩(?P<points7>[\d\.]+.)🏆(?P<points>\d+)'
            mobj = re.findall(reg, update.message.text)
            if mobj:
                old_top = get_all_world_top(date)
                wt_ordering_old = [x.emodji for x in old_top]
                for obj in mobj:
                    update_world_top(emodji=obj[0], name=obj[1], points=obj[3], date=date)

                new_top = get_all_world_top(date)
                new_top_points = {x.emodji: x.points for x in old_top}
                wt_ordering_new = [x.emodji for x in new_top]
                text = ''
                for castle in wt_ordering_new:
                    if wt_ordering_new.index(castle) != wt_ordering_old.index(castle):

                        if len([key for key, value in new_top_points.items()
                               if value == new_top_points.get(castle)]) > 1:
                            continue
                        if not text:
                            text = 'Топ изменился'
                        if wt_ordering_new.index(castle) <= wt_ordering_old.index(castle):
                            text += '\n(🔺{}){}'.format(
                                abs(wt_ordering_new.index(castle) - wt_ordering_old.index(castle)), castle)
                        else:
                            text += '\n(🔻{}){}'.format(
                                abs(wt_ordering_old.index(castle) - wt_ordering_new.index(castle)), castle)
                if text:
                    context.bot.send_message(chat_id=mid_id, text=text, parse_mode='HTML')

    if update.message.forward_from and update.message.forward_from.id == cwbot_id:
        marks = ['Commander', '🎖Glory', '🏅Level']
        if all([x in update.message.text for x in marks]):
            tag_reg = r'(.)\[([\w\d]+)\]'

            mobj = re.search(tag_reg, update.message.text)
            if mobj:
                castle, tag = mobj.groups()
            glory_reg = r'🎖Glory: (\d+)'
            mobj = re.search(glory_reg, update.message.text)
            glory = mobj.groups()[0]

            date = update.message.date

            print(castle, tag, glory)


def inline_button(update, context):
    # castles = ['🦇', '☘️', '🍁', '🍆', '🌹', '🖤', '🐢']
    # castles = ['🌑', '🐺', '🥔', '🐉', '🦈', '🦌', '🦅']
    if update.callback_query.data in castle_emoji:
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
    if update.callback_query.data != 'тык':
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
            if who == 597266304:  # katya
                texts.append('С тебя нюдес.')
                texts.append('А ты плохая девочка, отшлёпаю.')
            elif who == 252167939:  # masha
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
                texts.append('Дал бог Корбина, даст и плащ')
                texts.append('Часики то тикают, а у тебя Корбин без плаща')
                texts.append('А ты ищешь плащ своему алху?')
                texts.append('А может ну его, этот плащ?')
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


def help(update, context):
    chat_id = update.message.chat_id
    context.bot.send_message(
        chat_id=chat_id,
        text=help_text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


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


# def get_tags(castle):
#     tags = ''
#     if '⚔' in castle.action:
#         tags += '#{}_пробили '.format(castle.name.strip().replace(' ', '_').lower())
#         if '⚡️' in castle.action:
#             tags += '#{}_молния '.format(castle.name.strip().replace(' ', '_').lower())
#     elif '👌🛡' in castle.action or '😴' in castle.action:
#         return tags
#     elif '🛡' in castle.action:
#         tags += '#{}_дефнули '.format(castle.name.strip().replace(' ', '_').lower())
#         if '🔱' in castle.action:
#             tags += '#{}_га '.format(castle.name.strip().replace(' ', '_').lower())

#     return tags


def calculate_atak(update, context):
    global user_data
    message = update.message
    chat_id = update.message.chat_id
    if update.message.reply_to_message:
        message = update.message.reply_to_message
        if message.forward_from and message.forward_from.id == cwbot_id and (
                'Твои результаты в бою:' in message.text or 'Your result on the battlefield:' in message.text):
            m_text = message.text
            m_date = date_to_cw_battle(message.forward_date)
            re_atk = r'⚔️:(?P<atk>\d+).* 🛡:(?P<def>\d+)'
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

        # castles = ['🦇', '☘️', '🍁', '🍆', '🌹', '🖤', '🐢']
        # castles = ['🌑', '🐺', '🥔', '🐉', '🦈', '🦌', '🦅']
        keyboard = []
        row = []
        for castle in castle_emoji:
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

def sort_jewerly(update, context):
    message = update.message
    chat_id = update.message.chat_id
    if update.message.reply_to_message:
        message = update.message.reply_to_message
        if message.forward_from and message.forward_from.id == cwbot_id and 'Guild Warehouse:' in message.text:
            m_text = message.text
            jewerly_reg = r'(u\d+ (?:..)?Mystery (?:ring|amulet) lvl.(\d+)[\s\d:.↑↓%\-🏹⚗️🎩⚔️🛡🩸📦🛠(Def|Hp|Atk|Mana)]+)'
            mobj = re.findall(jewerly_reg, m_text)
            if mobj:
                from operator import itemgetter
                mobj = sorted(mobj, key=itemgetter(1), reverse=True)
                text = ''
                for obj in mobj:
                    text += obj[0] + '\n'
                context.bot.send_message(
                    chat_id=chat_id,
                    text=text)
    else:
        text = 'Не вижу куда, сделай reply'
        context.bot.send_message(chat_id=chat_id, text=text)


@admin_decorator
def whois(update, context):
    chat_id = update.message.chat_id
    text = ''
    users = get_user_data(type='requestProfile')
    for user in users:
        user_data = json.loads(user.data)
        if user_data.get('guild_tag'):
            text += '\n[{}]{} {} {}'.format(
                user_data.get('guild_tag'), user_data.get('userName'), user_data.get('class'), user_data.get('lvl'))
        else:
            text += '\n{} {} {}'.format(user_data.get('userName'), user_data.get('class'), user_data.get('lvl'))
    context.bot.send_message(chat_id, text)


def main():

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("add_mobu", add_mobu))
    dp.add_handler(CommandHandler("auth", auth))
    dp.add_handler(CommandHandler("auth_gear", auth_gear))
    dp.add_handler(CommandHandler("auth_guild", auth_guild))
    dp.add_handler(CommandHandler("auth_stock", auth_stock))
    dp.add_handler(CommandHandler("a_guilds", a_guilds))
    dp.add_handler(CommandHandler("a_spots", a_spots))
    dp.add_handler(CommandHandler("as_enable", as_enable))
    dp.add_handler(CommandHandler("as_disable", as_disable))
    dp.add_handler(CommandHandler("calc", calculate_atak))
    dp.add_handler(CommandHandler("du", myduels))
    dp.add_handler(CommandHandler("dug", myguild_duels))
    dp.add_handler(CommandHandler("delspot", del_spot))
    dp.add_handler(CommandHandler("gear", gear))
    dp.add_handler(CommandHandler("guild", guild))
    dp.add_handler(CommandHandler("guilds", guilds))
    dp.add_handler(CommandHandler("gs", gold_rules))
    dp.add_handler(CommandHandler("gs_enable", gs_enable))
    dp.add_handler(CommandHandler("gs_disable", gs_disable))
    dp.add_handler(CommandHandler("me", me))
    dp.add_handler(CommandHandler("profile", profile))
    dp.add_handler(CommandHandler("qtop", qtop))
    dp.add_handler(CommandHandler("reports", reports))
    dp.add_handler(CommandHandler("sell_disable", sell_disable))
    dp.add_handler(CommandHandler("sell_enable", sell_enable))
    dp.add_handler(CommandHandler('sort', sort_jewerly))
    dp.add_handler(CommandHandler("spot", find_spot))
    dp.add_handler(CommandHandler("spend", spend_my_gold))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stock", stock))
    dp.add_handler(CommandHandler("update_profile", update_profile))
    dp.add_handler(CommandHandler("update_gear", update_gear))
    dp.add_handler(CommandHandler("users", users))
    dp.add_handler(CommandHandler("whois", whois))
    dp.add_handler(CommandHandler("worldtop", worldtop))
    dp.add_handler(CommandHandler("wtb", wtb))
    dp.add_handler(CommandHandler("wtop", wtop))
    SHEAR_REGEX = r'\/battles(?:_(\d+))?(?: (\S+))?(?: (\S+))?'
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(SHEAR_REGEX), shear_top))

    # sub guilds for glory
    dp.add_handler(CommandHandler("sub_guild", sub_guild))
    dp.add_handler(CommandHandler("unsub_guild", unsub_guild))
    dp.add_handler(CommandHandler("list_sub_guild", list_sub_guilds))

    dp.add_handler(InlineQueryHandler(inlinequery))
    dp.add_handler(ChosenInlineResultHandler(on_result_chosen))

    dp.add_handler(CommandHandler("add_word", add_word))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+time \d\d:\d\d'), add_time_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+deltime \d\d:\d\d'), del_time_trigger))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+listtime'), list_time_triggers))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'\+\+add [\s\w\/\d\.]+'), add_trigger))
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
            print(first)
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
    job.run_repeating(glory_update, interval=28800, first=(first + 1260))
    job.run_repeating(all_gear_update, interval=28800, first=(first + 1260))
    job.run_repeating(auto_spend_gold, interval=28800, first=first)
    trigger_time = now.replace(minute=58, second=0)
    first = (trigger_time - now).seconds
    job.run_repeating(glory_update, interval=3600, first=first)


def init_db():
    db.connect(reuse_if_open=True)
    from alliances.models import Alliances, Spot
    from triggers.models import Trigger, TimeTrigger
    from users.models import UserData, GoldRules, WtbLogs, Duels, Users, Guilds, Request, Token, Report, UserSettings
    from core.models import (WorldTop)
    from public.models import Prices
    from mobu.models import Messages, Chats
    db.create_tables(
        [Trigger, TimeTrigger, Spot, Report, Token, Request, Guilds, GuildsGlory, Users, Chats, Messages,
         UserData, GoldRules, WtbLogs, Alliances, WorldTop, Duels, Prices, UserSettings], safe=True)
    db.close()


updater = Updater(TOKEN, use_context=True)
job = updater.job_queue

if __name__ == '__main__':
    init_db()
    start_time_triggers()
    main()
