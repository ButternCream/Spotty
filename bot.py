import spotipy
import spotipy.oauth2 as oauth2
import discord
from discord.ext import commands
import asyncio
import datetime
import re
import time
import sys,traceback
from pprint import pprint
from random import randint
from utils.decorators import Decorators
from utils.database import DatabasePointer
from utils.helpers import *
import logging
logging.basicConfig(filename=r'spotty.log', filemode='w', level=logging.WARNING,
					format=' %(asctime)s - %(levelname)s - %(message)s')

# Spotify fetching code courtesy of ritiek https://github.com/plamere/spotipy/issues/246

# https://discordapp.com/oauth2/authorize?scope=bot&permissions=66321471&client_id=<bot-id> (optional)&guild_id=<server-id> Example on how to add with all perms

class Spotty(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix=('!', '$', '(', ')', ';', '?', '.'))
		self.__fetch_task = self.loop.create_task(self.fetch_all())
		self.delay = delay
		self._dbpointer = DatabasePointer()
		self.credentials = generate_credentials()
		self.spotify = spotipy.Spotify(client_credentials_manager=self.credentials)

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
		songs = await fetch_playlist(self.spotify, spotify_user_id, playlist_id, last_checked)
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
		await self.wait_until_ready()
		while not self.is_closed():
			self.spotify = spotipy.Spotify(client_credentials_manager=self.credentials)
			data = self._dbpointer.fetch_tracking_data()
			for (playlist_id, playlist_name, channel_id, last_checked) in data:
				await self.fetch(int(channel_id), playlist_id, playlist_name, convert_time(last_checked))
			await asyncio.sleep(self.delay)

	""" Construct an embedded message when !track is used """
	async def track_embed(self, values):
		thumbnail_url = await fetch_playlist_art(self.spotify, spotify_user_id, values[0]['playlist_id'])
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


extensions = [
	'cogs.commands.owner',
	'cogs.commands.admin',
	'cogs.commands.everyone',
	'cogs.overrides'
]

""" Load cogs """
def load_extensions(bot, extensions):
	for extension in extensions:
		try:
			bot.load_extension(extension)
		except Exception as e:
			print(f'Failed to load extension {extension}.', file=sys.stderr)
			traceback.print_exc()


if __name__ == '__main__':
	bot = Spotty()
	load_extensions(bot, extensions)
	bot.run(spotty_token)
	logging.info("Started spotty")
