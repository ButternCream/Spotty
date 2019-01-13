import discord
from discord.ext.commands import CommandNotFound
import logging

class Overrides(object):
	def __init__(self, bot):
		self.bot = bot

	""" Overrides """
	async def on_ready(self):
		logging.info('We have logged in as {0.user}'.format(self.bot))
		print('We have logged in as {0.user}'.format(self.bot))
		await self.bot.change_presence(activity=discord.Activity(name='Spotify', type=2))
	
	async def on_command_error(self, ctx, error):
		if isinstance(error, CommandNotFound):
			return
		logging.error(str(error))
		raise error

def setup(bot):
	bot.add_cog(Overrides(bot))