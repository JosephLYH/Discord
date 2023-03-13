import asyncio
import random

import discord
from async_timeout import timeout


class MusicPlayer:
    __slots__ = ('bot', 'guild', 'channel', 'cog', 'queue', 'next', 'current', 'np', 'volume', 'loop', 'shuffle')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.current = None
        self.np = None
        self.volume = .5
        self.loop = False
        self.shuffle = False

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
            await self.bot.wait_until_ready()

            while not self.bot.is_closed():
                self.next.clear()

                try:
                    async with timeout(60*5):
                        source = await self.queue.get()
                        if self.shuffle:
                            qsize = self.queue.qsize()
                            for i in range(random.randint(0, max(0, qsize-1))):
                                temp = await self.queue.get()
                                await self.queue.put(temp)
                        if self.loop:
                            copy = await source.create_copy(source.ctx, source.data, source.filename)
                            await self.queue.put(copy)
                except asyncio.TimeoutError:
                    return self.destroy(self.guild)

                source.volume = self.volume
                self.current = source

                self.guild.voice_client.play(
                    source, 
                    after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                embed = discord.Embed(
                    title='Now playing', 
                    description=f'[{source.title}]({source.url})', 
                    color=discord.Color.green())
                self.np = await self.channel.send(embed=embed)
                await self.next.wait()

                # Make sure the FFmpeg process is cleaned up.
                source.cleanup()
                self.current = None
        
    def destroy(self, guild):
        return self.bot.loop.create_task(self.cog.cleanup(guild))