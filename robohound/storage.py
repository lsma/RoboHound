"""
storage.py

Interface class between the bot/plugins and the database
Mostly stolen from mee6
"""
import asyncio
import aioredis

class Db:
    def __init__(self, address, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._loop.create_task(self.start(address))
    
    async def start(self, address):
        self.redis = await aioredis.create_redis(
            address, loop=self._loop, encoding='utf-8')
    
    def get_namespace(self, n, sep=':'):
        return Storage(n + sep, self.redis, self)
        
        
class Storage():
    """Adds a prefix to Redis"""
    def __getitem__(self, key):
        return self.get_namespace(key)
    
    def __init__(self, namespace, redis, parent):
        self.namespace = namespace
        self.redis = redis
        self.parent = parent
        
    def get_namespace(self, n, sep=':'):
        new_n = f'{self.namespace}{n}{sep}'
        return Storage(new_n, self.redis, self)
    
    async def bgsave(self):
        return await self.redis.bgsave()
        
    async def keys(self, pattern):
        p = self.namespace + pattern
        return await self.redis.keys(p)
        
    async def set(self, key, value, expire=0):
        key = self.namespace + key
        return await self.redis.set(
            key,
            value,
            expire=expire
        )

    async def get(self, key):
        key = self.namespace + key
        return await self.redis.get(key)

    async def smembers(self, key):
        key = self.namespace + key
        return await self.redis.smembers(key)

    async def srem(self, key, value):
        key = self.namespace + key
        return await self.redis.srem(key, value)

    async def sadd(self, key, member, *members):
        key = self.namespace + key
        return await self.redis.sadd(key, member, *members)

    async def delete(self, key, *keys):
        key = self.namespace + key
        return await self.redis.delete(key, *keys)

    async def sort(self, key, *get_patterns, by=None, offset=None, count=None,
                   asc=None, alpha=False, store=None):
        key = self.namespace + key
        if by:
            by = self.namespace + by
        return await self.redis.sort(key, *get_patterns, by=by, offset=offset,
                                     count=None, asc=None, alpha=False,
                                     store=None)

    async def ttl(self, key):
        key = self.namespace + key
        return await self.redis.ttl(key)

    async def expire(self, key, timeout):
        key = self.namespace + key
        return await self.redis.expire(key, timeout)

    async def incr(self, key):
        key = self.namespace + key
        return await self.redis.incr(key)

    async def incrby(self, key, amount):
        key = self.namespace + key
        return await self.redis.incrby(key, amount)

    async def setnx(self, key, value):
        key = self.namespace + key
        return await self.redis.setnx(key, value)

    async def lpush(self, key, value, *values):
        key = self.namespace + key
        return await self.redis.lpush(key, value, *values)

    async def lpop(self, key, *values):
        key = self.namespace + key
        return await self.redis.lpop(key, *values)

    async def llen(self, key):
        key = self.namespace + key
        return await self.redis.llen(key)
        
    async def lrange(self, key, start, stop):
        key = self.namespace + key
        return await self.redis.lrange(key, start, stop)

    async def lrem(self, key, count, value):
        key = self.namespace + key
        return await self.redis.lrem(key, count, value)

    async def lset(self, key, index, value):
        key = self.namespace + key
        return await self.redis.lset(key, index, value)

    async def ltrim(self, start, stop):
        return await self.redis.ltrim(start, stop)

    async def rpush(self, key, value, *values):
        key = self.namespace + key
        return await self.redis.rpush(key, value, *values)        

    async def rpop(self, key, *values):
        key = self.namespace + key
        return await self.redis.rpop(key, *values)
