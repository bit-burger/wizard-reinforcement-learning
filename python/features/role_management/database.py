import sqlite3
from datetime import datetime
import discord


"""
Klasse für die Verwaltung von Discord-Rollen und Tags in einer SQLite-Datenbank.

Attribute:
- connection: SQLite-Verbindung zur Datenbank.
- cursor: SQLite-Cursor zum Ausführen von SQL-Befehlen.

Methoden:
- insert_tag(tag_name, color, members): Fügt einen neuen Tag mit einer bestimmten Farbe und einer Liste von Mitgliedern hinzu.
- delete_tag(tag_name): Löscht einen Tag basierend auf seinem Namen.
- get_tag(tag_name): Gibt Informationen über einen bestimmten Tag zurück.
- get_tags(): Gibt eine Liste aller Tags zurück.
- get_members_by_tag(tag_name): Gibt eine Liste von Mitgliedern (Discord-User-IDs) zurück, die zu einem bestimmten Tag gehören.
- insert_role(role_name): Fügt eine neue Rolle in die Datenbank ein.
- delete_role(role_name): Löscht eine Rolle basierend auf ihrem Namen aus der Datenbank.
- update_role_last_used(role_name): Aktualisiert den Zeitstempel, wann eine Rolle zuletzt verwendet wurde.
- get_last_used_role(): Gibt die am längsten nicht verwendete Rolle zurück.
- close(): Schließt die Verbindung zur Datenbank.
"""
class Database:
    def __init__(self, guild: discord.Guild=None):
        self.connection = sqlite3.connect('roles.db')
        self.cursor = self.connection.cursor()
        self.initialize_database()
        self.sync_roles(guild)

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

    def sync_roles(self, guild: discord.Guild=None):
        dc_roles = {role.name: role for role in guild.roles}
        self.cursor.execute('SELECT name FROM roles')
        db_roles = [row[0] for row in self.cursor.fetchall()]
        for role_name in dc_roles:
            if role_name not in db_roles:
                self.insert_role(role_name)
        for role_name in db_roles:
            if role_name not in dc_roles:
                self.delete_role(role_name)

    def insert_tag(self, tag_name: str, color: str, members: list[int]):
        try:
            self.cursor.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (tag_name, color))
            if members:
                for member in members:
                    self.cursor.execute('INSERT INTO tag_members (dc_userid, tag_name) VALUES (?, ?)',
                                        (member, tag_name))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting tag: {e}")

    def delete_tag(self, tag_name: str):
        self.cursor.execute('DELETE FROM tags WHERE name = ?', (tag_name,))
        self.connection.commit()

    def get_tag(self, tag_name: str):
        self.cursor.execute('SELECT * FROM tags WHERE name = ?', (tag_name,))
        return self.cursor.fetchone()

    def get_tags(self):
        self.cursor.execute('SELECT * FROM tags')
        return self.cursor.fetchall()

    def get_members_by_tag(self, tag_name: str):
        self.cursor.execute('SELECT dc_userid FROM tag_members WHERE tag_name = ?', (tag_name,))
        return self.cursor.fetchall()

    def insert_role(self, role_name: str):
        try:
            self.cursor.execute('INSERT INTO roles (name) VALUES (?)', (role_name,))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting role: {e}")

    def delete_role(self, role_name: str):
        self.cursor.execute('DELETE FROM roles WHERE name = ?', (role_name,))
        self.connection.commit()

    def update_role_last_used(self, role_name: str):
        current_time = datetime.now()
        self.cursor.execute('UPDATE roles SET last_used = ? WHERE name = ?', (current_time, role_name))
        self.connection.commit()

    def get_last_used_role(self):
        self.cursor.execute('SELECT name FROM roles ORDER BY last_used LIMIT 1')
        return self.cursor.fetchone()

    def close(self):
        self.connection.close()
