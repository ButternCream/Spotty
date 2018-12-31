""" TODO """
""" Custom Command Check Failures """
class CategoryCheckFailure(commands.CheckFailure): pass
class ChannelCheckFailure(commands.CheckFailure): pass

class Decorators:

	""" Decorator for checking if a message is in a valid category """
	def in_category(*category_names): # TODO: Change to category id because of duplicate names
		async def predicate(ctx):
			# TODO: Get valid categories from db by guild id
			current_channel = ctx.channel
			category_names = map(__lower, category_names)
			if current_channel.category.name.lower() in category_names:
				raise CategoryCheckFailure("Sorry you are not allowed to do that here :no_good:")
			return True
		return commands.check(predicate)
	
	""" Decorator for checking if a message is in a valid channel """
	def in_channel(*channel_names): # TODO: Change to channel id because of duplicate names
		async def predicate(ctx):
			# TODO: Get valid channels from db by guild id
			current_channel = ctx.channel
			channel_names = map(__lower, channel_names)
			if ctx.channel.name.lower() not in channel_names:
				raise ChannelCheckFailure("Sorry you are not allowed to do that here :no_good:")
			return True
		return commands.check(predicate)

    @handle_errors(in_channel.error, in_category.error)
    async def permission_error(ctx, error):
        if any(isinstance(error,err_type) for err_type in [CategoryCheckFailure, ChannelCheckFailure]):
            await ctx.send("Sorry you cant do that here :no_good:")

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


