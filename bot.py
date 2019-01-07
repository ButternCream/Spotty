import spotipy
import spotipy.oauth2 as oauth2
import discord
from discord.ext import commands
import asyncio
import datetime
import re
import time
import logging
from pprint import pprint
from random import randint
from utils.decorators import Decorators
from utils.database import DatabasePointer
from utils.config import *


logging.basicConfig(filename=r'spotty.log', filemode='w', level=logging.WARNING,
					format=' %(asctime)s - %(levelname)s - %(message)s')

# Spotify fetching code courtesy of ritiek https://github.com/plamere/spotipy/issues/246

# https://discordapp.com/oauth2/authorize?scope=bot&permissions=66321471&client_id=<bot-id> (optional)&guild_id=<server-id> Example on how to add with all perms


class Spotty(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix=('!', '$', '(', ')', ';', '?', '.'))
		self.__fetch_task = self.loop.create_task(self.fetch_all())
		self.__delay = delay
		self._dbpointer = DatabasePointer()
		self.register_commands()

	def register_commands(self):
		self.add_command(self.test)
		self.add_command(self.tracking)
		self.add_command(self.track)
		self.add_command(self.me)
		self.add_command(self.db)
		self.add_command(self.purgeme)
		self.add_command(self.stop)
		self.add_command(self.link)
		self.add_command(self.delay)
		self.add_command(self.random)

	""" Owner Only Commands """

	@commands.command()
	@commands.is_owner()
	@Decorators.pm_only()
	async def test(self, ctx):
		""" This is a test command """
		await ctx.send("Testing")

	@commands.command()
	@commands.is_owner()
	@Decorators.pm_only()
	async def me(self, ctx):
		""" Get database entries associated with you """
		user_id = ctx.author.id
		for row in self._dbpointer.fetch_by_user_id(user_id):
			await ctx.send(row)

	@commands.command()
	@commands.is_owner()
	@Decorators.pm_only()
	async def db(self, ctx):
		for row in self._dbpointer.fetch_all():
			await ctx.send(row)

	@commands.command()
	@commands.is_owner()
	@Decorators.pm_only()
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
		await ctx.send('<' + url + '>')

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
		embed_msg = await self.tracking_embed(data)
		await ctx.send(embed=embed_msg)

	""" Admin Commands """

	@commands.command()
	@commands.guild_only()
	@Decorators.guild_owner_or_spotty_role()
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
		if len(split) < 2:
			return await ctx.send("Usage: !track <playlist-urls>")
		urls = split[1:]
		data_list = list()
		for url in urls:
			playlist_id = await extract_playlist_id(url)
			if playlist_id is None:
				continue
			playlist_name = await fetch_playlist_name(spotify_user_id, playlist_id)
			values = {
				"guild_name": guild_name,
				"guild_id": guild_id,
				"username": username,
				"user_id": user_id,
				"playlist_id": playlist_id,
				"playlist_name": playlist_name,
				"channel_id": channel_id,
				"channel_name": channel_name,
				"last_checked": get_current_time(as_string=True)
			}
			
			if self._dbpointer.insert(values):
				data_list.append(values)
		if len(data_list) < 1:
			return
		embed_msg = await self.track_embed(data_list)
		await ctx.send(embed=embed_msg)

	@commands.command()
	@commands.guild_only()
	@Decorators.guild_owner_or_spotty_role()
	async def purgeme(self, ctx):
		""" 
		Usage: !purgeme
		Removes ALL database entries associated with you. 
		This will remove everything, i.e anywhere (can be other servers and channels) you called !track
		If you want to stop a single channel from tracking use !stop
		"""
		roles = [role.name.lower() for role in ctx.author.roles]
		user_id = ctx.author.id

		values = {
			"user_id": user_id
		}

		self._dbpointer.delete_all(values)
		await ctx.send('Removed all playlists you were tracking from the database.')

	@commands.command()
	@commands.guild_only()
	@Decorators.guild_owner_or_spotty_role()
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
			self._dbpointer.delete_by_unique_id({"u_id": id})
			embed_msg = await self.deleted_notify_embed(name=name)
			return await ctx.send(embed=embed_msg)
		self._dbpointer.delete_by_channel_id({"channel_id": channel_id})
		embed_msg = await self.deleted_notify_embed()
		await ctx.send(embed=embed_msg)

	@commands.command()
	@commands.guild_only()
	async def random(self, ctx):
		"""
		Usage !random <playlist-id or db id>
		Returns a random song from the specified playlist
		"""
		split = ctx.message.content.split(' ')
		if len(split) != 2:
			return await ctx.send("Usage: !random <id>")
		playlist_id = await extract_playlist_id(split[1])
		if playlist_id is None:
			playlist_id = self._dbpointer.get_playlist_id_by_unique_id(split[1])[0]
		results = spotify.user_playlist(spotify_user_id, playlist_id, fields='tracks,next,name')
		tracks = results['tracks']
		song_number = randint(1,int(tracks['total']))
		count = 1
		while True:
			for item in tracks['items']:
				track = item['track'] if 'track' in item else item
				try:
					if count == song_number:
						return await ctx.send(track['external_urls']['spotify'])
				except (KeyError, UnicodeEncodeError) as e:
					pass
				count += 1
			# 1 page = 50 results
			# check if there are more pages
			if tracks['next']:
				tracks = spotify.next(tracks)
			else:
				break


		

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
		logging.info("Found {0} songs in '{1}'".format(
			len(songs), playlist_name))
		for song in songs:
			await channel.send("New track added to '{0}'. {1}".format(playlist_name, song))

		values = {
			"last_checked": get_current_time(as_string=True),
			"pid": playlist_id,
			"channel_id": channel_id
		}

		self._dbpointer.update_time(values)
		return len(songs)

	async def fetch_all(self):
		"""
		Perform a fetch for all database entries
		:return: None
		"""
		global credential_manager
		global spotify
		await self.wait_until_ready()
		while not self.is_closed():
			spotify = spotipy.Spotify(
				client_credentials_manager=credential_manager)
			data = self._dbpointer.fetch_tracking_data()
			for (playlist_id, playlist_name, channel_id, last_checked) in data:
				await self.fetch(int(channel_id), playlist_id, playlist_name, convert_time(last_checked))
			await asyncio.sleep(self.__delay)

	""" Overrides """

	async def on_ready(self):
		logging.info('We have logged in as {0.user}'.format(self))
		print('We have logged in as {0.user}'.format(self))
		await discord_client.change_presence(activity=discord.Activity(name='Spotify', type=2))

	async def on_message(self, message):
		await self.process_commands(message)

	""" Error Handling """
	@Decorators.handle_errors(track.error, purgeme.error, stop.error, me.error, db.error, delay.error)
	async def perm_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(str(error))
		else:
			await ctx.send(str(error))

	""" Construct an embedded message when !track is used """
	async def track_embed(self, values):
		thumbnail_url = await fetch_playlist_art(spotify_user_id, values[0]['playlist_id'])
		embed = discord.Embed(
			title='Playlists Added',
			description='by %s' % values[0]['username'],
			colour=discord.Colour.green()
		)
		embed.set_thumbnail(url=thumbnail_url)
		embed.set_author(
			name='Spotty',
			icon_url=r'https://cdn.discordapp.com/attachments/509168690483298304/530556711329595392/spotty.png'
		)
		for val in values:
			embed.add_field(name=val['playlist_name'], value='Success! :white_check_mark:', inline=True)
		embed.set_footer(text='Use the tracking command to view the playlists being tracked.')

		return embed
	
	""" Embed for !stop command """
	async def deleted_notify_embed(self, name=None):
		if name is not None:
			desc = str()
		else:
			desc = 'Channel is no longer tracking playlist'
		embed = discord.Embed(
			title='Stopped',
			description=desc,
			colour=discord.Colour.green()
		)
		embed.set_author(
			name='Spotty',
			icon_url=r'https://cdn.discordapp.com/attachments/509168690483298304/530556711329595392/spotty.png'
		)
		if name is not None:
			embed.add_field(name=name, value='No longer being tracked. :x:', inline=True)
		embed.set_footer(text='Use the tracking command to view the playlists being tracked.')
		return embed

	""" Embed for !tracking """
	async def tracking_embed(self, data):
		embed = discord.Embed(
			title='Currently Tracking',
			colour=discord.Colour.green()
		)
		embed.set_author(
			name='Spotty',
			icon_url=r'https://cdn.discordapp.com/attachments/509168690483298304/530556711329595392/spotty.png'
		)
		for (id, name) in data:
			embed.add_field(name=name, value='Playlist ID: %d' % id, inline=True)
		return embed


""" Move Functions """

async def fetch_playlist(username, playlist_id, previous_date):
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id: The playlist id
	:param previous_date: The last time fetched
	:return: A list of URLs of the new songs
	"""
	results = spotify.user_playlist(
		username, playlist_id, fields='tracks,next,name')
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
				logging.warn(u'Skipping track {0} by {1} (local only?)'.format(
					track['name'], track['artists'][0]['name']))
		# 1 page = 50 results
		# check if there are more pages
		if tracks['next']:
			tracks = spotify.next(tracks)
		else:
			break
	return new_songs

async def fetch_playlist_art(username, playlist_id):
	results = spotify.user_playlist(username, playlist_id, fields='images')
	if results:
		return results['images'][0]['url']
	return None


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


def generate_credentials():
	""" Generate the token for Spotify. """
	credentials = oauth2.SpotifyClientCredentials(
		client_id=client_id,
		client_secret=client_secret)
	return credentials

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
	logging.error('Invalid playlist id or url')
	return None

def convert_time(time_string):
	"""
	Takes time as a string and converts it to an aware datetime
	:param time_string: Time in the form %Y-%m-%dT%H:%M:%SZ
	:return: An aware datetime
	"""
	added_at = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
	return pytz.UTC.localize(added_at)


def get_current_time(as_string=False):
	"""
	Get the current time
	:param as_string: Whether to return a datetime or as a string (for the db)
	:return: The current time
	"""
	ret = new_time.localize(datetime.datetime.now()).astimezone(old_time)
	return ret.strftime('%Y-%m-%dT%H:%M:%SZ') if as_string else ret


if __name__ == '__main__':
	discord_client = Spotty()
	credential_manager = generate_credentials()
	spotify = spotipy.Spotify(client_credentials_manager=credential_manager)
	discord_client.run(spotty_token)
	logging.info("Started spotty")
