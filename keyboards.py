from telegram import InlineKeyboardButton, ReplyKeyboardMarkup

def menu_markup():

    keyboard = [[InlineKeyboardButton("💰Слив голды"),
                 InlineKeyboardButton("📦Сток")]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    return reply_markup
