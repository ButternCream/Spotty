import discord
from discord.ext import commands
from utils.decorators import Decorators
from utils.helpers import *
import logging

""" Admin Commands """
class Admin(object):
	def __init__(self, bot):
		self.bot = bot

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
			playlist_name = await fetch_playlist_name(self.bot.spotify, spotify_user_id, playlist_id)
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
			
			if self.bot._dbpointer.insert(values):
				data_list.append(values)
		if len(data_list) < 1:
			return
		embed_msg = await self.bot.track_embed(data_list)
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

		self.bot._dbpointer.delete_all(values)
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
			owner_id = int(self.bot._dbpointer.get_user_id_for_unique_id(id)[0])
			if owner_id != user_id:
				return await ctx.send("Hmmm you shouldn't do that :no_good:")
			name = self.bot._dbpointer.fetch_name_by_unique_id(id)[0]
			self.bot._dbpointer.delete_by_unique_id({"u_id": id})
			embed_msg = await self.bot.deleted_notify_embed(name=name)
			return await ctx.send(embed=embed_msg)
		self.bot._dbpointer.delete_by_channel_id({"channel_id": channel_id})
		embed_msg = await self.bot.deleted_notify_embed()
		await ctx.send(embed=embed_msg)

	""" Error Handling """
	@Decorators.handle_errors(track.error, purgeme.error, stop.error)
	async def perm_error(self, ctx, error):
		await ctx.send(str(error))

def setup(bot):
	bot.add_cog(Admin(bot))