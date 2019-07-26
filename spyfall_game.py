import os
import telegram
from telegram.ext import Updater
from database import Database


def respond(user_id, msg, mode):
    pass


def main():
    updater = Updater(TOKEN)

    if MODE == 'dev':
        updater.start_polling()
    elif MODE == 'prod':
        updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
        updater.bot.set_webhook("https://spyfall-sg-telegram.herokuapp.com/" + TOKEN)
    else:
        print('MODE NOT VALID')
        exit()


if __name__ == '__main__':
    MODE = os.getenv("MODE")
    TOKEN = os.getenv("TOKEN")
    PORT = int(os.getenv("PORT"))
    db = Database()
    main()
