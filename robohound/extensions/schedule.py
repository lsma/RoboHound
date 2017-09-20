import re
import os
import logging
import json
import asyncio
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
    
    async def execute(self):
        now = datetime.datetime.now(tz=self.when.tzinfo)
        time_delta = (self.when - now).total_seconds()
        
        if time_delta > 0:
            await asyncio.sleep(time_delta)
    
    
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
        
        self.commands = []
        
        self.bot.loop.create_task(self.load())
    
    
    def parse(self, server, message):
        """Parse a time string like 'tomorrow at 3PM' into a datetime"""
        tz = timezone(self.TZ_CONVERT[server.region])
        dt, _ = self.cal.parseDT(datetimeString=message)
        return dt.astimezone(tz)
    
    async def save(self):
        """Save all currently waiting commands to a file"""
        d = []
        for i in self.commands:
            d.append(i.encode())
        
        data = json.dumps(d)
        
        async with aiofiles.open(self.SAVE_FILE, mode='w') as f:
            await f.write(data)
        self.log.info('Saved commands to disk')
        
        
    async def load(self):
        """Load commands from a file"""
        await self.bot.wait_until_ready()
        
        async with aiofiles.open(self.SAVE_FILE, mode='r') as f:
            d = await f.read()
        
        data = json.loads(d)
        self.commands.clear()
        
        for c in data:
            self.bot.loop.create_task(self.add_saved(
                c['content'],
                datetime.datetime.fromtimestamp(c['when']),
                str(c['channel']),
                str(c['author'])
            ))
            
    
    async def add_saved(self,content,when,channel,author):
        """Add a saved item to the manager"""
        if content.startswith('!'):
            t = SavedCommand
        else:
            t = SavedMessage
        
        saved_item = t(
            self.bot,
            content,
            when,
            channel,
            author,
        )
        
        self.commands.append(saved_item)
        await self.save()
        self.log.info(f'Added saved item "{content}"')
        await saved_item.execute()
        self.commands.remove(saved_item)
        await self.save()
        self.log.info(f'Removed saved item "{content}"')
        
        
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
        await self.bot.send_typing(ctx.message.channel)
        data = self.CMD.match(ctx.message.content)
        if data:
            content = data['content']
            when = self.parse(ctx.message.server, data['when'])
            
            await self.bot.say(
                f'I will excute `{content}` at ' + \
                f'{when:%a, %b %d, %Y at %H:%M:%S}', delete_after=6)
            
            await self.add_saved(content,when,
                ctx.message.channel,ctx.message.author)
            
            
        else:
            await self.bot.say("I don't understand.")
            await self.bot.say('Make sure your command looks ' + \
                f'like this:\n``!{ctx.command} `[some command]` ' + \
                f'[some time]``')
            await self.bot.say(f'Try `!help {ctx.command}`')
        
    @schedule.command(pass_context=True,no_pm=True)
    async def list(self, ctx):
        await self.bot.send_typing(ctx.message.channel)
        m = '\n'.join([str(x) for x in self.commands])
        await self.bot.say(f'**Scheduled Actions:**\n```\n{m}\n```')
    
    
    
def setup(bot):
    bot.add_cog(Schedule(bot))



