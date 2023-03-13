from config import config

import random
import os
import discord
from discord.ext import commands

aliases = {
    'image': ['img'],
}

class ImageCog(commands.Cog, name='Image Generator'):
    @commands.command('image', aliases=aliases['image'], description='Generates image')
    async def connect_(self, ctx, *args):
        arg = ' '.join(args)
        img_dir = 'img'

        img_files = os.listdir(os.path.join(img_dir, arg))
        img_file = random.choice(img_files)
        await ctx.send(file=discord.File(os.path.join(img_dir, arg, img_file)))

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageCog(bot))