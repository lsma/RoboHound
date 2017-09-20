import re
import os
import logging
import json
import asyncio
import functools
import aiofiles
import datetime
import parsedatetime
import pytz
import atexit
import discord
from discord.ext import commands
from pytz import timezone

from robohound.base import Extension


class Saved:
    """Base class for saved items"""
    def __str__(self):
        return f'{self.author.name} scheduled "{self.content}" for ' + \
            f'{self.when:%a, %b %d, %Y at %H:%M:%S}'
        
    def __init__(self, bot, content, when, channel, author):
        self.bot = bot
        self.content = content
        
        if isinstance(channel, 
            (discord.Channel, discord.PrivateChannel)):
            self.channel = channel
        elif isinstance(channel, str):
            self.channel = bot.get_channel(channel)
        else:
            raise TypeError('"channel" must be a discord.Channel, ' + \
                'discord.PrivateChannel, or str')
            
        if isinstance(when, datetime.datetime):
            self.when = when
        elif isinstance(when, float):
            self.when = datetime.datetime.fromtimestamp(when)
        else:
            raise TypeError('"when" must be a datetime.datetime, ' + \
                'or float')
        
        if isinstance(author, discord.Member):
            self.author = author
        elif isinstance(author, discord.User):
            self.author = self.channel.server.get_member(author.id)
        elif isinstance(author, str):
            self.author = self.channel.server.get_member(author)
        else:
            raise TypeError('"author" must be a discord.Member, ' + \
                'discord.User, or str')
                
        self._canceled = None
    
    
    @property
    def wait_time(self):
        now = datetime.datetime.now(tz=self.when.tzinfo)
        return (self.when - now).total_seconds()
    
    
    @property
    def overdue(self):
        return (self.wait_time < 0)
        
        
    async def execute(self):
        if not self.overdue:
            await asyncio.sleep(self.wait_time)
            return 1
        
    
    def cancel(self):
        self._canceled = True
    
    
    def encode(self, more={}):
        """Encode this object into a dict"""
        d = {'content': self.content,
             'when': self.when.timestamp(),
             'channel': self.channel.id,
             'author': self.author.id}
        
        d.update(more)
        
        return d
    
    @classmethod
    def decode(class_, d, bot):
        when = datetime.datetime.fromtimestamp(d['when'])
        channel = bot.get_channel(d['channel'])
        author = bot.get_user_info(d['author'])
        return class_(bot, d['content'], when, channel, author)


class SavedMessage(Saved):
    """This object holds a message for the bot to say at a certain time"""
    def __init__(self, bot, message, when, channel, author):
        super().__init__(bot, message, when, channel, author)
    
    async def execute(self):
        await super().execute()
        await self.bot.send_message(self.channel,
            f'*Scheduled Message:*\n{self.content}')



class SavedCommand(Saved):
    """This object holds a command for the bot to execute at a certain time"""
    
    def __init__(self, bot, cmd, when, channel, author):
        super().__init__(bot, cmd, when, channel, author)
            
    
    async def execute(self):
        m = discord.Message(
            content = self.content,
            channel = self.channel,
            author = {
                'username': self.author.name,
                'discriminator': self.author.discriminator,
                'id': self.author.id,
                'bot': self.bot,
            },
            timestamp = datetime.datetime.now().isoformat(),
            reactions = [],
        )
        await super().execute()
        await self.bot.send_message(self.channel,
            f'Executing ``{self.content}`` (schedule by {self.author.mention})')
        await self.bot.process_commands(m)




class Schedule(Extension):
    """Commands for time-based actions"""
    TZ_CONVERT = {
        discord.ServerRegion.us_west:       'US/Pacific',
        discord.ServerRegion.us_east:       'US/Eastern',
        discord.ServerRegion.us_central:    'US/Central',
        discord.ServerRegion.eu_west:       'Europe/London',
        discord.ServerRegion.eu_central:    'Europe/Berlin',
        discord.ServerRegion.singapore:     'Asia/Singapore',
        discord.ServerRegion.london:        'Europe/London',
        discord.ServerRegion.sydney:        'Pacific/Port_Moresby',
        discord.ServerRegion.amsterdam:     'Europe/Amsterdam',
        discord.ServerRegion.frankfurt:     'Europe/Berlin',
        discord.ServerRegion.brazil:        'America/Sao_Paulo',
        discord.ServerRegion.vip_us_east:   'US/Eastern',
        discord.ServerRegion.vip_us_west:   'US/Pacific',
        discord.ServerRegion.vip_amsterdam: 'Europe/Amsterdam',
    }
    
    CMD = re.compile('^!\w+\s+`(?P<content>[^`]+)`\s+(?P<when>(\w|\s)+)$')
    
    SAVE_FILE = 'extensions/data/schedule.json'
    
    
    def __init__(self, bot, *args, **kwargs):
        super().__init__(bot)
        
        self.cal = parsedatetime.Calendar()
        
        self.ready = False
        self.bot.loop.create_task(self.load())
    
    
    def parse(self, server, message):
        """Parse a time string like 'tomorrow at 3PM' into a datetime"""
        tz = timezone(self.TZ_CONVERT[server.region])
        dt, _ = self.cal.parseDT(datetimeString=message)
        return dt.astimezone(tz)
        
        
    async def load(self):
        """Load commands from a file"""
        await self.bot.wait_until_ready()
        
        self.log.info('Loading saved items')
        failed = {}
        total_items = await self.storage.llen('saved')
        while total_items > 0
            total_times -= 1
            
            data = await self.storage.rpop('saved')
            cur = self.decode_saved(**json.loads(data))
            
            if cur.overdue():
                if cur.channel in failed:
                    failed[cur.channel] += 1
                else:
                    failed[cur.channel] = 1
                self.log.debug(f'Ignored overdue item "{cur.content}"')
            else:
                self.bot.loop.call_soon(self.add_saved(cur))
        
        self.ready = True
        
        for ch in failed:
            await self.bot.send_message(
                ch,
                'Apologies, but I had to reboot, and lost ' + \
                '{} scheduled actions!'.format(failed[ch]),
            )
        
    
    def decode_saved(self,content,when,channel,author):
        """
        Makes a new saved item
        This coroutine will not complete until the saved item has been executed
        """
        if content.startswith('!'):
            t = SavedCommand
        else:
            t = SavedMessage
        
        return t(
            self.bot,
            content,
            when,
            channel,
            author,
        )
    
    
    async def add_saved(self, saved_item):
        """
        Makes a new saved item
        This coroutine will not complete until the saved item has been executed
        """
        data = saved_item.encode()
        
        # Put the saved item into the database in case the bot dies
        await self.storage.lpush('saved', data)
        self.log.info(f'Added saved item "{saved_item.content}"')
        
        # This coroutine will spend most of its life here, waiting for the saved
        # item to ripen, and be executed
        result = await saved_item.execute()
        
        # Remove the completed saved item from the database.  We don't want it
        # to run twice if the bot gets rebooted
        await self.storage.lrem('saved', 1, data)
        self.log.info(f'Saved item "{saved_item.content}" complete, removed' + \
            ' from database')
        
        
    @commands.group(pass_context=True,no_pm=True,invoke_without_command=True)
    async def schedule(self, ctx, content:str, when:str):
        """
        Schedule an action to run at a certain time
        Make sure to put <contents> in tick marks.  If <content>
        starts with a "!", it will be executed as a bot command.
        Otherwise, <content> will simply be messaged at the specified
        time. Examples:
        > !schedule `!coin` in 2 hours
        > !schedule `!unban ronald` tomorrow at 7PM'
        > !schedule `!roll ronald admin` in 7 days'
        > !schedule `!unroll ronald admin` on January 1st, 2018'
        > !schedule `Happy birthday!` on November 12th at 10AM
        The server's region will determine the timezone used
        """
        await self.bot.type()
        
        if not self.ready:
            mention = ctx.message.author.mention
            await self.bot.say(
                f"Sorry, {mention}, I'm a bit out-of-sorts right now.\n" + \
                'Try again later')
            return
        
        data = self.CMD.match(ctx.message.content)
        if data:
            content = data['content']
            when = self.parse(ctx.message.server, data['when'])
            
            await self.bot.say(
                f'I will excute `{content}` at ' + \
                f'{when:%a, %b %d, %Y at %H:%M:%S}', delete_after=6)
            
            saved_item = self.decode_saved(
                content = content,
                when = when,
                channel = ctx.message.channel,
                author = ctx.message.author,
            )
            
            self.bot.loop.call_soon(
                functools.partial(self.add_saved, saved_item)
            )
            
            
        else:
            await self.bot.say("I don't understand.")
            await self.bot.say('Make sure your command looks ' + \
                f'like this:\n``!{ctx.command} `[some command]` ' + \
                f'[some time]``')
            await self.bot.say(f'Try `!help {ctx.command}`')
        
    @schedule.command(pass_context=True,no_pm=True)
    async def list(self, ctx):
        await self.bot.type()
        #m = '\n'.join([str(x) for x in self.commands])
        #await self.bot.say(f'**Scheduled Actions:**\n```\n{m}\n```')
        await self.bot.say('Sorry, this commands is currently disabled')
    
    

def setup(bot):
    bot.add_cog(Schedule(bot))



