"""
launch.py

Launch the bot
"""
import os
import logging

from robohound import RoboHound


# Get environment variables
uname = os.getenv('RH_BOT_USERNAME')
token = os.getenv('RH_BOT_TOKEN')

client_id = os.getenv('RH_BOT_CLIENT_ID')
client_secret = os.getenv('RH_BOT_CLIENT_SECRET')

owner_id = os.getenv('RH_OWNER_ID')

redis = os.getenv('RH_REDIS_PORT')

debug = os.getenv('RH_DEBUG')


# Set up logging
logging.basicConfig(level=logging.INFO)
logging.info('Launching RoboHound')

logger = logging.getLogger('discord')

# Start the bot
bot = RoboHound(
    redis_address = ('localhost', int(redis)),
    log = logger,
    owner_id = owner_id,
    debug = debug,
)
bot.run(token)
