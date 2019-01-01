import sqlite3
from sqlite3 import OperationalError, IntegrityError

"""
Database class to manage the database and various operations
"""
class DatabasePointer(object):
    def __init__(self, location=':memory:'):
        self._filename = location
        self._connection = sqlite3.connect(self._filename)
        self._cursor = self._connection.cursor()
        self.__loc = location
        self.__create_table()

    def __repr__(self):
        return "DatabasePointer(location=%s) -> %s" % (self.__loc, self._filename)
    
    def __create_table(self):
        with self._connection:
            self._cursor.execute("""CREATE TABLE IF NOT EXISTS playlists (
             u_id INTEGER PRIMARY KEY,
             guild_name TEXT,
             guild_id TEXT,
             username TEXT,
             user_id TEXT,
             playlist_id TEXT,
             playlist_name TEXT,
             channel_id TEXT,
             channel_name TEXT,
             last_checked TEXT,
             UNIQUE(playlist_id, channel_id)
             )""")

    def insert(self, values):
        with self._connection:
            try:
                self._cursor.execute("""INSERT INTO playlists (guild_name, guild_id, username, user_id, playlist_id, playlist_name, channel_id, channel_name, last_checked) 
                VALUES (:guild_name, :guild_id, :username, :user_id, :playlist_id, :playlist_name, :channel_id, :channel_name, :last_checked)""", values)
            except IntegrityError as e:
                return False
        return True

        
    def update_time(self, values):
        with self._connection:
            self._cursor.execute("""
                    UPDATE playlists SET last_checked = :last_checked WHERE playlist_id = :pid AND channel_id = :channel_id
            """, values)

    def delete_by_name(self, values):
        with self._connection:
            self._cursor.execute("DELETE FROM playlists WHERE user_id=:user_id AND playlist_name=:playlist_name",
            values)

    def delete_all(self, values):
        with self._connection:
            self._cursor.execute("DELETE FROM playlists WHERE user_id=:user_id", values)
    
    def delete_by_channel_id(self, value):
        with self._connection:
            self._cursor.execute("DELETE FROM playlists WHERE channel_id=:channel_id", value)
            
    def delete_by_unique_id(self, value):
        with self._connection:
            self._cursor.execute("DELETE FROM playlists WHERE u_id=:u_id", value)

    """ Fetching """
    def fetch_all(self):
        self._cursor.execute("SELECT * FROM playlists")
        return self._cursor.fetchall()
    
    def fetch_tracking_data(self):
        self._cursor.execute("SELECT playlist_id, playlist_name, channel_id, last_checked FROM playlists")
        return self._cursor.fetchall()
    
    def fetch_by_playlist_id(self,id):
        self._cursor.execute("SELECT * FROM playlists WHERE playlist_id=:id", {"id": id})
        return self._cursor.fetchall()

    def fetch_by_user_id(self,user_id):
        self._cursor.execute("SELECT * FROM playlists WHERE user_id=:user_id", {"user_id": user_id})
        return self._cursor.fetchall()
    
    def fetch_playlists_by_channel_id(self,id):
        self._cursor.execute("SELECT u_id, playlist_name FROM playlists WHERE channel_id=:id", {"id": id})
        return self._cursor.fetchall()
    
    def fetch_name_by_unique_id(self,id):
        self._cursor.execute("SELECT playlist_name FROM playlists WHERE u_id=:id", {"id": id})
        return self._cursor.fetchone()
    
    def get_user_id_for_unique_id(self, u_id):
        self._cursor.execute("SELECT user_id FROM playlists WHERE u_id=:u_id", {"u_id": u_id})
        return self._cursor.fetchone()

    def get_playlist_id_by_unique_id(self, u_id):
        self._cursor.execute("SELECT playlist_id FROM playlists WHERE u_id=:u_id", {"u_id": u_id})
        return self._cursor.fetchone()

# TODO
class DatabseEntry(object):
    def __init__(self, **data):
        self.data = data
