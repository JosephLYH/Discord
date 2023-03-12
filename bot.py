# imports
import discord
from discord.ext import commands
from googleapiclient.discovery import build

import pafy
from lib import vlc

import random
import os

# local libraries
from config import config, conf

# global variables
be_funny = True
guild_playing = {}

# configs
bot = commands.Bot(
    command_prefix=config.COMMAND_PREFIX, 
    intents=discord.Intents.all())

youtube = build('youtube', 'v3', developerKey=conf.YOUTUBE_API_KEY)

# events
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(
        status=discord.Status.online, 
        activity=discord.Game(name=f'Music, type {config.COMMAND_PREFIX}help'))

@bot.command(name='join', help='Make the bot join your current voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f'You must join a voice channel first')
        return
    
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.channel.send(f'Joining {channel.name}')
    if be_funny:
        await ctx.channel.send(f'Time to ligma balls')

@bot.command(name='leave', help='Make the bot leave its current voice channel')
async def leave(ctx):
    voice_client = ctx.guild.voice_client

    if not voice_client:
        await ctx.send(f'Not currently in a channel')
        return
        
    await voice_client.disconnect()
    await ctx.channel.send(f'Left channel {voice_client.name}')

@bot.command(name='play', help='Search and play a song')
async def play(ctx, *args):
    song_name = ' '.join(args)
    if not song_name:
        if be_funny:
            await ctx.send(f'Enter a song name you dumbass')
            return
        
        await ctx.send('Please enter a song name')
        return

    voice_client = ctx.guild.voice_client
    if not voice_client:
        await ctx.author.voice.channel.connect()

    # find song on youtube
    request = youtube.search().list(
        part='id,snippet',
        q=song_name,
        maxResults=5,
        type='video')
    
    response = request.execute()

    search_results = []
    for video in response['items']:
        item = {
            'title': video['snippet']['title'],
            'url': f'https://www.youtube.com/watch?v={video["id"]["videoId"]}'}
        search_results.append(item)



    await ctx.send(f'Now playing: {search_results[0]["title"]}')
    guild_playing[ctx.guild.id] = True

@bot.command(name='pause', help='Pause the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if not voice_client:
        await ctx.send(f'Not currently in a channel')
        return

    if not voice_client.is_playing():
        await ctx.send('Not playing anything at the moment')
        return
    
    await voice_client.pause()  

@bot.command(name='stop', help='Stop the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if not voice_client:
        await ctx.send(f'Not currently in a channel')
        return

    if not voice_client.is_playing():
        await ctx.send('Not playing anything at the moment')
        return
    
    await voice_client.stop() 

# misc events
@bot.command(name='image', help='Send random image')
async def image_quokka(ctx, *args):
    arg = ' '.join(args)
    img_dir = 'img'

    img_files = os.listdir(os.path.join(img_dir, arg))
    img_file = random.choice(img_files)
    await ctx.send(file=discord.File(os.path.join(img_dir, arg, img_file)))

# error events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(f'{bot.user} does not have the correct role for this command')

bot.run(conf.TOKEN)