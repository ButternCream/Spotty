import discord
from discord.ext import commands
from utils.decorators import Decorators

class Owner(object):
	def __init__(self, bot):
		self.bot = bot

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
		for row in self.bot._dbpointer.fetch_by_user_id(user_id):
			await ctx.send(row)

	@commands.command()
	@commands.is_owner()
	@Decorators.pm_only()
	async def db(self, ctx):
		for row in self.bot._dbpointer.fetch_all():
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
			return await ctx.send("Current delay is %s" % str(self.bot.delay))
		elif len(split) == 2:
			new_delay = int(split[1])
			self.bot.delay = new_delay
		else:
			await ctx.send("Usage: !delay or !delay <seconds>")
		logging.warn("In the delay")

	""" Error Handling """
	@Decorators.handle_errors(me.error, db.error, delay.error)
	async def perm_error(self, ctx, error):
		logging.error(str(error))

def setup(bot):
	bot.add_cog(Owner(bot))