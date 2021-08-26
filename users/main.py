import json
import logging
import re
import time
from datetime import datetime, timedelta
from threading import Thread

import pytz
from core import cw_api
from core.config import TIMEZONE
from core.texts import *
from core.utils import date_to_cw_battle
from public.utils import *
from users.utils import *

user_data = {}
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING)

logger = logging.getLogger(__name__)

# api
def auth(update, context):
    user_id = update.message.from_user.id
    context.bot.send_message(user_id, api_auth_text)
    cw_api.createAuthCode(user_id)


def process_code(user_id, code):
    request = find_request(user_id)
    if request:
        if request.action == 'createAuthCode':
            cw_api.grantToken(user_id, code)
        elif request.action == 'authAdditionalOperation':
            token = find_token(user_id)
            cw_api.grantAdditionalOperation(token.token, request.req_id, code)

            if request.operation == 'GetUserProfile':
                time.sleep(3)
                cw_api.request_action(token.token, action='requestProfile')


# api profile
def profile(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='GetUserProfile')
        time.sleep(3)
        update_profile(update, context)


def update_profile(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    delete_log(user_id, None)
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.request_action(token.token, action='requestProfile')
        context.bot.send_message(chat_id=chat_id, text='Обновляю профиль')


def me(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.request_action(token=token.token, action='requestProfile')


# api stock
def auth_stock(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='GetStock')


def stock(update, context):
    chat_id = update.message.from_user.id
    token = find_token(chat_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.request_action(token.token, action='requestStock')


# api gear
def auth_gear(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='GetGearInfo')


def gear(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    gear = get_user_data(user_id, 'requestGearInfo')
    user = get_user_data(user_id, 'requestProfile')
    if not gear:
        token = find_token(user_id)
        if not token:
            context.bot.send_message(chat_id=chat_id, text=first_auth_text)
        else:
            cw_api.request_action(token.token, action='requestGearInfo')
            time.sleep(3)
    if gear and user:
        user = json.loads(user.data)
        gear = json.loads(gear.data)

        text = '{}{} <strong>{}</strong> gear:\n\n'.format(
            user.get('castle'), user.get('class'), user.get('userName'))

        formated_gear = {}
        quality_mapper = {
            'Masterpiece': 'A',
            'Excellent': 'B',
            'Great': 'C',
            'High': 'D',
            'Fine': 'E',
            'Epic Fine': 'SE',
            'Epic High': 'SD',
            'Epic Great': 'SC',
            'Epic Excellent': 'SB',
            'Epic Masterpiece': 'SA',
        }

        for key, value in gear.items():
            f_text = value.get('name')
            if value.get('condition') == 'broken':
                f_text = '🛠 ' + f_text
            if value.get('condition') == 'reinforced':
                f_text = f_text.replace('⚡', '✨')

            if value.get('quality', None):
                f_text += '({})'.format(quality_mapper.get(value.get('quality', None)))

            if value.get('atk'):
                f_text += '⚔️{}'.format(value.get('atk'))
            if value.get('def'):
                f_text += '🛡{}'.format(value.get('def'))
            if value.get('mana'):
                f_text += '💧{}'.format(value.get('mana'))

            if f_text:
                formated_gear[key] = f_text
        text += '\n'.join([formated_gear.get('weapon', ''), formated_gear.get('offhand', ''),
                           formated_gear.get('head', ''), formated_gear.get('hands', ''),
                           formated_gear.get('body', ''), formated_gear.get('feet', ''),
                           formated_gear.get('coat', ''), formated_gear.get('ring', ''),
                           formated_gear.get('amulet', '')])
        # text += '''{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}'''.format(
        #     )

    else:
        text = no_gear_text

    context.bot.send_message(chat_id, text, parse_mode='HTML')


def update_gear(update, context):
    chat_id = update.message.from_user.id
    token = find_token(chat_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.request_action(token.token, action='requestGearInfo')


def all_gear_update(context):
    gear_info = get_user_data(type='requestGearInfo')
    for gear in gear_info:
        chat_id = gear.chat_id
        token = find_token(chat_id)
        if token:
            cw_api.request_action(token.token, action='requestGearInfo')


# api guild
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


# api spend gold
def wtb(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    token = find_token(user_id)
    if not token:
        context.bot.send_message(chat_id=chat_id, text=first_auth_text)
    else:
        cw_api.authAdditionalOperation(token.token, operation='TradeTerminal')


def gold_rules(update, context):
    user_id = update.message.from_user.id
    text = update.message.text
    if not re.search(r'/gs[\n\s]+', text) or len(text.split('\n')) <= 1:
        context.bot.send_message(chat_id=user_id, text=gold_rules_bad_format_text)
    else:
        rules = '\n'.join([x.strip() for x in text.split('\n') if re.search(r'\d+ \d+', x)])
        create_rules(user_id, rules)
        context.bot.send_message(chat_id=user_id, text=gold_rules_save_text)


def gs_enable(update, context):
    chat_id = update.message.from_user.id
    update_rules(chat_id, True)
    context.bot.send_message(chat_id, text=auto_enabled_text)
    pass


def gs_disable(update, context):
    chat_id = update.message.from_user.id
    update_rules(chat_id, False)
    context.bot.send_message(chat_id, text=auto_disable_text)
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
        user_settings = get_user_settings(rule.chat_id)
        if user_settings:
            send_notification = user_settings.auto_spend_notification
        else:
            send_notification = True
        data = json.loads(user.data)
        user_gold = data.get('gold', 0)
        rules = [x.split(' ') for x in rule.rules.split('\n')]
        prices = []
        for r in rules:
            price = get_prices(r[0])
            price = [x for x in set(price.prices) if x <= int(r[1])]
            prices.append(price)
        while user_gold > 0 and len(rules):
            date = datetime.now() - timedelta(hours=1)
            log = get_wtb_log(rule.chat_id, date)
            if not log:
                r = rules[0]
                if (prices[0]):
                    price = prices[0][0]
                else:
                    prices.pop(0)
                    rules.pop(0)

                quantity = user_gold // price
                if quantity > 0:
                    create_wtb(rule.chat_id, quantity, price, item=r[0])
                    cw_api.wantToBuy(token.token, item_code=r[0], quantity=quantity, price=price)
                else:
                    rules.pop(0)
                    prices.pop(0)

            if log:
                if log.status == 'Ok':
                    user_gold -= log.quantity * log.price
                    if not user_data.get(rule.chat_id) or not user_data.get(rule.chat_id).get('m_id', False):
                        if send_notification:
                            try:
                                message = context.bot.send_message(
                                    rule.chat_id,
                                    text='Купил {}x{} по {}'.format(log.item, log.quantity, log.price),
                                    disable_notification=True)
                            except Exception as e:
                                update_rules(rule.chat_id, False)
                                print('{} {}'.format(rule.chat_id, e))

                            user_data[rule.chat_id] = {}
                            user_data[rule.chat_id]['m_id'] = message.message_id
                            user_data[rule.chat_id]['m_text'] = message.text

                    else:
                        if send_notification:
                            text = user_data[rule.chat_id].get('m_text', '')
                            text += '\nКупил {}x{} по {}'.format(log.item, log.quantity, log.price)
                            context.bot.edit_message_text(
                                chat_id=rule.chat_id,
                                message_id=user_data[rule.chat_id].get('m_id', False),
                                text=text)
                    rules.pop(0)
                    prices.pop(0)
                    delete_log(chat_id=rule.chat_id, status='Ok')
                elif log.status == 'NoOffersFoundByPrice':
                    if len(prices) > 1:
                        prices[0].pop(0)
                    else:
                        prices.pop(0)
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
        if send_notification:
            context.bot.send_message(
                chat_id=rule.chat_id, text='Слив окончен, осталось {}'.format(user_gold), disable_notification=True)


def auto_spend_gold(context):
    print('start auto spend')
    gr = get_all_rules()
    for rule in gr:
        print('start for {}'.format(rule.chat_id))
        logger.warning('spending gold for {}'.format(rule.chat_id))
        thread = SpendThread(rule.chat_id, rule, context)
        thread.start()


class SpendThread(Thread):
    def __init__(self, chat_id, rule, context):
        Thread.__init__(self)
        self.chat_id = chat_id
        self.rule = rule
        self.context = context

    def run(self):
        spend_gold(self.chat_id, self.rule, self.context)


# duels
def myduels(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    extra = update.message.text.replace('/du', '').strip()
    date = update.message.date.astimezone(pytz.timezone(TIMEZONE))
    if date.hour < 13:
        date = date - timedelta(days=1)
    date = date.replace(hour=9, minute=0, second=0)
    date = date.replace(tzinfo=None)
    duels, username = get_duels(user_id, date, extra)
    if duels is False:
        text = 'Duels of {} not found'.format(username)
    if username is None:
        text = 'Мы пока не знакомы, пройди авторизацию'
    else:
        win_count = 0
        win_text = ''
        lose_count = 0
        lose_text = ''
        lvl = 0
        for duel in duels:
            if username == duel.winner_name:
                win_count += 1
                lvl = duel.winner_level
                if duel.loser_guild:
                    guild = r'[{}]'.format(duel.loser_guild)
                else:
                    guild = ''
                win_text += '{} {} {} {}\n'.format(duel.loser_level, duel.loser_castle, guild, duel.loser_name)
            elif username == duel.loser_name:
                lose_count += 1
                lvl = duel.loser_level
                if duel.winner_guild:
                    guild = r'[{}]'.format(duel.winner_guild)
                else:
                    guild = ''
                lose_text += '{} {} {} {}\n'.format(duel.winner_level, duel.winner_castle, guild, duel.winner_name)

        text = '{} {}\n'.format(lvl, username)
        text += 'duels on {}/{}\n\n'.format(date.day, date.month)
        text += '❤️ Won {}\n'.format(win_count)
        text += win_text
        text += '\n'

        text += '💔 Lost {}\n'.format(lose_count)
        text += lose_text
        text += '\n'
        text += 'Total {}/{}'.format(win_count, lose_count)
    context.bot.send_message(chat_id, text, parse_mode='HTML')


def myguild_duels(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    extra = update.message.text.replace('/dug', '').strip()
    date = update.message.date.astimezone(pytz.timezone(TIMEZONE))
    # if date.hour >= 13:
    if date.hour < 13:
        date = date - timedelta(days=1)
    date = date.replace(hour=9, minute=0, second=0)
    date = date.replace(tzinfo=None)
    duels, guild = get_guild_duels(user_id, date, extra)
    if duels is False:
        text = 'Duels of {} not found'.format(guild)
    if guild is None:
        text = 'Мы пока не знакомы, пройди авторизацию'
    else:
        guildmates = {}
        for duel in duels:
            if guild == duel.winner_guild:
                if not guildmates.get(duel.winner_name, False):
                    guildmates[duel.winner_name] = {}
                    guildmates[duel.winner_name]['lvl'] = duel.winner_level
                    guildmates[duel.winner_name]['win'] = 1
                    guildmates[duel.winner_name]['lose'] = 0
                else:
                    guildmates[duel.winner_name]['win'] += 1
            elif guild == duel.loser_guild:
                if not guildmates.get(duel.loser_name, False):
                    guildmates[duel.loser_name] = {}
                    guildmates[duel.loser_name]['lvl'] = duel.loser_level
                    guildmates[duel.loser_name]['win'] = 0
                    guildmates[duel.loser_name]['lose'] = 1
                else:
                    guildmates[duel.loser_name]['lose'] += 1
        text = r'\[{}] duels on {}/{}'.format(guild, date.day, date.month)
        text += '\n\n'
        won = 0
        lost = 0
        # guildmates = guildmates.items().sort(key=lambda x: (x[1]['win']))
        sorted_keys = sorted(guildmates, key=lambda x: (guildmates[x]['win']), reverse=True)
        for key in sorted_keys:
            value = guildmates.get(key)
            won += value.get('win', 0)
            lost += value.get('lose', 0)
            text += '{}/{} {} {}\n'.format(
                value.get('win', 0), value.get('lose', 0), key, value.get('lvl'))

        text += '\n'
        text += '{} fighters won {} lost {}'.format(len(guildmates.keys()), won, lost)
        if '_' in text:
            text = text.replace('_', r'\_')
    context.bot.send_message(chat_id, text, parse_mode='Markdown')


# reports
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
            reports = find_report(-1001168950089, date, nickname, admin=True)
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
            reports = find_report(-1001168950089, date, nickname, admin=True)
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


def users(update, context):
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/users', '').strip()
    if not extra:
        pass
    else:
        users = get_users(extra)
        text = ''
        for user in users:
            text += '{:>2} {:<17}{:>6} {:>16}\n'.format(
                str(user.level), user.name, user.where,
                str(user.last_seen.strftime('%d.%m.%Y %H:%M')))

        context.bot.send_message(chat_id, text, parse_mode='HTML')


def update_guilds(update):
    text = update._effective_message.text
    last_seen = update.channel_post.forward_date

    guild_user_reg = r'(?P<castle>(☘️|🍆|🌹|🐢|🖤|🍁|🦇)).{0,2}\[(?P<tag>.{2,3})\](?P<nick>[\w\s\d_]+)(,|\n)'
    users = re.findall(guild_user_reg, text)
    if users:
        for user in users:
            if len(user[3].strip()) < 13:
                update_guild(castle=user[0], guild=user[2], where='battle', date=last_seen)
                update_user(
                    castle=user[0], guild=user[2].strip(), nick=user[3].strip(),
                    where='battle', date=last_seen, level=0)


def guilds(update, context):
    chat_id = update.message.chat_id
    extra = update.message.text.replace('/guilds', '').strip()
    if not extra:
        pass
    else:
        guilds = get_guilds(extra)
        text = ''
        for guild in guilds:
            text += '{}{} {} last seen {}\n'.format(
                guild.castle, '[' + guild.name + ']', guild.where.rjust(7),
                str(guild.last_seen).rjust(20))

        context.bot.send_message(chat_id, text, parse_mode='HTML')


def user_settings(update, context):
    chat_id = update.message.from_user.id
    settings = get_user_settings(chat_id)
    if settings:
        text = ''
        if settings.sell_notification:
            a = '✅'
            action = '/sell_disable'
        else:
            a = '❌'
            action = '/sell_enable'
        text += '{}Уведомления о продаже на бирже {}\n'.format(a, action)
        if settings.auto_spend_notification:
            a = '✅'
            action = '/as_disable'
        else:
            a = '❌'
            action = '/as_enable'
        text += '{}Уведомления о автосливе голды перед битвой {}\n'.format(a, action)
    else:
        token = find_token(chat_id)
        if not token:
            text = 'Надо пройти авторизацию /auth'
        else:
            text = 'Это новая функция, мне надо обновить токен, нажми /auth'
    context.bot.send_message(chat_id, text=text)


def as_enable(update, context):
    chat_id = update.message.from_user.id
    type = 'auto_spend_notification'
    update_settings(chat_id, True, type)
    context.bot.send_message(chat_id, text=as_enable_text)
    pass


def as_disable(update, context):
    chat_id = update.message.from_user.id
    type = 'auto_spend_notification'
    update_settings(chat_id, False, type)
    context.bot.send_message(chat_id, text=as_disable_text)
    pass


def sell_enable(update, context):
    chat_id = update.message.from_user.id
    type = 'sell_notification'
    update_settings(chat_id, True, type)
    context.bot.send_message(chat_id, text=sell_enabled_text)
    pass


def sell_disable(update, context):
    chat_id = update.message.from_user.id
    type = 'sell_notification'
    update_settings(chat_id, False, type)
    context.bot.send_message(chat_id, text=sell_disable_text)
    pass


def sub_guild(update, context):
    chat_id = update.message.from_user.id
    guild_name = update.message.text.replace('/sub_guild', '').strip()
    if guild_name:
        created = create_sub_guild(guild_name, chat_id)

        if not created:
            context.bot.send_message(update.message.chat_id, text=not_created_sub_guild.format(guild_name))
            return

        context.bot.send_message(update.message.chat_id, text=created_sub_guild.format(guild_name))


def unsub_guild(update, context):
    guild_name = update.message.text.replace('/unsub_guild', '').strip()

    deleted = delete_sub_guild(guild_name)
    if not deleted:
        context.bot.send_message(update.message.chat_id, text=not_deleted_sub_guild.format(guild_name))
        return

    context.bot.send_message(update.message.chat_id, text=deleted_sub_guild.format(guild_name))


def list_sub_guilds(update, context):
    guilds_list = get_sub_guilds()
    text = ''
    for guild in guilds_list:
        text += '\n{}{}'.format(guild.castle or '🤷‍♂️', guild.name)
    if not text:
        text = '🤷‍♂️'
    context.bot.send_message(update.message.chat_id, text=text)
