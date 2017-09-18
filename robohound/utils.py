"""
utils.py

Utility functions and the bot'd utility mixin class
"""

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
            return isinstance(msg.channel, discord.PrivateChannel) and
                msg.content.lower() in ('yes', 'no')
        
        # Wait for the answer, and return the result
        answer = await self.bot_owner_get(message, check=c, timeout=timeout)
        answer = answer.casefold()
        return answer == 'yes'
