import datetime
import discord
import asyncio
from discord.ext import commands

from robohound.utils import format_timedelta

class Information:
    """Commands for getting information about discord objects"""
    BL_SERVER = []
    BL_CHANNEL = []
    BL_USER = []
    
    def __init__(self, bot):
        self.bot = bot
    
    def get_info(self, s):
        m = ''
        for p in dir(s):
            if not p.startswith('_'):
                i = getattr(s, p)
                if not callable(i):
                    val = str(i).replace('`', '\`')
                    m += f'\n{p}:`{val}`'
        return m
        
    
    @commands.group(pass_context=True)
    async def info(self, ctx):
        """All info commands"""
        if ctx.invoked_subcommand is None:
            await self.bot.say(f'Try `{self.bot.command_prefix}help info`')
    
    @info.command(pass_context=True,no_pm=True)
    async def server(self, ctx):
        """Show information about the server"""
        header = await self.bot.say('Comming right up...')
        
        server = ctx.message.server
        created_at = server.created_at
        age = format_timedelta(
            datetime.datetime.now() - created_at,
            '{y} years, {d} days, {h} hours, {m} minutes, {s} seconds',
        )
        
        m = '**Server Information:**'
        m += f'\nServer name: {server.name}'
        m += '\nChannels: '
        m += ', '.join(ch.mention for ch in server.channels)
        m += f'\nDefault channel: {server.default_channel.mention}'
        m += '\nCreated: {:%Y-%m-%d %H:%M:%S}'.format(created_at)
        m += f'\nServer age: {age}'
        
        await self.bot.edit_message(header, new_content=m)
        
        
    @info.command(pass_context=True,no_pm=True)
    async def channel(self, ctx):
        """Show information about the channel"""
        await self.bot.send_typing(ctx.message.channel)
        m = '**Channel information**' + self.get_info(ctx.message.channel)
        await self.bot.say(m)
        
    @info.command(pass_context=True)
    async def user(self, ctx):
        """Show information about the user"""
        await self.bot.send_typing(ctx.message.channel)
        m = '**User information**' + self.get_info(ctx.message.author)
        await self.bot.say(m)
        
        
    
def setup(bot):
    bot.add_cog(Information(bot))


