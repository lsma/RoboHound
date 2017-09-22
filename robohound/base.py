"""
base_commands.py

Base and owner-only commands (extension managment, diagnostics, bot moderation, 
etc.) for the bot.
"""
import os
import re
from discord.ext import commands

from .utils import is_bot_ower

class Extension:
    def __init__(self, bot):
        self.bot = bot
        self.log = bot.log.getChild(self.__class__.__name__)
        self.storage = None
        
        self.bot.loop.create_task(self.init_storage())
    
    async def init_storage(self):
        await self.bot.wait_until_ready()
        self.storage = self.bot.storage.get_namespace(self.__class__.__name__)
        self.log.debug('Storage initialized')
        
        result = await self.storage.set('_', self.__class__.__name__)
        self.log.info(f'Storage up and running (test SET returned {result})')


class Base(Extension):
    """
    Extension containing base bot commands.
    This cog is always loaded during bot __init__, and can't be dumped.
    """
    
    EXT_PREFIX = 'robohound.extensions.'
    EXTENSION_FILENAME = re.compile('(?P<ext>\w+)\.py')
    
    @commands.command()
    async def about(self):
        """Print a short message about the bot"""
        await self.bot.say(self.bot.__class__.__doc__)
    
    
    @commands.group(aliases=['ext'], hidden=True, invoke_without_command=True)
    @is_bot_ower()
    async def extension(self):
        """extension command group"""
        await self.bot.type()
        sub_commands = '`, `'.join(self.bot.extension.commands)
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
        
        if f'{self.EXT_PREFIX}{ext}' in self.bot.extensions:
            await self.bot.say(f'Extension `{ext}` has already been loaded' + \
                f'\nTry `!ext reload {ext}`')
            self.log.info(f"Didn't load {ext}: already loaded")
            return
            
        try:
            self.bot.load_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Loaded "{ext}"')
            await self.bot.say(f'Extension `{ext}` has been loaded')
            
        except ModuleNotFoundError as e:
            self.log.info(f'Failed to load "{ext}"')
            await self.bot.say("I couldn't find any extension by that " + \
                f'name (`{ext}`)')
    
        except Exception as e:
            await self.bot.say( \
                'Sorry, I ran into an issue loading that extension')
            raise e


    @extension.command()
    @is_bot_ower()
    async def dump(self, *, ext:str):
        """Dump extension <ext>"""
        await self.bot.type()
        ext = ext.strip()
    
        if f'{self.EXT_PREFIX}{ext}' not in self.bot.extensions:
            await self.bot.say(f'Extension `{ext}` was never loaded')
            self.log.info(f"Didn't dump {ext}: not an active extension")
            return
            
        try:
            self.bot.unload_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Dumped {ext}')
            await self.bot.say(f'Extension `{ext}` has been dumped')
    
        except Exception as e:
            await self.bot.say( \
                'Sorry, I ran into an issue dumping that extension')
            raise e


    @extension.command()
    @is_bot_ower()
    async def reload(self, *, ext:str):
        """Reload extension <ext>"""
        await self.bot.type()
        ext = ext.strip()
    
        if f'{self.EXT_PREFIX}{ext}' not in self.bot.extensions:
            await self.bot.say(f'Extension `{ext}` was never loaded' + \
                f'\nTry `!ext load {ext}`')
            return
            
        try:
            self.bot.unload_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Dumped {ext}')
            
            self.bot.load_extension(f'{self.EXT_PREFIX}{ext}')
            self.log.info(f'Loaded {ext}')
            
            await self.bot.say(f'Extension `{ext}` has been reloaded')
    
        except ModuleNotFoundError as e:
            self.log.info(f'Failed to reload "{ext}"')
            self.log.warning(f'Module "{ext}" ' + \
                'was loaded at some point, but is now unavailable!')
            await self.bot.say("I couldn't find any extension by that " + \
                f'name (`{ext}`)')
    
        except Exception as e:
            await self.bot.say( \
                'Sorry, I ran into an issue reloading that extension')
            raise e


    @extension.command()
    @is_bot_ower()
    async def list(self):
        """List all extensions"""
        await self.bot.type()
        
        all_ = set()
        for ext in os.listdir('./robohound/extensions'):
            match = self.EXTENSION_FILENAME.match(ext)
            if match:
                all_.add(match['ext'])
        
        active = set(x.split('.')[-1] for x in self.bot.extensions)
        
        inactive = list(all_ - active)
        inactive.sort()
        
        active = list(active)
        active.sort()
        
        m = '**Active extensions:**\n`'
        m += '`\n`'.join(active)
        
        m += '`\n**Inactive extensions:**\n`'
        m += '`\n`'.join(inactive)
        m += '`'
        
        await self.bot.say(m)


    @commands.group(aliases=['db'], hidden=True, pass_context=True)
    @is_bot_ower()
    async def redis(self, ctx):
        """Commands for raw database editing !!VERY DANGEROUS!!"""
        if ctx.invoked_subcommand is None:
            await self.bot.say('You must use a sub-command')
            sub_commands = '`, `'.join(self.redis.commands)
            await self.bot.say(f'Available sub-commands: `{sub_commands}`')
    
    
    @redis.command()
    @is_bot_ower()
    async def set(self, key:str, value:str):
        """Save a value under key (temporary test command)"""
        await self.bot.storage.set(key, value)
        await self.bot.say('Stored `{}` under `{}`'.format(value,key))
        
        
    @redis.command()
    @is_bot_ower()
    async def get(self, key:str):
        """Retreive a value under key (temporary test command)"""
        value = await self.bot.storage.get(key)
        if value:
            await self.bot.say(f'`{key}`:\n```{value}```')
        else:
            await self.bot.say(f"*Couldn't find* `{key}`")
            
    @redis.command()
    @is_bot_ower()
    async def all(self, pattern:str):
        """Retreive all keys that match 'pattern'"""
        value = await self.bot.storage.keys(pattern)
        if value:
            await self.bot.say(f'`{pattern}`:\n```{value}```')
        else:
            await self.bot.say(f"*Couldn't find* `{pattern}`")
            
    @redis.command()
    @is_bot_ower()
    @commands.cooldown(1,20.0)
    async def save(self):
        """Save the redis database to disk"""
        value = await self.bot.storage.bgsave()
        await self.bot.say(f'`{value}`')

def setup(bot):
    bot.add_cog(Base(bot))
