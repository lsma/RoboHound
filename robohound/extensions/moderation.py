import discord
import asyncio
from discord.ext import commands

from robohound.base import Extension


class Moderation(Extension):
    """moderation commands"""
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx,member_name:str):
        """Kick a member"""
        member = self.bot.get_user(ctx, member_name)
        if member:
            await self.bot.kick(member)
        else:
            await self.bot.say("Sorry, couldn't find that member")
    
        await self.bot.say(f'A OK! {member.name} has been kicked')
    
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, *,member_name:str):
        """Ban a member"""
        member = self.bot.get_user(ctx, member_name)
        if member:
            await self.bot.ban(member, 0)
        else:
            await self.bot.say("Sorry, couldn't find that member")
    
        await self.bot.say(f'A OK! {member.name} has been banned')
    
    
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def lban(self, ctx):
        """List all bans"""
        bans = await self.bot.get_bans(ctx.message.server)
        if bans:
            bans = '\n'.join(['{0.name} ({0.id})'.format(u) for u in bans])
            await self.bot.say(f'Current active bans:\n{bans}')
        else:
            await self.bot.say('Congratulations! You have no bans')
    
        
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(ban_members=True)
    async def mute(self, ctx,member_name:str):
        """Mute/unmute a member"""
        member = self.bot.get_user(ctx, member_name)
        if member:
            await self.bot.server_voice_state( \
                member, mute=not member.voice.mute)
        else:
            await self.bot.say("Sorry, couldn't find that member")
    
        await self.bot.say(f'A OK! {member.name} has been muted')
        
    
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(deafen_members=True)
    async def deafen(self, ctx,member_name:str):
        """Deafen/undeafen a member"""
        member = self.bot.get_user(ctx, member_name)
        if member:
            await self.bot.server_voice_state( \
                member, deafen=not member.voice.deaf)
        else:
            await self.bot.say("Sorry, couldn't find that member")
    
        await self.bot.say(f'A OK! {member.name} has been muted')
        
    
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx,member_name:str,role_name:str):
        """Add a user to a role"""
        member = self.bot.get_user(ctx, member_name)
        if member:
            role = self.get_role(ctx, role_name)
            if role:
                await self.bot.add_roles(member, role)
            else:
                await self.bot.say("Sorry, couldn't find that roll")
        else:
            await self.bot.say("Sorry, couldn't find that member")
    
        await self.bot.say(f'A OK!  I have added {member.name} to {role.name}')
    
    
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(manage_roles=True)
    async def unrole(self, ctx,member_name:str,role_name:str):
        """Remove a user from a role"""
        member = self.bot.get_user(ctx, member_name)
        if member:
            role = self.get_role(ctx, role_name)
            if role:
                await self.bot.remove_roles(member, role)
            else:
                await self.bot.say("Sorry, couldn't find that roll")
        else:
            await self.bot.say("Sorry, couldn't find that member")
    
        await self.bot.say( \
            f'A OK!  I have removed {member.name} from {role.name}')
    
    @commands.command(pass_context=True,no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, *args:str):
        """Delete lots messages"""
        await self.bot.type()
        
        limit = 5
        check = None
        m = None
        go = True
        
        if len(args) == 0:
            limit = 5
            m = 'Deleted 5 messages'
            
        elif len(args) == 1:
            arg = args[0]
            
            if arg.isdecimal():
                limit = int(arg)
                m = 'Deleted {} messages'.format(arg)
                
            else:
                member = self.bot.get_user(ctx, arg)
                if member:
                    limit = 5
                    check = lambda m: m.author == member
                    m = f'Deleted 5 messages from {member.name}'
                else:
                    go = False
                    m = f"I don't know what to do with {arg}"
            
        else:
            if args[0].isdecimal():
                limit = int(args[0])
                
                members = list(filter(lambda x: x.name in args[1:] or
                                           x.mention in args[1:] or
                                           x.nick in args[1:],
                                ctx.message.server.members))
                check = lambda m: m.author in members
                
                m = 'Deleted {} messages from {}'.format(args[0], ','.join(args[1:]))
            
            else:
                go = False
                m = 'First argument must specify the number of messages to ' + \
                    'delete'
            
        if go:
            if limit > 10:
                warning =  'You are about to delete alot of messages.'
                warning += '\nPlease confirm with `DELETE` in 20 seconds'
                reply = await self.bot.say(warning)
                confirm = await self.bot.wait_for_message(timeout=20,
                    author=ctx.message.author, channel=ctx.message.channel,
                    content='DELETE')
                await self.bot.delete_message(reply)
                if not confirm:
                    return
                else:
                    await self.bot.delete_message(confirm)
                await asyncio.sleep(0.5)
                
            await self.bot.delete_message(ctx.message)
            await asyncio.sleep(0.5)
            await self.bot.purge_from(
                ctx.message.channel, limit=limit, check=check)
                    
        reply = await self.bot.say(m)
        await asyncio.sleep(5)
        await self.bot.delete_message(reply)

    
def setup(bot):
    bot.add_cog(Moderation(bot))

