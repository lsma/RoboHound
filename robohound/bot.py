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
        """
        owner_id        ID of discord useer who is running the bot (ie you)
        redis_address   tuple in the form (hostname, port) of a redis server
        log             Python logging object.  Defaults to *.bot
        """
        super().__init__(command_prefix='!', description=self.__doc__)
        
        self._owner_id = kwargs.get('owner_id')
        self._db = Db(kwargs.get('redis_address'))
        self.storage = None
        self.log = kwargs.get('log', logging.getLogger().getChild('bot'))
    
    def load_commands(self):
        """Find all un-added commands in this bot and add them"""
        await self.wait_until_ready()
        
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
        """Start RoboHound"""
        super().run(t, reconnect=True)
        
    
    async def bot_owner_get(self, message, check=None, timeout=None):
        """
        Internal utility function used by plugins that need to confirm something
        with the bot owner
        """
        await self.wait_until_ready()
        await self.send_message(self.owner, message)
        return await client.wait_for_message(
            author=self.owner, check=check, timeout=timeout)
    
    async def bot_owner_confirm(self, message):
        """
        Internal utility function used by plugins that need to get a yes/no
        answer from the bot owner
        """
        # Check to make sure the answer is a private message and
        #   it is yes or no
        def c(msg):
            return isinstance(msg.channel, discord.PrivateChannel) and
                msg.content.lower() in ('yes', 'no')
        
        # Wait for the answer, and return the result
        answer = await self.bot_owner_get(message, check=c, timeout=timeout)
        answer = answer.casefold()
        return answer == 'yes'
        
        
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
            
        self.owner = await self.get_user_info(self._owner_id)
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
            
        
