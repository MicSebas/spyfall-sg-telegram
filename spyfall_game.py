import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database


def start(bot, update):
    users = db.get_users()
    user_id = update.message.from_user.id
    if user_id in users:
        game_room_id = db.get_user_attribute(user_id, 'game_room')
        game_master = db.get_room_attribute(game_room_id, 'master_name')
        msg = 'You are already in the middle of a game!\nGame room: *%s* (%s)' % (game_room_id, game_master)
        keyboard = None
    else:
        msg = 'Hi, %s! Welcome to *Spyfall SG Telegram Bot*!\n\nWhat would you like to do?' % update.message.from_user.first_name
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Start Game', callback_data='start_game'), InlineKeyboardButton('Join Game', callback_data='start_join')],
                                         [InlineKeyboardButton('cancel', callback_data='cancel')]])
    bot.send_message(user_id, msg, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=keyboard)


def cancel(bot, update):
    user_id = update.callback_query.from_user.id
    users = db.get_users()
    if user_id not in users:
        msg_id = update.callback_query.message.message_id
        msg = 'Operation cancelled. Thank you for using Spyfall SG Telegram Bot!'
        bot.edit_message_text(msg, user_id, msg_id)
    else:
        room_id = db.get_user_attribute(users, 'game_room')
        players = db.get_room_attribute(room_id, 'roles')
        msg = 'Game cancelled by game master. Use /start to start or join a new game!'
        for player_id in players:
            msg_id = db.get_user_attribute(player_id, 'msg_id')
            bot.edit_message_text(msg, player_id, msg_id)
            db.remove_user(player_id)
        db.delete_room(room_id)


def start_game(bot, update):
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    msg = 'How many spies do you want for this game?\n\nWe recommend 2 spies if you have more than 7 players.'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('1', callback_data='spies_1'), InlineKeyboardButton('2', callback_data='spies_2')],
                                     [InlineKeyboardButton('cancel', callback_data='cancel')]])
    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def start_join(bot, update):
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    msg = 'Which game do you want to join?'
    rooms = db.get_rooms()
    keyboard = [[InlineKeyboardButton(room, callback_data='join_%s' % room)] for room in rooms]
    keyboard.append([InlineKeyboardButton('Refresh', callback_data='start_join')])
    keyboard.append([InlineKeyboardButton('cancel', callback_data='cancel')])
    keyboard = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def init_game(bot, update):
    user_id = update.callback_query.from_user.id
    user_name = update.callback_query.from_user.username
    user_fullname = update.callback_query.from_user.first_name + ' ' + update.callback_query.from_user.last_name
    user_fullname = user_fullname.strip()
    msg_id = update.callback_query.message.message_id
    spies = int(update.callback_query.data[-1])
    room_id = db.init_room(user_id, user_name, spies)
    db.add_user(user_id, user_fullname, room_id, True, msg_id)
    msg = 'Game room ID: *%s*\n\n' % room_id
    msg += 'Waiting for players...\n'
    msg += '1. %s' % user_fullname
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Start Game!', callback_data='begin')],
                                     [InlineKeyboardButton('Cancel', callback_data='cancel')]])
    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard, parse_mode=telegram.ParseMode.MARKDOWN)


def join_game(bot, update):
    user_id = update.callback_query.from_user.id
    user_fullname = update.callback_query.from_user.first_name + ' ' + update.callback_query.from_user.last_name
    user_fullname = user_fullname.strip()
    room_id = update.callback_query.data.split('_')[1]
    players = db.get_room_attribute(room_id, 'players')
    if players > 11:
        query_id = update.callback_query.id
        msg = 'This room is at full capacity!'
        bot.answer_callback_query(query_id, msg)
    else:
        msg_id = update.callback_query.message.message_id
        db.join_room(room_id, user_id)
        db.add_user(user_id, user_fullname, room_id, False, msg_id)
        players = db.get_room_attribute(room_id, 'roles')
        msg = 'Game room ID: *%s*\n\n' % room_id
        if len(players) < 12:
            msg += 'Waiting for players...\n'
        else:
            msg += 'Room is at full capacity!\n'
        for i, player_id in enumerate(players):
            player_name = db.get_user_attribute(player_id, 'user_name')
            msg += '%d. %s\n' % (i+1, player_name)
        msg = msg.strip()
        for player_id in players:
            msg_id = db.get_user_attribute(player_id, 'msg_id')
            if db.get_user_attribute(player_id, 'master'):
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Start Game!', callback_data='begin')],
                                                 [InlineKeyboardButton('Cancel', callback_data='cancel')]])
            else:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Quit game', callback_data='quit')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard, parse_mode=telegram.ParseMode.MARKDOWN)


def begin_game(bot, update):
    pass


def quit_room(bot, update):
    pass


def callback_query_handler(bot, update):
    data = update.callback_query.data
    if data == 'start_game':
        start_game(bot, update)
    elif data == 'start_join':
        start_join(bot, update)
    elif data == 'cancel':
        cancel(bot, update)
    elif data.startswith('spies'):
        init_game(bot, update)
    elif data.startswith('join'):
        join_game(bot, update)
    # elif data == 'begin':
    #     begin_game(bot, update)
    # elif data == 'quit':
    #     quit_room(bot, update)
    else:
        query_id = update.callback_query.id
        bot.answer_callback_query(query_id, 'Function unavailable')


def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    if MODE == 'dev':
        updater.start_polling()
    elif MODE == 'prod':
        updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
        updater.bot.set_webhook("https://spyfall-sg-telegram.herokuapp.com/" + TOKEN)
    else:
        print('MODE NOT VALID')
        exit()
    updater.idle()


if __name__ == '__main__':
    MODE = os.getenv("MODE")
    TOKEN = os.getenv("TOKEN")
    PORT = int(os.getenv("PORT"))
    DATABASE_URL = os.getenv('DATABASE_URL')
    db = Database(DATABASE_URL)
    main()
