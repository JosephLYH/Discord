import asyncio
import itertools
import random
import sys
import traceback
from collections import defaultdict

import discord
from discord.ext import commands

from config import config
from lib.common import duration2time
from lib.players import MusicPlayer
from lib.ytdlp import YTDLPSource

aliases = {
    'join': ['connect', 'j'],
    'play': ['p'],
    'pause': ['p-', 'stop'],
    'resume': ['r'],
    'skip': ['s'],
    'remove': ['rem', 'rm'],
    'clear': ['clr', 'cl', 'c'],
    'queue': ['playlist', 'list', 'que', 'q'],
    'now playing': ['song', 'current', 'currentsong', 'playing', 'np'],
    'volume': ['vol', 'v'],
    'leave': ['disconnect', 'bye', 'dc', 'lv', 'l'],
    'loop': ['lp'],
    'shuffle': ['sf'],
}

class VoiceConnectionError(commands.CommandError):
    '''Custom Exception class for connection errors.'''

class InvalidVoiceChannel(VoiceConnectionError):
    '''Exception for cases of invalid Voice Channels.'''

class MusicCog(commands.Cog, name='Music Player' if not config.be_funny else 'Only noobs need tutorial, do you even dark souls'):
    __slots__ = ('bot', 'players')

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx: commands.Context):
        '''A local check which applies to all commands in this cog.'''
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        '''A local error handler for all errors arising from commands in this cog.'''
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx: commands.Context):
        '''Retrieve the guild player, or generate one.'''
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == self.bot.user.id:
            return
        
        if before.channel and before.channel.id in map(lambda x: x.channel.id, self.bot.voice_clients) and len(before.channel.members) == 1:
            await self.cleanup(before.channel.guild)

    @commands.command(name='join', aliases=aliases['join'], help='Connects to voice' if not config.be_funny else 'Joins to disrupt the voice chat')
    async def connect_(self, ctx: commands.Context, *, channel: discord.VoiceChannel=None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(title='', description=f'No channel to join. Please call `{config.music_cmd_prefix}join` from a voice channel.', color=discord.Color.green())
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👍')
        
        await ctx.send(f'**Joined** 🎶 `{channel}`')
        if config.be_funny:
            await ctx.send('**Time to dancin first** ╰(*°▽°*)╯')
            await ctx.invoke(self.play_, 'https://www.youtube.com/watch?v=Cjp6RVrOOW0')

    @commands.command(name='play', aliases=aliases['play'], help='Searchs and plays music' if not config.be_funny else 'Pretty self explanatory, do you use brain')
    async def play_(self, ctx: commands.Context, *args):
        search = ' '.join(args)
        if not search:
            if config.be_funny:
                return await ctx.send(f'Enter a music you dumbass')
        
            return await ctx.send('Enter a music')

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        if player.current:
            embed = discord.Embed(title='', description=f'Waiting to add to queue', color=discord.Color.green())
            await ctx.send(embed=embed)            
            return await player.waiting.put([ctx, search])
        
        source = await YTDLPSource.create_source(ctx, search, loop=self.bot.loop)
        await player.queue.put(source)

    @commands.command(name='pause', aliases=aliases['pause'], help='Pauses the playing music')
    async def pause_(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(title='', description="I'm currently not playing anything", color=discord.Color.green())
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send('**Paused** ⏸️')

    @commands.command(name='resume', aliases=aliases['resume'], help='Resumes the paused music')
    async def resume_(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send('**Resuming** ⏯️')

    @commands.command(name='skip', aliases=aliases['skip'], help='Skips the current music')
    async def skip_(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send('**Skipped** ⏭')
    
    @commands.command(name='remove', aliases=aliases['remove'], help='Removes specified song from queue by index')
    async def remove_(self, ctx: commands.Context, pos : int=None):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if pos == None:
            player.queue._queue.pop()
        else:
            try:
                s = player.queue._queue[pos-1]
                del player.queue._queue[pos-1]
                embed = discord.Embed(title='', description=f"**Removed** [{s['title']}]({s['url']}) [{s['requester'].mention}]", color=discord.Color.green())
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(title='', description=f"Could not find a track for '{pos}'", color=discord.Color.green())
                await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=aliases['clear'], help='Clears entire queue')
    async def clear_(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('**Cleared** 💣')

    @commands.command(name='queue', aliases=aliases['queue'], help='Shows the queue')
    async def queue_info(self, ctx: commands):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(title='', description='I am currently not playing anything', color=discord.Color.green())
            return await ctx.send(embed=embed)
        
        fmt = f'\n__Now Playing__:\n[{vc.source.title}]({vc.source.url}) | `{duration2time(vc.source.duration)} Requested by: {vc.source.requester}`\n\n__Up Next:__\n'
        if not player.queue.empty():
            upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
            fmt += '\n'.join(f"`{idx + 1}.` [{_['title']}]({_['url']}) | ` {duration2time(_['duration'])} Requested by: {_['requester']}`\n" for idx, _ in enumerate(upcoming))
            fmt += f'\n**{len(upcoming)} songs in queue**\n\n'   
        
        if not player.waiting.empty():
            upcoming = list(itertools.islice(player.waiting._queue, 0, int(len(player.waiting._queue))))         
            fmt += '\n'.join(f"`{idx + 1}.` [{search}] | ` Unknown duration Requested by: {ctx.author}`\n" for idx, [ctx, search] in enumerate(upcoming))
            fmt += f'\n**{len(upcoming)} songs in waiting to be searched**\n\n'
        
        if player.queue.empty() and player.waiting.empty():
            fmt += '**Queue is empty**\n\n'

        embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt.rstrip(), color=discord.Color.green())

        await ctx.send(embed=embed)

    @commands.command(name='now playing', aliases=aliases['now playing'], help='Displays information about the current song')
    async def now_playing_(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(title='', description='I am currently not playing anything', color=discord.Color.green())
            return await ctx.send(embed=embed)

        embed = discord.Embed(title='', description=f'[{vc.source.title}]({vc.source.url}) | `{duration2time(vc.source.duration)} Requested by: {vc.source.requester}`', color=discord.Color.green())
        embed.set_author(name='Now Playing 🎶')
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=aliases['volume'], help="Changes the music player volume")
    async def change_volume(self, ctx: commands.Context, *, vol: float=None):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not currently connected to voice", color=discord.Color.green())
            return await ctx.send(embed=embed)
        
        if not vol:
            embed = discord.Embed(title='', description=f'🔊 **{(vc.source.volume)*100}%**', color=discord.Color.green())
            return await ctx.send(embed=embed)

        if not 0 < vol < 101:
            embed = discord.Embed(title='', description='Please enter a value between 1 and 100', color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(title='', description=f'**`{ctx.author}`** set the volume to **{vol}%**', color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name='leave', aliases=aliases['leave'], help='Stops music and disconnects from voice')
    async def leave_(self, ctx: commands.Context):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👋')
        
        await ctx.send('**Disconnected**')        
        if config.be_funny:
            await ctx.send('**Bye 9 bye**')

        await self.cleanup(ctx.guild)

    @commands.command(name='loop', aliases=aliases['loop'], help='Triggers loop')
    async def loop_(self, ctx: commands.Context):
        vc = ctx.voice_client
        
        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)
        player.loop = not player.loop
        
        if not player.loop:
            return await ctx.send('**Stopped looping** ↩') 

        await ctx.send('**Looping** 🔁')

    @commands.command(name='shuffle', aliases=aliases['shuffle'], help='Triggers shuffle')
    async def shuffle_(self, ctx: commands.Context):
        vc = ctx.voice_client
        
        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)
        player.shuffle = not player.shuffle
        
        if not player.shuffle:
            return await ctx.send('**Stopped shuffling** ➡') 

        await ctx.send('**Shuffling** 🔀')

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))