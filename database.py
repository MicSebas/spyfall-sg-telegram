import os
import psycopg2
import json
from datetime import datetime as dt
import random
import string

chars = string.ascii_uppercase + string.digits


def generate_random_string(length=6):
    return ''.join([random.choice(chars) for _ in range(length)])


def string_to_json(s):
    return json.loads(s)


def json_to_string(d):
    return json.dumps(d)


class Database:
    def __init__(self, url=None, reset=False):
        if url is not None:
            self.conn = psycopg2.connect(url, sslmode='require')
        else:
            self.conn = psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')
        self.cursor = self.conn.cursor()
        if reset:
            self.drop_table('users')
            self.drop_table('games')
        stmt = "CREATE TABLE IF NOT EXISTS users (user_id BIGINT NOT NULL, user_name TEXT NOT NULL, game_room TEXT NOT NULL, master INT NOT NULL, msg_id BIGINT NOT NULL)"
        self.commit(stmt)
        stmt = "CREATE TABLE IF NOT EXISTS games (room_id TEXT NOT NULL, master_id BIGINT NOT NULL, master_name TEXT NOT NULL, spies BIGINT NOT NULL, players BIGINT NOT NULL, location TEXT NOT NULL, roles TEXT NOT NULL)"
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
    # user_id, user_name, game_room, master, msg_id
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
    # room_id, master_id, master_name, spies, players, location, roles
    def get_rooms(self):
        stmt = "SELECT room_id FROM games WHERE players < 12"
        rows = self.fetch(stmt)
        return [row[0] for row in rows]

    def init_room(self, master_id, master_name, spies):
        room_id = generate_random_string()
        existing_rooms = self.get_rooms()
        while room_id in existing_rooms:
            room_id = generate_random_string()
        players = 1
        location = 'init'
        roles = [master_id]
        roles = json_to_string(roles)
        stmt = "INSERT INTO games VALUES ('%s', %d, '%s', %d, %d, '%s', '%s')" % (room_id, master_id, master_name, spies, players, location, roles)
        self.commit(stmt)
        return room_id

    def delete_room(self, room_id):
        stmt = "DELETE FROM games WHERE room_id = '%s'" % room_id
        self.commit(stmt)

    def get_room_attribute(self, room_id, attribute):
        if attribute == 'all':
            attribute = '*'
        stmt = "SELECT %s FROM games WHERE room_id = '%s'" % (attribute, room_id)
        rows = self.fetch(stmt)
        if attribute == '*':
            return rows
        elif rows[0]:
            a = rows[0][0]
            if attribute == 'roles':
                a = string_to_json(a)
            return a
        else:
            return None

    def join_room(self, room_id, user_id):
        roles = self.get_room_attribute(room_id, 'roles')
        current_players = self.get_room_attribute(room_id, 'players')
        new_players = current_players + 1
        roles.append(user_id)
        roles = json_to_string(roles)
        stmt = "UPDATE games SET players = %d WHERE room_id = '%s'" % (new_players, room_id)
        self.commit(stmt)
        stmt = "UPDATE games SET roles = '%s' WHERE room_id = '%s'" % (roles, room_id)
        self.commit(stmt)


def main():
    db = Database()
    print(db.get_rooms())
    print(db.get_users())
    print(db.get_room_attribute('KEX15L', '*'))


if __name__ == '__main__':
    main()
