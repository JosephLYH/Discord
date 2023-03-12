# local library
from config import config, conf, ytdl_config
from lib.music import YTDLSource

# library
import os
import random

# api library
import discord
from discord.ext import commands
from googleapiclient.discovery import build

# code
bot = commands.Bot(
    command_prefix=config.command_prefix, 
    intents=discord.Intents.all())

youtube = build('youtube', 'v3', developerKey=conf.YOUTUBE_API_KEY)

# events
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(
        status=discord.Status.online, 
        activity=discord.Game(name=f'Music, type {config.command_prefix}help'))

@bot.command(name='join', aliases=['j'], help='Make the bot join your current voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f'You must join a voice channel first')
        return
    
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.channel.send(f'Joining {channel.name}')
    if config.be_funny:
        await ctx.channel.send(f'Time to ligma balls')

@bot.command(name='leave', help='Make the bot leave its current voice channel')
async def leave(ctx):
    voice_client = ctx.guild.voice_client

    if not voice_client:
        await ctx.send(f'Not currently in a channel')
        return
        
    await voice_client.disconnect()
    await ctx.channel.send(f'Left channel {voice_client.name}')

@bot.command(name='play', aliases=['p'], help='Search and play a music')
async def play(ctx, *args):
    music_name = ' '.join(args)
    if not music_name:
        if config.be_funny:
            await ctx.send(f'Enter a music name you dumbass')
            return
        
        await ctx.send('Enter a music name')
        return

    voice_client = ctx.guild.voice_client
    if not voice_client:
        await ctx.author.voice.channel.connect()
        voice_client = ctx.guild.voice_client
        if config.be_funny:
            await ctx.channel.send(f'Time to ligma balls')

    # request = youtube.search().list(
    #     part='id,snippet',
    #     q=music_name,
    #     maxResults=1,
    #     type='video')
    
    # response = request.execute()

    # search_results = []
    # for video in response['items']:
    #     item = {
    #         'title': video['snippet']['title'],
    #         'url': f'https://www.youtube.com/watch?v={video["id"]["videoId"]}'}
    #     search_results.append(item)

    # play music
    source = await YTDLSource.create_source(ctx, music_name, stream=False)
    voice_client.stop()
    voice_client.play(source)

@bot.command(name='pause', help='Pause the music')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if not voice_client:
        await ctx.send(f'Not currently in a channel')
        return

    if not voice_client.is_playing():
        await ctx.send('Not playing anything at the moment')
        return
    
    await voice_client.pause()  

@bot.command(name='resume', help='Resume the music')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if not voice_client:
        await ctx.send(f'Not currently in a channel')
        return
    
    await voice_client.resume()  

@bot.command(name='stop', help='Stop the music')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if not voice_client:
        await ctx.send(f'Not currently in a channel')
        return
    
    await voice_client.stop() 

# misc events
@bot.command(name='image', aliases=['img'], help='Send random image')
async def image(ctx, *args):
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