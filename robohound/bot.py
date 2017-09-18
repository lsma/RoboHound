"""
bot.py

The actual bot class and base code/mechanisms
"""
import logging
import discord
from discord.ext import commands

from .storage import Db, Storage


class RoboHound(commands.Bot):
    """
    woof
    -RoboHound
    """
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix='!', description=self.__doc__)
        
        self._db = Db(kwargs.get('redis_address'))
        self.storage = None
        self.log = kwargs.get('log', logging.getLogger().getChild('bot'))
    
    def load_commands(self):
        """Find all un-added commands in this bot and add them"""
        t = 0
        for x in dir(self):
            v = getattr(self, x)
            if isinstance(v, commands.core.Command):
                self.add_command(v)
                self.log.debug(f'Added base-level command {x}')
                t += 1
        
        if t:
            self.log.info(f'Added {t} base-level command(s)')
        else:
            self.log.debug('No base-level commands were added')
    
    def run(self, t):
        super().run(t, reconnect=True)
        
    async def on_ready(self):
        self.log.info('Connected and ready to go')
        self.log.info(f'Logged in as {self.user.name} ({self.user.id})')
        
        try:
            await self.change_presence(game=discord.Game(name='fetch'))
        except Exception as e:
            self.log.warning("Couldn't set game status")
            raise e
    
        try:
            self.load_commands()
        except Exception as e:
            self.log.warning("Couldn't load base-level commands")
            raise e
            
            
        self.storage = await self._db.get_namespace('')
            
    
    @commands.command()
    async def set(self, key, value):
        """Save a value under key (temporary test command)"""
        await self.storage.set(key, value)
        await self.say('Stored `{}` under `{}`'.format(value,key))
        
        
    @commands.command()
    async def get(self, key):
        """Retreive a value under key (temporary test command)"""
        value = await self.storage.get(key)
        if value:
            await self.say(f'`{key}`:\n```{value}```')
        else:
            await self.say(f"*Couldn't find* `{key}`")
            
        
