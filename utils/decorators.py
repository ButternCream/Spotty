""" Custom Command Check Failures """
from discord.ext import commands
class PermissionCheckFailure(commands.CheckFailure): pass

class Decorators:
	__lower = lambda x: x.lower()

	""" Decorator for checking if a message is in a valid category """
	def in_category(*category_names): # TODO: Change to category id because of duplicate names
		async def predicate(ctx):
			# TODO: Get valid categories from db by guild id
			current_channel = ctx.channel
			category_names = list(map(__lower, category_names))
			if current_channel.category.name.lower() in category_names:
				raise PermissionCheckFailure("Sorry you are not allowed to do that here :no_good:")
			return True
		return commands.check(predicate)
	
	""" Decorator for checking if a message is in a valid channel """
	def in_channel(*channel_names): # TODO: Change to channel id because of duplicate names
		async def predicate(ctx):
			# TODO: Get valid channels from db by guild id
			current_channel = ctx.channel
			channel_names = list(map(__lower, channel_names))
			if ctx.channel.name.lower() not in channel_names:
				raise PermissionCheckFailure("Sorry you are not allowed to do that here :no_good:")
			return True
		return commands.check(predicate)

	""" Decorator for checking if you're guild owner or have the spotty admin role """
	def guild_owner_or_spotty_role():
		async def predicate(ctx):
			roles = [r.name.lower() for r in ctx.author.roles]
			if ctx.author == ctx.guild.owner or "spotty admin" in roles:
				return True
			raise PermissionCheckFailure("Sorry you are not allowed to do that :no_good:")
		return commands.check(predicate)

	""" Decorator for commands that should be PM only """
	def pm_only():
		async def predicate(ctx):
			if ctx.guild is None:
				return True
			raise commands.CheckFailure("PM's only :no_good:")
		return commands.check(predicate)

	"""  
	Cleaner way for one function to handle multiple bot command errors 

	@handle_errors(test.error, me.error, ...)
	async def test_error(...):
		...

	Instead of
	@test.error
	async def test_error(...):
		...
	"""
	def handle_errors(*functions):
		def wrapper(*args, **kwargs):
			for fn in functions:
				fn(*args, **kwargs)
		return wrapper
			