"""
launch.py

Launch the bot
"""
import os
import logging

from robohound import RoboHound

token = os.getenv('RH_TOKEN')
redis = os.getenv('RH_REDIS_PORT')
debug = os.getenv('RH_DEBUG')

logging.basicConfig(level=logging.INFO)
logging.info('Launching RoboHound')

logger = logging.getLogger('RoboHound')
if debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

bot = RoboHound(
    redis_address = ('localhost', int(redis)),
    log = logger,
)
bot.run(token)
