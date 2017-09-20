import os
import random
import aiohttp
import async_timeout
import discord
import asyncio
from discord.ext import commands

from robohound.utils import fetch
from robohound.base import Extension


class Amusement(Extension):
    """Pointless or recreational commands"""
    NO_EMOJI = "At this time, Discord does not allow bots to create emoji."
        
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
    
    
    @commands.command()
    async def fortune(self):
        """Pick something from a list of words"""
        await self.bot.type()
        
        app = await asyncio.create_subprocess_exec( \
            'fortune', '-s', stdout=asyncio.subprocess.PIPE, loop=self.bot.loop)
        reply = await app.communicate(None)
        await app.wait()
        
        f = reply[0].decode('utf-8').rstrip()
        await asyncio.sleep((random.random()+1)*2)
        await self.bot.say(f)
        
    @commands.command(pass_context=True)
    @commands.has_permissions(manage_emojis=True)
    async def emojify(self, ctx):
        """Make the last posted image into an emoji (Blocked by discord atm)"""
        logs = self.bot.logs_from(ctx.message.channel, limit=10)
        async for message in logs:
            if message.attachments:
                att = message.attachments[-1]
                name = att['filename'].split('.')[0]
                
                response = await fetch(att['url'])
                
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


