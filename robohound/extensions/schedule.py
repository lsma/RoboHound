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
from concurrent.futures import CancelledError
from discord.ext import commands
from pytz import timezone

from robohound.base import Extension


class Saved:
    """Base class for saved items"""
    def __str__(self):
        return f'{self.author.name} scheduled "{self.content}" for ' + \
            f'{self.when:%a, %b %d, %Y at %H:%M:%S %Z}'
        
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
                
        self._canceled = False
        self._completed = False
    
    def format(self, with_channel=False, with_server=False):
        m = str(self)
        if with_channel:
            m += f' in {self.channel.mention}'
        if with_server:
            m += f' in `{self.channel.server.name}`'
        return m
    
    @property
    def wait_time(self):
        now = datetime.datetime.now(tz=self.when.tzinfo)
        return (self.when - now).total_seconds()
    
    @property
    def overdue(self):
        return (self.wait_time < 0)
        
    def cancel(self):
        self._canceled = True
        
    @property
    def completed(self):
        return self._completed
        
    @property
    def canceled(self):
        return self._canceled
        
    async def execute(self):
        if not self.overdue and not self.canceled:
            await asyncio.sleep(self.wait_time)
            return 1
        
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
        resp = await super().execute()
        if resp:
            message = await self.bot.send_message(self.channel, self.content)
            await self.bot.add_reaction(message, '\u23F2')
            self._completed = True
        return resp



class SavedCommand(Saved):
    """This object holds a command for the bot to execute at a certain time"""
    
    def __init__(self, bot, cmd, when, channel, author):
        super().__init__(bot, cmd, when, channel, author)
            
    
    async def execute(self):
        resp = await super().execute()
        if resp:
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
            await self.bot.send_message(self.channel, 'Executing ' + \
                f'``{self.content}`` (schedule by {self.author.mention})')
            await self.bot.process_commands(m)
            self._completed = True
        return resp




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
    
    CONTENT_LIMIT = 960
    
    
    def __init__(self, bot, *args, **kwargs):
        super().__init__(bot)
        
        self.cal = parsedatetime.Calendar()
        
        self.ready = False
        self.bot.loop.create_task(self.load())
        
        self.indices  = {'author':{}, 'channel':{}, 'server':{}}
        self._tasks = {}
    
    
    def parse(self, server, message):
        """Parse a time string like 'tomorrow at 3PM' into a datetime"""
        tz = timezone(self.TZ_CONVERT[server.region])
        dt, _ = self.cal.parseDT(datetimeString=message)
        return dt.astimezone(tz)
        
        
    async def load(self):
        """Load commands from a file"""
        await self.bot.wait_until_ready()
        
        failed = {}
        total_items = await self.storage.llen('saved')
        self.log.info(f'Loading saved items ({total_items})')
        while total_items > 0:
            total_items -= 1
            
            data = await self.storage.rpop('saved')
            cur = self.decode_saved(**json.loads(data))
            
            if cur.overdue:
                if cur.channel in failed:
                    failed[cur.channel] += 1
                else:
                    failed[cur.channel] = 1
                self.log.debug(f'Ignored overdue item "{cur.content}"')
            else:
                self.bot.loop.create_task(self.add_saved(cur,save_db=False))
        
        self.ready = True
        
        for ch in failed:
            await self.bot.send_message(
                ch,
                'Apologies, but I had some downtime, and missed ' + \
                '{} scheduled actions!'.format(failed[ch]),
            )
        
        if self.bot.debug:
            # We'll need to re-save the db after weeding out overdue actions
            async def post_load_db_save():
                await asyncio.sleep(10)
                self.log.debug('Post-load db save')
                await self.storage.bgsave()
                
            self.bot.loop.create_task(post_load_db_save())
    
    
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
    
    def _indices_add(self, s):
        """Add a Saved object to the search indicies"""
        self.log.debug(f'Adding item "{s.content}" to the indicies')
        if s.author.id in self.indices['author']:
            self.indices['author'][s.author.id].append(s)
        else:
            self.indices['author'][s.author.id] = [s,]

        if s.channel.id in self.indices['channel']:
            self.indices['channel'][s.channel.id].append(s)
        else:
            self.indices['channel'][s.channel.id] = [s,]
            
        if s.channel.server.id in self.indices['server']:
            self.indices['server'][s.channel.server.id].append(s)
        else:
            self.indices['server'][s.channel.server.id] = [s,]
            
    def _indices_remove(self, s):
        """Remove a Saved object from the search indicies"""
        self.log.debug(f'Removing item "{s.content}" from the indicies')
        self.indices['author'][s.author.id].remove(s)
        self.indices['channel'][s.channel.id].remove(s)
        self.indices['server'][s.channel.server.id].remove(s)
    
    async def _db_add_saved_item(self, s, save_db=True):
        """
        Save a Saved object the database
        Note that this method will not check to see if the item is already on
        the database, so it will create duplicates
        """
        self.log.debug(f'Saving item "{s.content}" to the database')
        data = json.dumps(s.encode())
        
        # Put the saved item into the database in case the bot dies
        await self.storage.lpush('saved', data)
        if self.bot.debug and save_db:
            await self.storage.bgsave()
        self.log.info(f'Added saved item "{s.content}"')
        
        
    async def _db_remove_saved_item(self, s):
        """Remove a Saved object from the database"""
        self.log.debug(f'Removing item "{s.content}" from the database')
        data = json.dumps(s.encode())
        
        responce = await self.storage.lrem('saved', 1, data)
        
        if responce:
            self.log.info(f'Removed "{s.content}" from database')
        else:
            e = f'Failed to remove "{s.content}" from database: ' + \
                'no such entry'
            self.log.warning(e)
            raise Exception(e)
        
    
    async def _execute(self, s):
        self.log.debug(f'Executing item "{s.content}"')
        try:
            result = await s.execute()
        finally:
            #remove the item after 
            self._indices_remove(s)
            await self._db_remove_saved_item(s)
        
    
    async def add_saved(self, s, save_db=True):
        """
        Makes a new saved item
        This coroutine will not complete until the saved item has been executed
        """
        self.log.debug(f'Adding new item: "{s.content}"')
        await self._db_add_saved_item(s, save_db)
        self._indices_add(s)
        
        self._tasks[s] = \
            self.bot.loop.create_task(self._execute(s))
    
    
    def _cancel_saved(self, s):
        self._tasks[s].cancel()
        
    
    @commands.group(pass_context=True,invoke_without_command=True)
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
        
        if len(content) > self.CONTENT_LIMIT:
            mention = ctx.message.author.mention
            await self.bot.say(f"Sorry {mention}, that's too long to remember.")
            return
            
        
        data = self.CMD.match(ctx.message.content)
        if data:
            content = data['content']
            when = self.parse(ctx.message.server, data['when'])
            
            saved_item = self.decode_saved(
                content = content,
                when = when,
                channel = ctx.message.channel,
                author = ctx.message.author,
            )
            
            self.bot.loop.create_task(self.add_saved(saved_item))
            
            await self.bot.say(
                f'I will excute `{content}` on ' + \
                f'{when:%a, %b %d, %Y at %H:%M:%S}', delete_after=6)
            
        else:
            await self.bot.say("I don't understand.")
            await self.bot.say('Make sure your command looks ' + \
                f'like this:\n``!{ctx.command} `[some command]` ' + \
                f'[some time]``')
            await self.bot.say(f'Try `!help {ctx.command}`')
        
        
    @schedule.command(pass_context=True)
    async def delete(self, ctx):
        """Delete an upcoming scheduled action made by you"""
        await self.bot.say('This command is under construction')
        
    @schedule.group(pass_context=True)
    async def list(self, ctx):
        """Lists all your scheduled actions, or by channel or server"""
        if ctx.invoked_subcommand is None:
            await self.bot.say('You must use a sub-command')
            sub_commands = '`, `'.join(self.list.commands)
            await self.bot.say(f'Available sub-commands: `{sub_commands}`')
    
    
    @list.command(pass_context=True)
    async def channel(self, ctx):
        """List all upcoming scheduled actions you've made in this channel"""
        self.bot.type()
        by_author = set(self.indices['author'].get(ctx.message.author.id, []))
        by_channel = set(self.indices['channel'].get(ctx.message.channel.id,[]))
        items = list(by_author & by_channel)
        items.sort(key=lambda s: s.when.timestamp())
        if items:
            m = '\n'.join(str(i) for i in items)
            await self.bot.say(m)
        else:
            await self.bot.say('No scheduled items',delete_after=6)
        
    @list.command(pass_context=True)
    async def server(self, ctx):
        """List all upcoming scheduled actions you've made in this server"""
        self.bot.type()
        by_author = set(self.indices['author'].get(ctx.message.author.id, []))
        by_server = set(self.indices['server'].get(ctx.message.server.id,[]))
        items = list(by_author & by_server)
        items.sort(key=lambda s: s.when.timestamp())
        if items:
            m = '\n'.join(i.format(True) for i in items)
            await self.bot.say(m)
        else:
            await self.bot.say('No scheduled items',delete_after=6)
        
    @list.command(pass_context=True)
    async def all(self, ctx):
        """List all upcoming scheduled actions you've made anywhere"""
        self.bot.type()
        items = self.indices['author'].get(ctx.message.author.id, [])
        items.sort(key=lambda s: s.when.timestamp())
        if items:
            m = '\n'.join(i.format(True, True) for i in items)
            await self.bot.say(m)
        else:
            await self.bot.say('No scheduled items',delete_after=6)
        
    @schedule.group(pass_context=True)
    async def admin(self, ctx):
        """Commands for server admins to manage scheduled actions"""
        if ctx.invoked_subcommand is None:
            await self.bot.say('You must use a sub-command')
            sub_commands = '`, `'.join(self.schedule.admin.commands)
            await self.bot.say(f'Available sub-commands: `{sub_commands}`')
     
    #@admin.command(pass_context=True)
    #async def delete(self, ctx):
        #"""Delete an upcoming scheduled action made in this server"""
        #await self.bot.say('This command is under construction')
        
    @admin.group(pass_context=True)
    async def list(self, ctx):
        """List all scheduled actions by channel, or in the whole server"""
        if ctx.invoked_subcommand is None:
            await self.bot.say('You must use a sub-command')
            sub_commands = '`, `'.join(self.schedule.admin.list.commands)
            await self.bot.say(f'Available sub-commands: `{sub_commands}`')
    
    @list.command(pass_context=True)
    async def channel(self, ctx):
        """List all upcoming scheduled actions made in this channel"""
        self.bot.type()
        items = self.indices['channel'].get(ctx.message.channel.id, [])
        items.sort(key=lambda s: s.when.timestamp())
        if items:
            m = '\n'.join(i.format(True) for i in items)
            await self.bot.say(m)
        else:
            await self.bot.say('No scheduled items',delete_after=6)
            
    @list.command(pass_context=True)
    async def server(self, ctx):
        """List all upcoming scheduled actions made in this server"""
        self.bot.type()
        items = self.indices['server'].get(ctx.message.server.id, [])
        items.sort(key=lambda s: s.when.timestamp())
        if items:
            m = '\n'.join(i.format(True) for i in items)
            await self.bot.say(m)
        else:
            await self.bot.say('No scheduled items',delete_after=6)
        
    #@admin.command(pass_context=True)
    #async def delete_all(self, ctx):
        #"""Delete all upcoming scheduled actions made in this server"""
        #await self.bot.say('This command is under construction')
        
    #@admin.command(pass_context=True)
    #async def blacklist(self, ctx):
        #"""
        #Block specific user(s) or role(s) from using !schedule
        #This puts the schedule extension into blacklist mode for the server:
        #All members can use the command, except those who have been blacklisted.
        #"""
        #await self.bot.say('This command is under construction')
        
    #@admin.command(pass_context=True)
    #async def unblacklist(self, ctx):
        #"""
        #Remove specific user(s) or role(s) from the blacklist
        #This puts the schedule extension into blacklist mode for the server.
        #"""
        #await self.bot.say('This command is under construction')
    
    #@admin.command(pass_context=True)
    #async def whitelist(self, ctx):
        #"""
        #Allow specific user(s) or role(s) to use !schedule
        #This puts the schedule extension into whitelist mode for the server:
        #only members who have been whitelisted can use the command.
        #"""
        #await self.bot.say('This command is under construction')
    
    #@admin.command(pass_context=True)
    #async def unwhitelist(self, ctx):
        #"""
        #Remove specific user(s) or role(s) from the whitelist
        #This puts the schedule extension into whitelist mode for the server.
        #"""
        #await self.bot.say('This command is under construction')
    
    

def setup(bot):
    bot.add_cog(Schedule(bot))



