import asyncio
import os

import discord
import youtube_dl

from config import ytdl_config

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_config.format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *args, ctx, data, filename):
        super().__init__(source)
        self.filename = filename

        self.ctx = ctx
        self.requester = ctx.author
        
        self.data = data
        self.title = data.get('title')
        self.alt_title = data.get('alt_title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration')

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, loop=None):
        loop = loop or asyncio.get_event_loop()

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search))
        if 'entries' in data:
            data = data['entries'][0]

        source = ytdl.prepare_filename(data)

        return cls(
            discord.FFmpegPCMAudio(source), 
            ctx=ctx, 
            data=data,
            filename=source)
    
    @classmethod
    async def create_copy(cls, ctx, data, filename):
        return cls(
            discord.FFmpegPCMAudio(filename), 
            ctx=ctx,
            data=data,
            filename=filename)