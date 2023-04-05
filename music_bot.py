import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import config

load_dotenv()

bot = commands.Bot(
    command_prefix=config.music_cmd_prefix, 
    intents=discord.Intents.all())

# events
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(
        status=discord.Status.online, 
        activity=discord.Game(name=f'Music, type {config.music_cmd_prefix}help'))

# main function
async def main():
    await bot.load_extension('cog.music')

    async with bot:
        await bot.start(os.getenv('MUSIC_TOKEN'))

asyncio.run(main())