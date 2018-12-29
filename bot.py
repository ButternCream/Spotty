import spotipy
import spotipy.oauth2 as oauth2
import discord
from discord.ext import commands
import asyncio
import datetime
from database import DatabasePointer
from config import *
import re
import time

# Fetching code courtesy of ritiek https://github.com/plamere/spotipy/issues/246

class Spotty(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix='!')
		self.__fetch_task = self.loop.create_task(self.fetch_all())
		self.__delay = delay
		self._dbpointer = DatabasePointer(location=db_location)
		self.register_commands()

	def register_commands(self):
		self.add_command(self.tracking)
		self.add_command(self.track)
		self.add_command(self.me)
		self.add_command(self.stopall)
		self.add_command(self.stop)
		self.add_command(self.link)

	@commands.command()
	async def link(self, ctx):
		message = ctx.message
		split = message.content.split(' ')
		if len(split) != 2:
			return await ctx.send(bold("Usage: !link <id>"))
		id = self._dbpointer.get_playlist_id_by_unique_id(split[1])[0]
		url = await fetch_playlist_link(spotify_user_id, id)
		await ctx.send(url)

	@commands.command()
	async def tracking(self, ctx):
		message = ctx.message
		channel_id = message.channel.id
		channel_name = await self.get_channel_name(channel_id)

		data = self._dbpointer.fetch_playlists_by_channel_id(channel_id)
		if len(data) == 0:
			return await ctx.send(bold("#{0} is not currently tracking any playlists.".format(channel_name)))
		string = "Channel is currently tracking:\n"
		for (id, name) in data:
			string += "'%s' - ID: %d\n" % (name, id)
		await ctx.send(string) 

	@commands.command()
	async def track(self, ctx):
		message = ctx.message

		roles = [role.name.lower() for role in message.author.roles]
		user_id = message.author.id
		username = message.author.name
		channel_id = message.channel.id
		channel_name = await self.get_channel_name(channel_id)

		split = message.content.split(' ')
		if len(split) != 2:
			return await ctx.send(bold("Usage: !track <playlist-url>"))
		if 'spotty admin' not in roles: return await warn_user(message.channel)
		playlist_id = await extract_playlist_id(split[1])
		playlist_name = await fetch_playlist_name(spotify_user_id, playlist_id)
		self._dbpointer.insert(username, user_id, playlist_id, playlist_name, channel_id, channel_name, get_current_time(as_string=True))
		await ctx.send(bold("#{0} is now tracking the playlist '{1}'".format(channel_name, playlist_name)))

	@commands.command()
	@commands.is_owner()
	async def me(self, ctx):
		message = ctx.message
		user_id = message.author.id
		for row in self._dbpointer.fetch_by_user_id(user_id):
			await ctx.send(row) 

	@commands.command()
	async def stopall(self, ctx):
		message = ctx.message
		user_id = message.author.id
		if 'spotty admin' not in roles: return await warn_user(message.channel)
		self._dbpointer.delete_all(user_id) 
		await ctx.send(bold('Removed all playlists you were tracking from the database.'))

	@commands.command()
	async def stop(self, ctx):
		message = ctx.message
		roles = [role.name.lower() for role in message.author.roles]
		user_id = message.author.id
		channel_id = message.channel.id
		channel_name = await self.get_channel_name(channel_id)

		if 'spotty admin' not in roles: return await warn_user(message.channel)
		split = message.content.split(' ')
		if len(split) > 1:
			id = int(split[1])
			owner_id = int(self._dbpointer.get_user_id_for_unique_id(id)[0])
			if owner_id != user_id:
				return await ctx.send("Hmmm you shouldn't do that :no_good:")
			name = self._dbpointer.fetch_name_by_unique_id(id)[0]
			self._dbpointer.delete_by_unique_id(id)
			return await ctx.send(bold("#{1} has stopped tracking '{0}'.".format(name, channel_name))) 
		self._dbpointer.delete_by_channel_id(channel_id)
		await ctx.send(bold('#{0} has stopped tracking all playlists.'.format(channel_name)))

	async def on_ready(self):
		print('We have logged in as {0.user}'.format(self))
		await discord_client.change_presence(activity=discord.Game(name="Spotify"))

	async def on_message(self, message):
		await self.process_commands(message)

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
	

def bold(string):
	return '**'+string+'**'

async def warn_user(channel):
	await channel.send("Hmmm you shouldn't do that :no_good:")

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

async def fetch_playlist_link(username, playlist_id):
	result = spotify.user_playlist(username, playlist_id)
	return result['external_urls']['spotify']

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
