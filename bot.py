import spotipy
import spotipy.oauth2 as oauth2
import discord
import asyncio
import datetime
from database import DatabasePointer
from config import *
import re
import time

# Fetching code courtesy of ritiek https://github.com/plamere/spotipy/issues/246

class Spotty(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args,**kwargs)
		self.__fetch_task = self.loop.create_task(self.fetch_all())
		self.__delay = delay
		self.__master = master_id
		self._dbpointer = DatabasePointer(location=db_location)

	async def on_ready(self):
		print('We have logged in as {0.user}'.format(self))
		await discord_client.change_presence(activity=discord.Game(name="Spotify"))

	async def on_message(self, message):
		if message.author == self.user: return

		user_id = message.author.id
		username = message.author.name
		channel_id = message.channel.id
		channel_name = await self.get_channel_name(channel_id)

		if message.content.startswith("!tracking"):
			data = self._dbpointer.fetch_playlists_by_channel_id(channel_id)
			if len(data) == 0:
				return await message.channel.send("#{0} is not currently tracking any playlists.")
			string = "Channel is currently tracking:\n"
			for (id, name) in data:
				string += "%d - %s\n" % (id, name)
			await message.channel.send(string) 

		elif message.content.startswith("!track"):
			split = message.content.split(' ')
			if len(split) != 2:
				return await message.channel.send("Usage: !track <playlist-url>")
			playlist_id = await extract_playlist_id(split[1])
			playlist_name = await fetch_playlist_name(spotify_user_id, playlist_id)
			self._dbpointer.insert(username, user_id, playlist_id, playlist_name, channel_id, channel_name, get_current_time(as_string=True))
			await message.channel.send("#{0} is now tracking the playlist '{1}'".format(channel_name, playlist_name))

		elif message.content.startswith("!me"):
			if user_id != self.__master: return
			for row in self._dbpointer.fetch_by_user_id(user_id):
				await message.channel.send(row) 

		elif message.content.startswith("!stopall"):
			self._dbpointer.delete_all(user_id) 
			await message.channel.send('Removed all playlists you were tracking from the database.')

		elif message.content.startswith("!stop"):
			split = message.content.split(' ')
			if len(split) > 1:
				id = int(split[1])
				owner_id = int(self._dbpointer.get_user_id_for_unique_id(id)[0])
				if owner_id != user_id:
					return await message.channel.send("Hmmm you shouldn't do that :no_good:")
				name = self._dbpointer.fetch_name_by_unique_id(id)[0]
				self._dbpointer.delete_by_unique_id(id)
				return await message.channel.send("Stopped tracking '{0}'.".format(name)) 
			self._dbpointer.delete_by_channel_id(channel_id)
			await message.channel.send('#{0} has stopped tracking all playlists.'.format(channel_name))

		elif message.content.startswith("!delay"):
			if user_id != self.__master: return
			split = message.content.split(' ')
			if len(split) == 1:
				return await message.channel.send("**Current delay is %s**" % str(self.__delay))
			elif len(split) == 2:
				new_delay = int(split[1])
				self.__delay = new_delay
			else:
				await message.channel.send("**Usage: !delay or !delay <seconds>**")

	async def fetch(self, channel_id, playlist_id, playlist_name, last_checked):
		"""
		Perform a fetch for a single database entry
		:param channel_id: The channel id to post to
		:param playlist_id: The playlist id to search
		:param playlist_name: The playlist name for channels tracking multiple playlists
		:return: None
		"""
		channel = self.get_channel(channel_id)
		songs = await fetch_playlist(spotify_user_id, playlist_id, last_checked)
		print("Found {0} songs in '{1}'".format(len(songs), playlist_name))
		for song in songs:
			await channel.send("New track added to '{0}'. {1}".format(playlist_name, song))
		self._dbpointer.update_time(channel_id, playlist_id, get_current_time(as_string=True))
		return len(songs)
			
	async def fetch_all(self):
		"""
		Perform a fetch for all database entries
		:return: None
		"""
		await self.wait_until_ready()
		print("Fetching new songs")
		while not self.is_closed():
			data = self._dbpointer.fetch_tracking_data()
			for (playlist_id, playlist_name, channel_id, last_checked) in data:
				await self.fetch(int(channel_id),playlist_id,playlist_name, convert_time(last_checked))
			await asyncio.sleep(self.__delay)

	async def get_channel_name(self, channel_id):
		"""
		Get discord channel name from its id
		:param channel_id: The channel id as an int
		:return: The name of the channel
		"""
		return self.get_channel(channel_id).name

async def extract_playlist_id(string):
	"""
	Takes in a string and extracts the playlist id
	:param string: The spotify playlist URL or id
	:return: The id
	"""
	p = re.compile(r"(?<!=)[0-9a-zA-Z]{22}")
	result = p.findall(string)
	if len(result) > 0:
		return result[0]
	print('Invalid playlist id or url')

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


def get_current_time(as_string=False):
	"""
	Get the current time
	:param as_string: Whether to return a datetime or as a string (for the db)
	:return: The current time
	"""
	ret = new_time.localize(datetime.datetime.now()).astimezone(old_time)
	return ret.strftime('%Y-%m-%dT%H:%M:%SZ') if as_string else ret

async def fetch_playlist_name(username, playlist_id):
	"""
	Find the name of a spotify playlist by its id
	:return: The name of the playlist
	"""
	result = spotify.user_playlist(username, playlist_id)
	return result['name']

async def fetch_playlist(username, playlist_id, previous_date):
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id:
	:return: A list of URLs of the new songs
	"""
	results = spotify.user_playlist(username, playlist_id, fields='tracks,next,name')
	tracks = results['tracks']
	new_songs = []
	while True:
		for item in tracks['items']:
			track = item['track'] if 'track' in item else item
			try:
				track_url = track['external_urls']['spotify']
				if convert_time(item['added_at']) > previous_date:
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
