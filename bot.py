# local library
from config import config

# library
import os
from dotenv import load_dotenv
import asyncio
import discord
from discord.ext import commands

load_dotenv()

bot = commands.Bot(
    command_prefix=config.command_prefix, 
    intents=discord.Intents.all())

# events
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(
        status=discord.Status.online, 
        activity=discord.Game(name=f'Music, type {config.command_prefix}help'))

# main function
async def main():
    await bot.load_extension('cogs.music')

    async with bot:
        await bot.start(os.getenv('TOKEN'))

asyncio.run(main())