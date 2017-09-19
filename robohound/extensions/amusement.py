import os
import random
import aiohttp
import async_timeout
import discord
import asyncio
from discord.ext import commands
from .utils import checks

async def fetch(session, url):
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            return await response.text()

class Amusement:
    """Pointless or recreational commands"""
    NO_EMOJI = "At this time, Discord does not allow bots to create emoji."

    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def coin(self):
        """Flip a coin"""
        if random.randint(0,1):
            await self.bot.say('Heads!')
        else:
            await self.bot.say('Tails!')
    
    @commands.command(pass_context=True)
    async def pick(self, ctx, *args:str):
        """Pick something from a list of words"""
        await self.bot.say('I choose...')
        await self.bot.send_typing(ctx.message.channel)
        await asyncio.sleep((random.random()+1)*2)
        await self.bot.say('`{}`'.format(random.choice(args)))
    
    
    @commands.command(pass_context=True)
    async def fortune(self, ctx):
        """Pick something from a list of words"""
        await self.bot.send_typing(ctx.message.channel)
        try:
            app = os.popen('fortune')
            f = app.read()
            app.close()
        except Exception as e:
            f = 'Go away! No fortunes today!'
        await asyncio.sleep((random.random()+1)*2)
        await self.bot.say(f)
        
    @commands.command(pass_context=True)
    @checks.admin_or_permissions(manage_emojis=True)
    async def emojify(self, ctx):
        """Make the last posted image into an emoji (Blocked by discord atm)"""
        logs = await self.bot.logs_from(ctx.message.channel, limit=10)
        for message in logs:
            if message.attachments:
                att = message.attachments[-1]
                name = att['filename'].split('.')[0]
                
                async with aiohttp.ClientSession() as session:
                    response = await fetch(session, att['url'])
                
                try:
                    await self.bot.create_custom_emoji(message.server, name=name,
                                            image=bytes(response.content))
                except discord.errors.Forbidden as err:
                    print(str(err))
                    if 'support@discordapp.com' in str(err):
                        await self.bot.say(amusementCog.NO_EMOJI)
                        return
                        
                await self.bot.say('Emoji added!')
                return
        await self.bot.say("I couldn't find an image in the last few messages")
                
    
def setup(bot):
    bot.add_cog(Amusement(bot))


