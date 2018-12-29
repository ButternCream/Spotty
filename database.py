import sqlite3
from sqlite3 import OperationalError

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
             username TEXT,
             user_id TEXT,
             playlist_id TEXT,
             playlist_name TEXT,
             channel_id TEXT,
             channel_name TEXT,
             last_checked TEXT,
             UNIQUE(playlist_id, channel_id)
             )""")

    def insert(self, username, user_id, playlist_id, playlist_name, channel_id, channel_name, last_checked):
        with self._connection:
            self._cursor.execute("""INSERT INTO playlists (username, user_id, playlist_id, playlist_name, channel_id, channel_name, last_checked) 
            VALUES (:username, :user_id, :playlist_id, :playlist_name, :channel_id, :channel_name, :last_checked)""",  
            {"username": username, "user_id": user_id, "playlist_id": playlist_id, "playlist_name":playlist_name, "channel_id": channel_id, 
            "channel_name": channel_name, "last_checked": last_checked})
        
    def update_time(self, channel_id, playlist_id, last_checked):
        with self._connection:
            self._cursor.execute("""
                    UPDATE playlists SET last_checked = :last_checked WHERE playlist_id = :pid AND channel_id = :channel_id
            """, {"last_checked": last_checked, "pid": playlist_id, "channel_id": channel_id})

    def delete_by_name(self, user_id, playlist_name):
        with self._connection:
            self._cursor.execute("DELETE FROM playlists WHERE user_id=:user_id AND playlist_name=:playlist_name",
            {"user_id": user_id, "playlist_name": playlist_name})

    def delete_all(self, user_id):
        with self._connection:
            self._cursor.execute("DELETE FROM playlists WHERE user_id=:user_id", {"user_id": user_id})
    
    def delete_by_channel_id(self, channel_id):
        with self._connection:
            self._cursor.execute("DELETE FROM playlists WHERE channel_id=:channel_id", {"channel_id": channel_id})

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
        self._cursor.execute("SELECT playlist_name FROM playlists WHERE channel_id=:id", {"id": id})
        return self._cursor.fetchall()