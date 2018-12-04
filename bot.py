import spotipy
import spotipy.oauth2 as oauth2
import discord
import asyncio
import datetime
from config import *

# Fetching code courtesy of ritiek https://github.com/plamere/spotipy/issues/246 

PREVIOUS_DATE = new_time.localize(datetime.datetime.now()).astimezone(old_time)

class Spotty(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args,**kwargs)
		self.test_channel_id = test_channel # Testing Channel
		self.spotty_channel_id = music_channel # Music Channel
		self.fetch_task = self.loop.create_task(self.fetch())


	async def on_ready(self):
		print('We have logged in as {0.user}'.format(self))
		await discord_client.change_presence(activity=discord.Game(name="Spotify"))

	async def fetch(self):
		await self.wait_until_ready()
		channel = self.get_channel(self.spotty_channel_id)
		while not self.is_closed():
			songs = await fetch_playlist(spotify_user_id, spotify_playlist_id)
			for song in songs:
				await channel.send(song)
			set_current_time()
			await asyncio.sleep(7200)  # Sleep 2 hours, spotify doesnt have webhooks yet :(

def generate_token():
	""" Generate the token. """
	credentials = oauth2.SpotifyClientCredentials(
		client_id=client_id,
		client_secret=client_secret)
	token = credentials.get_access_token()
	return token


def set_current_time():
	"""
	Resets the time after a fetch
	:return: None
	"""
	global PREVIOUS_DATE
	PREVIOUS_DATE = new_time.localize(datetime.datetime.now()).astimezone(old_time)

async def fetch_playlist(username, playlist_id):
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id:
	:return: A list of URLs of the new songs
	"""
	print('Fetching new songs')
	results = spotify.user_playlist(username, playlist_id,
									fields='tracks,next,name')
	tracks = results['tracks']
	new_songs = []
	while True:
		for item in tracks['items']:
			if 'track' in item:
				track = item['track']
			else:
				track = item
			try:
				track_url = track['external_urls']['spotify']
				#track_name = u'{0} by {1}'.format(track['name'], track['artists'][0]['name']
				added_at = datetime.datetime.strptime(item['added_at'], '%Y-%m-%dT%H:%M:%SZ')
				if pytz.UTC.localize(added_at) > PREVIOUS_DATE:
					new_songs.append(track_url)
			except (KeyError, UnicodeEncodeError) as e:
				print(u'Skipping track {0} by {1} (local only?)'.format(
					track['name'], track['artists'][0]['name']))
		# 1 page = 50 results
		# check if there are more pages
		if tracks['next']:
			tracks = spotify.next(tracks)
		else:
			break
	return new_songs


if __name__ == '__main__':
	discord_client = Spotty()
	token = generate_token()
	spotify = spotipy.Spotify(auth=token)
	discord_client.run(spotty_token)
