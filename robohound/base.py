"""
base_commands.py

Base and owner-only commands (extension managment, diagnostics, bot moderation, 
etc.) for the bot.
"""
from discord.ext import commands

from .utils import is_bot_ower

class Extension:
    all_extensions = set()
    def __init__(self, bot):
        name = self.__class__.__name__
        if name in self.all_extensions:
            raise NameError(f"Can't init extension '{name}', already in use")
        self.all_extensions.add(name)
        
        self.bot = bot
        self.log = bot.log.getChild(self.__class__.__name__)
        self.storage = bot.storage.get_namespace(self.__class__.__name__)


class Base(Extension):
    """
    Extension containing base bot commands.
    This cog is always loaded during bot __init__, and can't be dumped.
    """
    
    EXT_PREFIX = 'robohound.extensions.'
    
    @commands.command()
    async def about(self):
        await self.bot.say(self.bot.__class__.__doc__)
    
    
    @commands.group(aliases=['ext'], hidden=False, invoke_without_command=True)
    @is_bot_ower()
    async def extension(self):
        """extension command group"""
        await self.bot.type()
        sub_commands = '`, `'.join(self.extension.commands)
        m = f'Available sub-commands: `{sub_commands}`'
        await self.bot.say(m)
        m = 'Current active extensions:'
        for e in self.bot.extensions:
            m += '\n `{}`'.format(e.split('.')[-1])
        await self.bot.say(m)
        

    @extension.command()
    @is_bot_ower()
    async def load(self, *, ext:str):
        """Load extension <ext>"""
        await self.bot.type()
        ext = ext.strip()
    
        try:
            self.bot.load_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Loaded {ext}')
            await self.bot.say(f'Extension `{ext}` has been loaded')
    
        except Exception as e:
            await self.bot.say('Sorry, I ran into an issue loading that extension')
            raise e


    @extension.command()
    @is_bot_ower()
    async def dump(self, *, ext:str):
        """Dump extension <ext>"""
        await self.bot.type()
        ext = ext.strip()
    
        try:
            self.bot.unload_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Dumped {ext}')
            await self.bot.say(f'Extension `{ext}` has been dumped')
    
        except Exception as e:
            await self.bot.say('Sorry, I ran into an issue dumping that extension')
            raise e


    @extension.command()
    @is_bot_ower()
    async def reload(self, *, ext:str):
        """Reload extension <ext>"""
        await self.bot.type()
        ext = ext.strip()
    
        try:
            self.bot.unload_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Dumped {ext}')
            
            self.bot.load_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Loaded {ext}')
            
            await self.bot.say(f'Extension `{ext}` has been reloaded')
    
        except Exception as e:
            await self.bot.say('Sorry, I ran into an issue reloading that extension')
            raise e


    @extension.command()
    @is_bot_ower()
    async def list(self):
        """List all extensions"""
        await self.bot.type()
        m = 'Current active extensions:'
        for e in self.bot.extensions:
            m += '\n `{}`'.format(e.split('.')[-1])
        await self.bot.say(m)


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
