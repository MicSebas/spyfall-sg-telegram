import os
import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError
from database import Database
import json
from time import sleep


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
        room_id = db.get_user_attribute(user_id, 'game_room')
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
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Ready to Begin!', callback_data='begin')],
                                     [InlineKeyboardButton('cancel', callback_data='cancel')]])
    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard, parse_mode=telegram.ParseMode.MARKDOWN)


def join_game(bot, update):
    print('joining')
    user_id = update.callback_query.from_user.id
    print(user_id)
    user_fullname = update.callback_query.from_user.first_name + ' ' + update.callback_query.from_user.last_name
    user_fullname = user_fullname.strip()
    print(user_fullname)
    room_id = update.callback_query.data.split('_')[1]
    print(room_id)
    no_of_players = db.get_room_attribute(room_id, 'players')
    print(no_of_players)
    if no_of_players > 11:
        query_id = update.callback_query.id
        msg = 'This room is at full capacity!'
        bot.answer_callback_query(query_id, msg)
    else:
        msg_id = update.callback_query.message.message_id
        print(msg_id)
        players = db.join_room(room_id, user_id)
        print(players)
        db.add_user(user_id, user_fullname, room_id, 0, msg_id)
        print('added')
        msg = 'Game room ID: *%s*\n\n' % room_id
        if len(players) < 12:
            msg += 'Waiting for players...\n'
        else:
            msg += 'Room is at full capacity!\n'
        for i, player_id in enumerate(players):
            player_name = db.get_user_attribute(player_id, 'user_name')
            msg += '%d. %s\n' % (i+1, player_name)
        msg = msg.strip()
        print(msg)
        for player_id in players:
            print(player_id)
            player_id = int(player_id)
            print(player_id)
            msg_id = db.get_user_attribute(player_id, 'msg_id')
            print(msg_id)
            is_master = db.get_user_attribute(player_id, 'master')
            print(is_master)
            if is_master:
                print('master keyboard')
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Ready to Begin!', callback_data='begin')],
                                                 [InlineKeyboardButton('Cancel', callback_data='cancel')]])
            else:
                print('normal keyboard')
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Quit game', callback_data='quit')]])
            try:
                print('sending')
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard, parse_mode=telegram.ParseMode.MARKDOWN)
            except TelegramError:
                print('Failed to send message to', player_id)


def quit_room(bot, update):
    user_id = update.callback_query.from_user.id
    room_id = db.get_user_attribute(user_id, 'game_room')
    msg_id = update.callback_query.message.message_id
    players = db.quit_room(room_id, user_id)
    db.remove_user(user_id)
    msg = 'Successfully quit game room! Use /start to start or join a new game!'
    bot.edit_message_text(msg, user_id, msg_id, keyboard=None)
    msg = 'Game room ID: *%s*\n\n' % room_id
    if len(players) < 12:
        msg += 'Waiting for players...\n'
    else:
        msg += 'Room is at full capacity!\n'
    for i, player_id in enumerate(players):
        player_name = db.get_user_attribute(player_id, 'user_name')
        msg += '%d. %s\n' % (i + 1, player_name)
    msg = msg.strip()
    for player_id in players:
        msg_id = db.get_user_attribute(player_id, 'msg_id')
        if db.get_user_attribute(player_id, 'master'):
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Ready to Begin!', callback_data='begin')],
                                             [InlineKeyboardButton('Cancel', callback_data='cancel')]])
        else:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Quit game', callback_data='quit')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard, parse_mode=telegram.ParseMode.MARKDOWN)


def begin_game(bot, update):
    user_id = update.callback_query.from_user.id
    room_id = db.get_user_attribute(user_id, 'game_room')
    spies = db.get_room_attribute(room_id, 'spies')
    players = db.get_room_attribute(room_id, 'players')
    if spies > players:
        query_id = update.callback_query.id
        msg = 'Not enough players to start game.'
        bot.answer_callback_query(query_id, msg)
    else:
        location, roles = db.begin_game(room_id)
        for player_id, role in roles.items():
            if role == 'Spy':
                msg = 'You are the *SPY*!\n\n'
                msg += 'Your mission will be to figure out what the location is. Ask questions without revealing yourself as the spy.\n\n'
                msg += 'You can get the list of all possible locations using the /locations command.'
            else:
                msg = 'You are *NOT* the spy.\n\n'
                msg += 'Location: %s\nYour role: %s\n\n' % (location, role)
                msg += 'Answer questions from other players specifically from the perspective of your role. Try to figure out who the spy is!'
            is_master = db.get_user_attribute(player_id, 'master')
            if is_master:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Reveal all roles', callback_data='reveal')]])
            else:
                keyboard = None
            msg_id = db.get_user_attribute(player_id, 'msg_id')
            bot.edit_message_text(msg, player_id, msg_id, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=keyboard)


def reveal(bot, update):
    user_id = update.callback_query.from_user.id
    room_id = db.get_user_attribute(user_id, 'game_room')
    roles = db.get_room_attribute(room_id, 'roles')
    location = db.get_room_attribute(room_id, 'location')
    msg = 'Thank you for playing! Here\'s what happened in your last game:\n\n'
    msg += 'Location: %s\n' % location
    for player_id, role in roles.items():
        player_id = int(player_id)
        player_name = db.get_user_attribute(player_id, 'user_name')
        msg += '%s: %s\n' % (player_name, '*SPY*' if role == 'Spy' else role)
    for player_id in list(roles.keys()):
        player_id = int(player_id)
        msg_id = db.get_user_attribute(player_id, 'msg_id')
        bot.edit_message_text(msg, player_id, msg_id, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=None)
        db.remove_user(player_id)
    db.delete_room(room_id)


def get_locations(bot, update):
    user_id = update.message.from_user.id
    locations = json.load(open('locations.json'))
    locations = list(locations.keys())
    msg = ', '.join(locations)
    bot.send_message(user_id, msg)


def kick_player(bot, update):
    user_id = update.message.from_user.id
    is_master = db.get_user_attribute(user_id, 'master')
    if is_master is None:
        msg = 'You\'re not in any game. Use /start to start or join a new game.'
        keyboard = None
    elif not is_master:
        msg = 'Only game masters have access to this command!'
        keyboard = None
    else:
        room_id = db.get_user_attribute(user_id, 'game_room')
        players = db.get_room_attribute(room_id, 'roles')
        msg = 'Who do you want to kick?'
        keyboard = [[InlineKeyboardButton(db.get_user_attribute(player_id, 'user_name'), callback_data='kick_%d' % player_id)] for player_id in players]
        keyboard.append([InlineKeyboardButton('cancel', callback_data='cancel_kick')])
        keyboard = InlineKeyboardMarkup(keyboard)
    bot.send_message(user_id, msg, reply_markup=keyboard)


def cancel_kick(bot, update):
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    bot.delete_message(user_id, msg_id)


def kicked(bot, update):
    user_id = update.callback_query.from_user.id
    room_id = db.get_user_attribute(user_id, 'game_room')
    msg_id = update.callback_query.message.message_id
    kicked_id = int(update.callback_query.data.split('_')[1])
    if kicked_id == user_id:
        query_id = update.callback_query.id
        msg = 'You can\'t kick yourself out!'
        bot.answer_callback_query(query_id, msg)
    else:
        kicked_name = db.get_user_attribute(kicked_id, 'user_name')
        msg = 'Successfully kicked %s.' % kicked_name
        bot.edit_message_text(msg, user_id, msg_id)
        msg = 'Game master has kicked you out of the room. Use /start to start or join a new game!'
        kicked_msg_id = db.get_user_attribute(kicked_id, 'msg_id')
        bot.edit_message_text(msg, kicked_id, kicked_msg_id)
        players = db.quit_room(room_id, kicked_id)
        msg = 'Game room ID: *%s*\n\n' % room_id
        if len(players) < 12:
            msg += 'Waiting for players...\n'
        else:
            msg += 'Room is at full capacity!\n'
        for i, player_id in enumerate(players):
            player_name = db.get_user_attribute(player_id, 'user_name')
            msg += '%d. %s\n' % (i + 1, player_name)
        msg = msg.strip()
        for player_id in players:
            player_msg_id = db.get_user_attribute(player_id, 'msg_id')
            if db.get_user_attribute(player_id, 'master'):
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Start Game!', callback_data='begin')],
                                                 [InlineKeyboardButton('Cancel', callback_data='cancel')]])
            else:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Quit game', callback_data='quit')]])
            bot.edit_message_text(msg, user_id, player_msg_id, reply_markup=keyboard, parse_mode=telegram.ParseMode.MARKDOWN)
        sleep(2)
        bot.delete_message(user_id, msg_id)


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
    elif data == 'begin':
        begin_game(bot, update)
    elif data == 'quit':
        quit_room(bot, update)
    elif data == 'reveal':
        reveal(bot, update)
    elif data == 'cancel_kick':
        cancel_kick(bot, update)
    elif data.startswith('kick'):
        kicked(bot, update)
    else:
        query_id = update.callback_query.id
        bot.answer_callback_query(query_id, 'Function unavailable')


def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('locations', get_locations))
    dispatcher.add_handler(CommandHandler('kick', kick_player))
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
    db = Database(DATABASE_URL, reset=False)
    main()
