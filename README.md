# Spotty
### The spotify music sharing bot

##### Spotty will fetch songs in the specified playlist every X seconds.
##### If it finds any new songs it will post it to the specified discord channel in the database

### What it looks like
![Image](https://i.imgur.com/JQADBCK.png)
![WithDB](https://i.imgur.com/nP1H8Sx.png)

### *Todo*
- ~~Instead of saving the entire playlist in a set :scream:, simply save the last time checked. Then filter the next fetch based on the previous time.~~
- Wait for spotify webhooks
- Exception handling for the database
- !tracking - returns the unique db id of an entry along with the playlist name :heavy_check_mark:
- !stop <id> - Stop tracking the specified playlist. Where id will be the specified unique id from !tracking :heavy_check_mark:
- !random <id> - Randomly pick a song from the specific playlist
- more tbd

### Commands
```
!track <playlist-id or url> - Will post new songs added to the playlist in the discord channel you use this command in (see image above)
!tracking - List the names of what the current channel is tracking
!me - print out database entries associated with your discord id (master_id in config.py) (debugging purposes)
!stop <id> - Stop the current channel from tracking anything or a specific playlist if the id from !tracking is specified
!stopall - Removes ALL of your tracking entries in the database
!delay <new-delay> - Sets or returns the delay between fetches (in seconds). <new-delay> is optional
```

### My Config File
```python
import os
import pytz

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_SECRET')
spotty_token = os.getenv('SPOTTY_TOKEN')

delay = 20
master_id = your discord id
db_location = r'db/spotty.db' # Local db

spotify_user_id = 'your user id'

old_time = pytz.timezone("UTC") # Spotify's timestamps
new_time = pytz.timezone("America/Los_Angeles") # Your timezone

```
