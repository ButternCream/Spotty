import spotipy
import spotipy.oauth2 as oauth2
import discord
from discord.ext import commands
import asyncio
import datetime
from database import DatabasePointer, DatabseEntry
from config import *
import re
import time
import logging
from utils import handle_errors
logging.basicConfig(filename=r'spotty.log', filemode='w', level=logging.ERROR, format=' %(asctime)s - %(levelname)s - %(message)s')

# Spotify fetching code courtesy of ritiek https://github.com/plamere/spotipy/issues/246

# discord.abc.GuildChannel -> category [CategoryChannel]
# discord.CategoryChannel -> name, channels
# https://discordapp.com/oauth2/authorize?scope=bot&permissions=66321471&client_id=<bot-id> (optional)&guild_id=<server-id> Example on how to add with all perms

class Spotty(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix='!')
		self.__fetch_task = self.loop.create_task(self.fetch_all())
		self.__delay = delay
		self._dbpointer = DatabasePointer(location=db_location)
		self.register_commands()

	def register_commands(self):
		self.add_command(self.test)
		self.add_command(self.tracking)
		self.add_command(self.track)
		self.add_command(self.me)
		self.add_command(self.purgeme)
		self.add_command(self.stop)
		self.add_command(self.link)

	""" Owner Only Commands """

	@commands.command()
	@commands.is_owner()
	async def test(self, ctx):
		""" This is a test command """
		message = ctx.message
		await ctx.send(message.author, "Hi")
		guild = message.guild
		channels = guild.channels
		categories = {channel.category.name if channel.category else None for channel in channels}
		roles = guild.roles
		members = some_role.members
		music_channels = list()
		for channel in channels:
			if channel.category is None: continue
			if channel.category.name == 'Music':
				music_channels.append(channel.name)
		logging.info(guild.name)
		logging.info(categories)
		logging.info(music_channels)

	@commands.command()
	@commands.is_owner()
	async def me(self, ctx):
		""" Get database entries associated with you """
		user_id = ctx.author.id
		for row in self._dbpointer.fetch_by_user_id(user_id):
			await ctx.send(row) 

	@commands.command()
	@commands.is_owner()
	async def delay(self, ctx):
		"""
		Usage: !delay <seconds> or !delay
		Sets the delay
		"""
		split = ctx.message.content.split(' ')
		if len(split) == 1:
			return await ctx.send("Current delay is %s" % str(self.__delay))
		elif len(split) == 2:
			new_delay = int(split[1])
			self.__delay = new_delay
		else:
			await ctx.send("Usage: !delay or !delay <seconds>")

	""" Everyone Commands """

	@commands.command()
	@commands.guild_only()
	async def link(self, ctx):
		""" 
		Usage: !link <id>
		Gets the link of the specified playlist id 
		"""
		split = ctx.message.content.split(' ')
		if len(split) != 2:
			return await ctx.send("Usage: !link <id>")
		id = self._dbpointer.get_playlist_id_by_unique_id(split[1])[0]
		url = await fetch_playlist_link(spotify_user_id, id)
		await ctx.send(url)

	@commands.command()
	@commands.guild_only()
	async def tracking(self, ctx):
		""" 
		Usage: !tracking
		Shows what the current channel is tracking. <playlist-name> - <id>
		"""
		channel_id = ctx.channel.id
		channel_name = ctx.channel.name

		data = self._dbpointer.fetch_playlists_by_channel_id(channel_id)
		if len(data) == 0:
			return await ctx.send("#{0} is not currently tracking any playlists.".format(channel_name))
		string = "Channel is currently tracking:\n"
		for (id, name) in data:
			string += "'%s' - ID: %d\n" % (name, id)
		await ctx.send(string) 

	""" Admin Commands """

	@commands.command()
	@commands.guild_only()
	@commands.has_role("Spotty Admin")
	async def track(self, ctx):
		""" 
		Usage: !track <playlist-id or link> 
		Tracks the specified playlist in the channel its called in 
		"""
		roles = [role.name.lower() for role in ctx.author.roles]
		user_id = ctx.author.id
		username = ctx.author.name
		channel_id = ctx.channel.id
		channel_name = ctx.channel.name
		guild_name = ctx.guild.name
		guild_id = ctx.guild.id

		split = ctx.message.content.split(' ')
		if len(split) != 2:
			return await ctx.send("Usage: !track <playlist-url>")
		playlist_id = await extract_playlist_id(split[1])
		playlist_name = await fetch_playlist_name(spotify_user_id, playlist_id)
		if not self._dbpointer.insert(guild_name, guild_id, username, user_id, playlist_id, playlist_name, channel_id, channel_name, get_current_time(as_string=True)):
			return await ctx.send("The channel #{0} already tracking {1}?".format(channel_name, playlist_name))
		await ctx.send("#{0} is now tracking the playlist '{1}'".format(channel_name, playlist_name))

	@commands.command()
	@commands.guild_only()
	@commands.has_role("Spotty Admin")
	async def purgeme(self, ctx):
		""" 
		Usage: !purgeme
		Removes ALL database entries associated with you. 
		This will remove everything, i.e anywhere (can be other servers and channels) you called !track
		If you want to stop a single channel from tracking use !stop
		"""
		roles = [role.name.lower() for role in ctx.author.roles]
		user_id = ctx.author.id
		self._dbpointer.delete_all(user_id) 
		await ctx.send('Removed all playlists you were tracking from the database.')

	@commands.command()
	@commands.guild_only()
	@commands.has_role("Spotty Admin")
	async def stop(self, ctx):
		""" 
		Usage: !stop <(optional) id> 
		Stops tracking the specified playlist or stops tracking all playlists in a channel 
		"""
		roles = [role.name.lower() for role in ctx.author.roles]
		user_id = ctx.author.id
		channel_id = ctx.channel.id
		channel_name = ctx.channel.name

		split = ctx.message.content.split(' ')
		if len(split) > 1:
			id = int(split[1])
			owner_id = int(self._dbpointer.get_user_id_for_unique_id(id)[0])
			if owner_id != user_id:
				return await ctx.send("Hmmm you shouldn't do that :no_good:")
			name = self._dbpointer.fetch_name_by_unique_id(id)[0]
			self._dbpointer.delete_by_unique_id(id)
			return await ctx.send("#{1} has stopped tracking '{0}'.".format(name, channel_name))
		self._dbpointer.delete_by_channel_id(channel_id)
		await ctx.send('#{0} has stopped tracking all playlists.'.format(channel_name))

	""" Coroutine Fetch Functions """

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
		logging.info("Found {0} songs in '{1}'".format(len(songs), playlist_name))
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

	""" Overrides """

	async def on_ready(self):
		logging.info('We have logged in as {0.user}'.format(self))
		print('We have logged in as {0.user}'.format(self))
		await discord_client.change_presence(activity=discord.Game(name="Spotify"))

	async def on_message(self, message):
		await self.process_commands(message)


	""" Error Handling """
	@handle_errors(track.error, purgeme.error, stop.error)
	async def perm_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send("Sorry you cant do that :no_good:")

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
	logging.info('Invalid playlist id or url')

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
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id: The playlist id
	:return: The URL of the playlist
	"""
	result = spotify.user_playlist(username, playlist_id)
	return result['external_urls']['spotify']

async def fetch_playlist(username, playlist_id, previous_date):
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id: The playlist id
	:param previous_date: The last time fetched
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
				logging.info(u'Skipping track {0} by {1} (local only?)'.format(
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
	logging.info("Started spotty")
