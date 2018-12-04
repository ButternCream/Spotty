import spotipy
import spotipy.oauth2 as oauth2
import discord
import asyncio
import datetime
from config import *

# Fetching code courtesy of ritiek https://github.com/plamere/spotipy/issues/246

class Spotty(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args,**kwargs)
		self.test_channel_id = test_channel # Testing Channel
		self.spotty_channel_id = music_channel # Music Channel
		self.fetch_task = self.loop.create_task(self.fetch())
		self.delay = delay

	async def on_ready(self):
		print('We have logged in as {0.user}'.format(self))
		await discord_client.change_presence(activity=discord.Game(name="Spotify"))

	async def fetch(self):
		global PREVIOUS_DATE
		await self.wait_until_ready()
		channel = self.get_channel(self.test_channel_id)
		while not self.is_closed():
			songs = await fetch_playlist(spotify_user_id, spotify_playlist_id)
			print("Found {0} songs".format(len(songs)))
			for song in songs:
				await channel.send(song)
			PREVIOUS_DATE = get_current_time()
			await asyncio.sleep(self.delay)  # Sleep 2 hours, spotify doesnt have webhooks yet :(

def convert_time(time_string):
	"""
	Takes time as a string and converts it to an aware datetime
	:param time_string: Time in the form %Y-%m-%dT%H:%M:%SZ
	:return: An aware datetime
	"""
	added_at = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
	return pytz.UTC.localize(added_at)

def generate_token():
	""" Generate the token for Spotify. """
	credentials = oauth2.SpotifyClientCredentials(
		client_id=client_id,
		client_secret=client_secret)
	token = credentials.get_access_token()
	return token


def get_current_time():
	"""
	Get the current time
	:return: current time
	"""
	return new_time.localize(datetime.datetime.now()).astimezone(old_time)

async def fetch_playlist(username, playlist_id):
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id:
	:return: A list of URLs of the new songs
	"""
	print('Fetching new songs')
	results = spotify.user_playlist(username, playlist_id, fields='tracks,next,name')
	tracks = results['tracks']
	new_songs = []
	while True:
		for item in tracks['items']:
			track = item['track'] if 'track' in item else item
			try:
				track_url = track['external_urls']['spotify']
				if convert_time(item['added_at']) > PREVIOUS_DATE:
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
	PREVIOUS_DATE = get_current_time()
	discord_client.run(spotty_token)
