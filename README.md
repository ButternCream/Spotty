# Spotty
### The spotify music sharing bot

##### Spotty will fetch songs in the specified playlist every X seconds.
##### If it finds any new songs it will post it to the specified discord channel in the database

### What it looks like
![Image](https://i.imgur.com/JQADBCK.png)
![WithDB](https://i.imgur.com/nP1H8Sx.png)

### *Todo* :construction:
- Wait for spotify webhooks :worried:
- Exception handling for the database :heavy_check_mark: (kind of)
- Better permissions for things like !stop and !track :heavy_check_mark:
- Limit the channels in which !track can be called :x:
- !random :id: - Randomly pick a song from the specific playlist :x:
- !where - List the channels in the server that are tracking playlists :x:
- !tracking - returns the unique db id of an entry along with the playlist name :heavy_check_mark:
- !stop :id: - Stop tracking the specified playlist. Where id will be the specified unique id from !tracking :heavy_check_mark:
- !link :id: - Get the link of the specified playlist. id from !tracking :heavy_check_mark:
- more tbd

### Commands :exclamation:
```
!help - As you'd expect
!track <playlist-id or url> - Will post new songs added to the playlist in the discord channel you use this command in (see image above)
!tracking - List the names and ids of what the current channel is tracking
!stop <id> - Stop the current channel from tracking anything or a specific playlist if the id from !tracking is specified
!purgeme - Removes ALL of your tracking entries in the database
!link <id> - Get the link of a playlist you are tracking. Get id from !tracking
```

### How To Use :question:
1. Clone repo
2. pip install -r requirements.txt
3. Configure a config.py file (see below)
4. Add your bot to your server and make sure it has permission to send messages
5. Make a role called 'Spotty Admin'
6. Assign the role whoever you want to be able to use the !track command

To simply add the bot to your server just [click here](https://discordapp.com/oauth2/authorize?scope=bot&permissions=11392&client_id=519285781479555089)
Its currently just running on my raspberry pi but eventually I'll move it to a VPC
*Note: make sure it has permssion to send and read messages*

Until I figure out a better way of handling permissions, this is how it works so everyone cant !track

### My Config File
```python
import os
import pytz

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_SECRET')
spotty_token = os.getenv('SPOTTY_TOKEN')

delay = 20
db_location = r'db/spotty.db' # Local db

spotify_user_id = 'your user id'

old_time = pytz.timezone("UTC") # Spotify's timestamps
new_time = pytz.timezone("America/Los_Angeles") # Your timezone

```
