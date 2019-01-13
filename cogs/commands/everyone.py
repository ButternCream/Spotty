import discord
from discord.ext import commands
from utils.decorators import Decorators
from utils.helpers import *
from random import randint
import logging

class Everyone(object):
	def __init__(self, bot):
		self.bot = bot

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
		id = self.bot._dbpointer.get_playlist_id_by_unique_id(split[1])[0]
		url = await fetch_playlist_link(self.bot.spotify, spotify_user_id, id)
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

		data = self.bot._dbpointer.fetch_playlists_by_channel_id(channel_id)
		if len(data) == 0:
			return await ctx.send("#{0} is not currently tracking any playlists.".format(channel_name))
		embed_msg = await self.bot.tracking_embed(data)
		await ctx.send(embed=embed_msg)

	@commands.command()
	@commands.guild_only()
	async def random(self, ctx):
		"""
		Usage: !random <playlist-id or db id>
		Returns a random song from the specified playlist
		"""
		split = ctx.message.content.split(' ')
		if len(split) != 2:
			return await ctx.send("Usage: !random <id>")
		playlist_id = await extract_playlist_id(split[1])
		if playlist_id is None:
			playlist_id = self.bot._dbpointer.get_playlist_id_by_unique_id(split[1])[0]
		
		#get_random_song(playlist_id)
		results = self.bot.spotify.user_playlist(spotify_user_id, playlist_id, fields='tracks,next,name')
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
				tracks = self.bot.spotify.next(tracks)
			else:
				break

	""" Error Handling """
	@Decorators.handle_errors(random.error, tracking.error, link.error)
	async def perm_error(self, ctx, error):
		logging.error(str(error))

def setup(bot):
	bot.add_cog(Everyone(bot))