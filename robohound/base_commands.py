"""
base_commands.py

Base and owner-only commands (extension managment, diagnostics, bot moderation, 
etc.) for the bot.
"""
from discord.ext import commands

class Base:
    """
    Extension containing base bot commands.
    This cog is always loaded during bot __init__, and can't be dumped.
    """

    def __init__(self, bot):
        self.bot = bot
    
    
    @commands.command()
    async def about(self):
        await self.bot.say(self.bot.__class__.__doc__)
    
    
    @commands.group(aliases=['db'], hidden=True, pass_context=True)
    async def redis(self, ctx):
        """Commands for raw database editing !!VERY DANGEROUS!!"""
        if ctx.invoked_subcommand is None:
            await self.bot.say('You must use a sub-command')
    
    
    @redis.command()
    async def set(self, key, value):
        """Save a value under key (temporary test command)"""
        await self.bot.storage.set(key, value)
        await self.bot.say('Stored `{}` under `{}`'.format(value,key))
        
        
    @redis.command()
    async def get(self, key):
        """Retreive a value under key (temporary test command)"""
        value = await self.bot.storage.get(key)
        if value:
            await self.bot.say(f'`{key}`:\n```{value}```')
        else:
            await self.bot.say(f"*Couldn't find* `{key}`")

def setup(bot):
    bot.add_cog(Base(bot))
