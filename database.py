import os
import psycopg2
import json
from datetime import datetime as dt


class Database:
    def __init__(self, reset=False):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
        self.cursor = self.conn.cursor()
        if reset:
            self.drop_table('users')
            self.drop_table('game')
        stmt = "CREATE TABLE IF NOT EXISTS users (user_id BIGINT NOT NULL, user_name TEXT NOT NULL, game_room TEXT NOT NULL, master BIT NOT NULL, msg_id BIGINT NOT NULL)"
        self.commit(stmt)
        stmt = "CREATE TABLE IF NOT EXISTS game (room_id TEXT NOT NULL, game_info TEXT NOT NULL, state TEXT NOT NULL, players TEXT NOT NULL)"
        self.commit(stmt)

    # Low-level functions
    def commit(self, stmt):
        self.cursor.execute(stmt)
        self.conn.commit()

    def fetch(self, stmt):
        self.cursor.execute(stmt)
        rows = self.cursor.fetchall()
        return rows

    # Table functions
    def drop_table(self, table_name):
        stmt = "DROP TABLE IF EXISTS %s" % table_name
        self.commit(stmt)

    # User functions
    def get_users(self):
        stmt = "SELECT user_id FROM users"
        rows = self.fetch(stmt)
        return [row[0] for row in rows]

    def add_user(self, user_id, user_name, game_room, master, msg_id):
        stmt = "INSERT INTO users VALUES (%d, '%s', '%s', %d, %d)" % (user_id, user_name, game_room, master, msg_id)
        self.commit(stmt)

    def remove_user(self, user_id):
        stmt = "DELETE FROM users WHERE user_id = %d" % user_id
        self.commit(stmt)

    def get_user_attribute(self, user_id, attribute):
        if attribute == 'all':
            attribute = '*'
        stmt = "SELECT %s FROM users WHERE user_id = %d" % (attribute, user_id)
        rows = self.fetch(stmt)
        if attribute == '*':
            return rows
        elif rows[0]:
            return rows[0][0]
        else:
            return None

    def update_user_attribute(self, user_id, attribute, new_value):
        if attribute == 'user_name' or attribute == 'game_room':
            new_value = "'%s'" % new_value
        else:
            new_value = str(new_value)
        stmt = "UPDATE users SET %s = %s WHERE user_id = %d" % (attribute, new_value, user_id)
        self.commit(stmt)

    # Game room functions


def main():
    db = Database()
    db.drop_table('users')
    db.drop_table('games')


if __name__ == '__main__':
    main()
