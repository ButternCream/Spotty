# Spotty
##### *The spotify music sharing bot*

##### Spotty will fetch songs in the specified playlist every X seconds.
##### If it finds any new songs it will post it to the specified discord channel

###What it looks like
![Image](https://i.imgur.com/JQADBCK.png)

###*Todo*
- Instead of saving the entire playlist in a set :scream:, simply save the last time checked. Then filter the next fetch based on the previous time.
- Wait for spotify webhooks

### My Config File
```python
import os

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_SECRET')
spotty_token = os.getenv('SPOTTY_TOKEN') # Bot token

test_channel = # A testing channel I used
music_channel = # The channel id for the bot i.e # 12345...

spotify_user_id = 'some_user_id'
spotify_playlist_id = 'some_playlist_id'
```