"""
bot.py

The actual bot class and base code/mechanisms
"""
import logging
import traceback
import discord
from discord.ext import commands

from .storage import Db, Storage
from .utils import *


class RoboHound(commands.Bot, UtilityMixin):
    """
    woof
    -RoboHound
    """
    def __init__(self, *args, **kwargs):
        """
        owner_id        ID of discord useer who is running the bot (ie you)
        redis_address   tuple in the form (hostname, port) of a redis server
        log             Python logging object.  RoboHound will log to a child
        """
        super().__init__(command_prefix='!', description=self.__doc__)
        
        self._owner_id = kwargs.get('owner_id')
        
        self._db = Db(kwargs.get('redis_address'))
        self.storage = None
        
        self.log = kwargs.get('log', logging.getLogger()).getChild('RoboHound')
        self.debug = kwargs.get('debug', False)
        if self.debug:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)
        
    
    
    def run(self, t):
        """Start RoboHound"""
        super().run(t, reconnect=True)
    
    
        
    async def on_ready(self):
        self.log.info('Connected and ready to go')
        self.log.info(f'Logged in as {self.user.name} ({self.user.id})')
        
        try:
            await self.change_presence(game=discord.Game(name='fetch'))
        except Exception as e:
            self.log.warning("Couldn't set game status")
            raise e
            
        self.storage = self._db.get_namespace('')
        self.owner = await self.get_user_info(self._owner_id)
        
        # This extensions holds most of the bot's base capabilities
        self.load_extension('robohound.base')
        self.add_command(self.reload_base)
    
    async def on_command_error(self, exception, ctx):
        self.log.error(f'Ignoring exception in command "{ctx.command}"')
        tb = ''.join(traceback.format_exception( \
            type(exception), exception, exception.__traceback__))
        self.log.error(tb)
    
    @commands.command(hidden=True)
    @is_bot_ower()
    async def reload_base(self):
        self.log.debug('Unloading base extension')
        self.unload_extension('robohound.base')
        self.log.debug('Reloading base extension')
        self.load_extension('robohound.base')
        await self.say('Success')
        
            
        
