import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import config

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
    for cog in os.listdir('cog'):
        if cog.endswith('.py'):
            await bot.load_extension(f'cog.{os.path.splitext(cog)[0]}')

    async with bot:
        await bot.start(os.getenv('TOKEN'))

asyncio.run(main())