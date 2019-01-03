import os
import pytz

client_id = 'SPOTIFY_CLIENT_ID'
client_secret = 'SPOTIFY_SECRET'
spotty_token = 'BOT_TOKEN'

delay = 30
db_location = r'db/spotty.db' # Local db

spotify_user_id = 'your user id'

old_time = pytz.timezone("UTC") # Spotify's timestamps
new_time = pytz.timezone("America/Los_Angeles") # Your timezone