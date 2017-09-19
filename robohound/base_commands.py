"""
base_commands.py

Base and owner-only commands (extension managment, diagnostics, bot moderation, 
etc.) for the bot.
"""
from discord.ext import commands

from ..utils import is_bot_ower

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
    
    
    @commands.group(aliases=['ext'], hidden=True, pass_context=True,
                    invoke_without_command=True)
    @is_bot_ower()
    async def extension(self, ctx):
        """extension command group"""
        await self.send_typing(ctx.message.channel)
        sub_commands = ', '.join(extension.commands)
        m = f'Available sub-commands: {sub_commands}'
        await self.say(m)
        await self.extension.list()
        

    @extension.command(pass_context=True)
    @is_bot_ower()
    async def load(self, ctx, *, ext:str):
        """Load extension <ext>"""
        await self.send_typing(ctx.message.channel)
        ext = ext.strip()
    
        try:
            self.load_extension(f'extensions.{ext}')
            self.log.info(f'Loaded {ext}')
            await self.say(f'Extension `{ext}` has been loaded')
    
        except Exception as e:
            await self.say('Sorry, I ran into an issue loading that extension')
            raise e


    @extension.command(pass_context=True)
    @is_bot_ower()
    async def dump(self, ctx, *, ext:str):
        """Dump extension <ext>"""
        await self.send_typing(ctx.message.channel)
        ext = ext.strip()
    
        try:
            self.unload_extension(f'extensions.{ext}')
            self.log.info(f'Dumped {ext}')
            await self.say(f'Extension `{ext}` has been dumped')
    
        except Exception as e:
            await self.say('Sorry, I ran into an issue dumping that extension')
            raise e


    @extension.command(pass_context=True)
    @is_bot_ower()
    async def reload(self, ctx, *, ext:str):
        """Reload extension <ext>"""
        await self.send_typing(ctx.message.channel)
        ext = ext.strip()
    
        try:
            self.unload_extension(f'extensions.{ext}')
            self.log.info(f'Dumped {ext}')
            
            self.load_extension(f'extensions.{ext}')
            self.log.info(f'Loaded {ext}')
            
            await self.say(f'Extension `{ext}` has been reloaded')
    
        except Exception as e:
            await self.say('Sorry, I ran into an issue reloading that extension')
            raise e


    @extension.command()
    @is_bot_ower()
    async def list(self):
        """List all extensions"""
        await self.send_typing(ctx.message.channel)
        m = 'Current active extensions:'
        for e in self.extensions:
            m += '\n `{}`'.format(e.split('.')[-1])
        await self.say(m)


    @commands.group(aliases=['db'], hidden=True, pass_context=True)
    @is_bot_ower()
    async def redis(self, ctx):
        """Commands for raw database editing !!VERY DANGEROUS!!"""
        if ctx.invoked_subcommand is None:
            await self.bot.say('You must use a sub-command')
    
    
    @redis.command()
    @is_bot_ower()
    async def set(self, key, value):
        """Save a value under key (temporary test command)"""
        await self.bot.storage.set(key, value)
        await self.bot.say('Stored `{}` under `{}`'.format(value,key))
        
        
    @redis.command()
    @is_bot_ower()
    async def get(self, key):
        """Retreive a value under key (temporary test command)"""
        value = await self.bot.storage.get(key)
        if value:
            await self.bot.say(f'`{key}`:\n```{value}```')
        else:
            await self.bot.say(f"*Couldn't find* `{key}`")

def setup(bot):
    bot.add_cog(Base(bot))
