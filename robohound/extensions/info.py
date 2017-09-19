import discord
import asyncio
from discord.ext import commands
from .utils import checks


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
        await self.bot.send_typing(ctx.message.channel)
        m = '**Server information**' + self.get_info(ctx.message.server)
        await self.bot.say(m)
        
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


