import asyncio
import itertools
import random
import sys
import traceback
from collections import defaultdict

import discord
from discord.ext import commands

from config import config
from lib.players import MusicPlayer
from lib.ytdl import YTDLSource

aliases = {
    'join': ['connect', 'j'],
    'play': ['p'],
    'pause': ['p-'],
    'resume': ['r'],
    'skip': ['s'],
    'remove': ['rem', 'rm'],
    'clear': ['clr', 'cl', 'c'],
    'queue': ['playlist', 'list', 'que', 'q'],
    'now playing': ['song', 'current', 'currentsong', 'playing', 'np'],
    'volume': ['vol', 'v'],
    'leave': ['disconnect', 'stop', 'bye', 'dc', 'lv', 'l'],
    'loop': ['lp'],
    'shuffle': ['sf'],
}

class VoiceConnectionError(commands.CommandError):
    '''Custom Exception class for connection errors.'''

class InvalidVoiceChannel(VoiceConnectionError):
    '''Exception for cases of invalid Voice Channels.'''

class MusicCog(commands.Cog, name='Only noobs need tutorial, do you even dark souls' if config.be_funny else 'Music Player'):
    __slots__ = ('bot', 'players')

    def __init__(self, bot):
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
            del self.loop[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
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

    def get_player(self, ctx):
        '''Retrieve the guild player, or generate one.'''
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='join', aliases=aliases['join'], description='Connects to voice')
    async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
        '''Connect to voice.
        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        This command also handles moving the bot to different channels.
        '''
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(title='', description=f'No channel to join. Please call `{config.command_prefix}join` from a voice channel.', color=discord.Color.green())
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
            await ctx.send('Time to ligma balls')

    @commands.command(name='play', aliases=aliases['play'], description='Search and play a music')
    async def play_(self, ctx, *args):
        search = ' '.join(args)
        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)

        await player.queue.put(source)

    @commands.command(name='pause', aliases=aliases['pause'],description='Pauses music')
    async def pause_(self, ctx):
        '''Pause the currently playing song.'''
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(title='', description="I'm currently not playing anything", color=discord.Color.green())
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send('**Paused** ⏸️')

    @commands.command(name='resume', aliases=aliases['resume'], description='Resumes music')
    async def resume_(self, ctx):
        '''Resume the currently paused song.'''
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send('**Resuming** ⏯️')

    @commands.command(name='skip', aliases=aliases['skip'], description='Skips to next song in queue')
    async def skip_(self, ctx):
        '''Skip the song.'''
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send('**Stopped** ⏹')
    
    @commands.command(name='remove', aliases=aliases['remove'], description='Removes specified song from queue')
    async def remove_(self, ctx, pos : int=None):
        '''Removes specified song from queue'''

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
                embed = discord.Embed(title='', description=f"Removed [{s['title']}]({s['url']}) [{s['requester'].mention}]", color=discord.Color.green())
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(title='', description=f"Could not find a track for '{pos}'", color=discord.Color.green())
                await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=aliases['clear'], description='Clears entire queue')
    async def clear_(self, ctx):
        '''Deletes entire queue of upcoming songs.'''

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('**Cleared** 💣')

    @commands.command(name='queue', aliases=aliases['queue'], description='Shows the queue')
    async def queue_info(self, ctx: commands):
        '''Retrieve a basic queue of upcoming songs.'''
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(title='', description='**Queue is empty**', color=discord.Color.green())
            return await ctx.send(embed=embed)

        seconds = vc.source.duration % (24 * 3600) 
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = '%dh %02dm %02ds' % (hour, minutes, seconds)
        else:
            duration = '%02dm %02ds' % (minutes, seconds)

        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
        fmt = '\n'.join(f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['url']}) | ` {duration} Requested by: {_['requester']}`\n" for _ in upcoming)
        fmt = f'\n__Now Playing__:\n[{vc.source.title}]({vc.source.url}) | ` {duration} Requested by: {vc.source.requester}`\n\n__Up Next:__\n' + fmt + f'\n**{len(upcoming)} songs in queue**'
        embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=discord.Color.green())
        embed.set_footer(text=f'{ctx.author.display_name}')

        await ctx.send(embed=embed)

    @commands.command(name='now playing', aliases=aliases['now playing'], description='Shows the current playing song')
    async def now_playing_(self, ctx):
        '''Display information about the currently playing song.'''
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(title='', description='I am currently not playing anything', color=discord.Color.green())
            return await ctx.send(embed=embed)
        
        seconds = vc.source.duration % (24 * 3600) 
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = '%dh %02dm %02ds' % (hour, minutes, seconds)
        else:
            duration = '%02dm %02ds' % (minutes, seconds)

        embed = discord.Embed(title='', description=f'[{vc.source.title}]({vc.source.web_url}) [{vc.source.requester.mention}] | `{duration}`', color=discord.Color.green())
        embed.set_author(icon_url=self.bot.user.avatar_url, name=f'Now Playing 🎶')
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=aliases['volume'], description="Changes music player's volume")
    async def change_volume(self, ctx, *, vol: float=None):
        '''Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        '''
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

    @commands.command(name='leave', aliases=aliases['leave'], description='Stops music and disconnects from voice')
    async def leave_(self, ctx):
        '''Stop the currently playing song and destroy the player.
        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        '''
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title='', description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👋')
        
        await ctx.send('Disconnected')        
        if config.be_funny:
            await ctx.send('Bye 9 bye')

        await self.cleanup(ctx.guild)

    @commands.command(name='loop', aliases=aliases['loop'], description='Trigger loop')
    async def loop_(self, ctx):
        '''Set loop
        '''
        vc = ctx.voice_client
        
        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)
        player.loop = not player.loop
        
        if not player.loop:
            await ctx.send('**Stopped looping** ↩') 
            return

        await ctx.send('**Looping** 🔁')

    @commands.command(name='shuffle', aliases=aliases['shuffle'], description='Trigger shuffle')
    async def shuffle_(self, ctx):
        '''Set shuffle
        '''
        vc = ctx.voice_client
        
        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)
        player.shuffle = not player.shuffle
        
        if not player.shuffle:
            await ctx.send('**Stopped shuffling** ➡') 
            return

        await ctx.send('**Shuffling** 🔀')

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))