import base64
import io
import os
import random

import discord
import requests
from discord.ext import commands
from PIL import Image

from config import img_config

aliases = {
    'image': ['img'],
    'sd_model': [],
    'sd': ['stable_diffusion', 'gen'],
}

class ImageCog(commands.Cog, name='Image Generator'):
    @commands.command('image', aliases=aliases['image'], help='Generates image')
    async def image_(self, ctx, *args):
        arg = ' '.join(args)
        img_dir = img_config.img_dir

        img_files = os.listdir(os.path.join(img_dir, arg))
        img_file = random.choice(img_files)
        await ctx.send(file=discord.File(os.path.join(img_dir, arg, img_file)))

    @commands.command('sd_model', aliases=aliases['sd_model'], help='Set stable diffusion model, default = chilloutmix')
    async def model_(self, ctx, model='chilloutmix'):
        payload = img_config.options_payload

        if model not in img_config.model_map.keys():
            embed = discord.Embed(title='', description='Model not installed', color=discord.Color.dark_red())
            return await ctx.send(embed=embed)

        payload['sd_model_checkpoint'] = img_config.model_map[model]

        response = requests.post(url=f'{img_config.sd_url}/sdapi/v1/options', json=payload)

        if response.status_code != 200:
            embed = discord.Embed(title='', description='Failed to load model', color=discord.Color.dark_red())
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(title='', description=f'Successfully loaded model {payload["sd_model_checkpoint"]}', color=discord.Color.green())
        return await ctx.send(embed=embed)

    @commands.command('sd', aliases=aliases['sd'], help='Generates stable diffusion image, enter postive and negative prompt, e.g. \sd "corgi" "bad anatomy, watermark"')
    async def sd_(self, ctx, pos_prompt, neg_prompt=''):
        sd_path = os.path.join(img_config.img_dir, 'sd')
        os.makedirs(sd_path, exist_ok=True)

        payload = img_config.txt2image_payload
        payload['prompt'] = pos_prompt
        payload['negative_prompt'] = neg_prompt

        response = requests.post(url=f'{img_config.sd_url}/sdapi/v1/txt2img', json=payload)
        r = response.json()

        if response.status_code != 200:
            embed = discord.Embed(title='', description='Failed to generate iamge', color=discord.Color.dark_red())
            return await ctx.send(embed=embed)
        
        for i in r['images']:
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

            num_images = len(os.listdir(sd_path))
            image.save(os.path.join(sd_path, f'{num_images}.jpg'))

            await ctx.send(file=discord.File(os.path.join(sd_path, f'{num_images}.jpg')))

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageCog(bot))