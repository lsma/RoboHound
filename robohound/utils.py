"""
utils.py

Utility functions and the bot'd utility mixin class
"""
import logging
from math import floor
from discord.ext.commands import check

logger = logging.getLogger('discord.RoboHound.utils')
logger.setLevel(logging.DEBUG)

class UtilityMixin:
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
            return isinstance(msg.channel, discord.PrivateChannel) and \
                msg.content.lower() in ('yes', 'no')
        
        # Wait for the answer, and return the result
        answer = await self.bot_owner_get(message, check=c, timeout=timeout)
        answer = answer.casefold()
        return answer == 'yes'

def is_bot_ower():
    """Decorator which makes sure the command invoker is the bot owner"""
    def predicate(ctx):
        logger.debug(f'is_bot_owner check for {ctx.command.name}')
        return ctx.message.author.id == ctx.bot.owner.id

    return check(predicate)
    
def format_timedelta(td, time_format):
    """
    Format a datetime.timedelta into an human-readable string
    Available items for time_format:
    {s}   seconds
    {S}   seconds (zero-padded)
    {m}   minutes
    {M}   minutes (zero-padded)
    {h}   hours
    {H}   hours (zero-padded)
    {d}   days
    {y}   years
    {st}  total seconds
    {mt}  total minutes
    {ht}  total hours
    {dt}  total days
    {yt}  total years
    """
    seconds = td.total_seconds()

    seconds_total = seconds

    minutes = int(floor(seconds / 60))
    minutes_total = minutes
    seconds -= minutes * 60

    hours = int(floor(minutes / 60))
    hours_total = hours
    minutes -= hours * 60

    days = int(floor(hours / 24))
    days_total = days
    hours -= days * 24

    years = int(floor(days / 365))
    years_total = years
    days -= years * 365
    
    seconds = int(seconds)

    return time_format.format(**{
        's':  seconds,
        'S':  str(seconds).zfill(2),
        'm':  minutes,
        'M':  str(minutes).zfill(2),
        'h':  hours,
        'H':  str(hours).zfill(2),
        'd':  days,
        'y':  years,
        'st': seconds_total,
        'mt': minutes_total,
        'ht': hours_total,
        'dt': days_total,
        'yt': years_total,
    })
