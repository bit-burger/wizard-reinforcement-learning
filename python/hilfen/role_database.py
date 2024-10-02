import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='database.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.initialize_database()

    def initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                name  TEXT PRIMARY KEY,
                color TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag_members (
                dc_userid INT,
                tag_name  TEXT REFERENCES tags (name) ON DELETE CASCADE,
                PRIMARY KEY (dc_userid, tag_name)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                name      TEXT PRIMARY KEY,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.connection.commit()

    def insert_tag(self, tag_name:str, color:str, members:list[int]):
        try:
            self.cursor.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (tag_name, color))
            if members:
                for member in members:
                    self.cursor.execute('INSERT INTO tag_members (dc_userid, tag_name) VALUES (?, ?)', (member, tag_name))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting tag: {e}")

    def delete_tag(self, tag_name:str):
        self.cursor.execute('DELETE FROM tags WHERE name = ?', (tag_name,))
        self.connection.commit()

    def insert_role(self, role_name:str):
        try:
            self.cursor.execute('INSERT INTO roles (name) VALUES (?)', (role_name,))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting role: {e}")

    def delete_role(self, role_name:str):
        self.cursor.execute('DELETE FROM roles WHERE name = ?', (role_name,))
        self.connection.commit()

    def update_role_last_used(self, role_name:str):
        current_time = datetime.now()
        self.cursor.execute('UPDATE roles SET last_used = ? WHERE name = ?', (current_time, role_name))
        self.connection.commit()

    def close(self):
        self.connection.close()