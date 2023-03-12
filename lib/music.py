from config import ytdl_config

import os
import asyncio
import discord
import youtube_dl

# youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_config.format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *args, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration')

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, url: str, *args, loop=None, stream=True):
        download = not stream
        loop = loop or asyncio.get_event_loop()

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download))
        if 'entries' in data:
            data = data['entries'][0]

        embed = discord.Embed(
            title='', 
            description=f'Queued [{data["title"]}]({data["webpage_url"]})', 
            color=discord.Color.green())
        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {
                'webpage_url': data['webpage_url'], 
                'requester': ctx.author, 
                'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)
    
    @classmethod
    async def regather_stream(cls, data, *args, loop=None):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info, url=data['webpage_url'], download=False)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)