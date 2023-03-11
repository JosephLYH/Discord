import discord
from discord.ext import commands
from googleapiclient.discovery import build

import youtube_dl

from config import config, conf

bot = commands.Bot(
    command_prefix=config.COMMAND_PREFIX, 
    intents=discord.Intents.all())

youtube = build('youtube', 'v3', developerKey=conf.YOUTUBE_API_KEY)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(
        status=discord.Status.online, 
        activity=discord.Game(name=f'Music, type {config.COMMAND_PREFIX}help'))

@bot.command(name='join', help='Make the bot join your current voice channel')
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.channel.send(f'{bot.user} is ready to serve music!')

@bot.command(name='leave', help='Make the bot leave its current voice channel')
async def leave(ctx):
    await ctx.guild.voice_client.disconnect()
    await ctx.channel.send(f'{bot.user} has left the voice channel')

@bot.command(name='play', help='Play a song')
async def play_song(ctx, song_name: str):
    voice_client = ctx.guild.voice_client

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

    player = await voice_client.create_ytdl_player(search_results[0]['url'])

@bot.command(name='play url', help='PLay a song from url')
async def play_url(ctx, url: str):
    return

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(f'{bot.user} does not have the correct role for this command.')

bot.run(conf.TOKEN)