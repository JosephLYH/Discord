import base64
import io
import os
import random
import copy
import asyncio

import discord
import requests
from discord.ext import commands
from PIL import Image

from config import config, img_config

aliases = {
    'image': ['i', 'img'],
    'sd_model': ['m', 'model'],
    'sd': ['stable_diffusion', 'diffuse'],
    'sd_options': ['so'],
    'sd_print_options': ['spo'],
    'sd_loras': ['loras'],
}

class ImageCog(commands.Cog, name='Image Generator' if not config.be_funny else '不可以色色'):
    def __init__(self):
        super()
        self.cfgs = {}
        self.lock = asyncio.Lock()

    async def get_payload(self, ctx: commands.Context):
        if ctx.author.id in self.cfgs.keys():
            return self.cfgs[ctx.author.id]
        
        self.cfgs[ctx.author.id] = copy.deepcopy(img_config.txt2img_payload)

        return self.cfgs[ctx.author.id]

    @commands.command('image', aliases=aliases['image'], help='Chooses random image from directory')
    async def image_(self, ctx, *args):
        arg = ' '.join(args)
        img_dir = img_config.img_dir

        img_files = os.listdir(os.path.join(img_dir, arg))
        img_file = random.choice(img_files)
        await ctx.send(file=discord.File(os.path.join(img_dir, arg, img_file)))

    @commands.command('sd_model', aliases=aliases['sd_model'], help='Set stable diffusion model')
    async def sd_model_(self, ctx, model=None):
        payload = await self.get_payload(ctx)

        if model not in img_config.model_map.keys():
            embed = discord.Embed(title='Model not installed', description=f'SFW models {img_config.sfw_models}\nNSFW models {img_config.nsfw_models}', color=discord.Color.dark_red())
            return await ctx.send(embed=embed)

        payload['sd_model_checkpoint'] = img_config.model_map[model]
        
        embed = discord.Embed(title='', description=f'Successfully loaded {payload["sd_model_checkpoint"]}', color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command('sd', aliases=aliases['sd'], help='Generates stable diffusion image, enter pos & neg prompt, e.g. \sd "corgi" "bad anatomy, watermark"')
    async def sd_(self, ctx, pos_prompt, neg_prompt=''):
        sd_path = os.path.join(img_config.img_dir, 'sd')
        os.makedirs(sd_path, exist_ok=True)

        payload = await self.get_payload(ctx)
        payload['prompt'] = pos_prompt
        payload['negative_prompt'] = neg_prompt
        options = {'sd_model_checkpoint': payload['sd_model_checkpoint']}

        async with self.lock:
            response = requests.post(url=f'{img_config.sd_url}/sdapi/v1/options', json=options)
            if response.status_code != 200:
                embed = discord.Embed(title='', description='Failed to load model', color=discord.Color.dark_red())
                return await ctx.send(embed=embed)

            response = requests.post(url=f'{img_config.sd_url}/sdapi/v1/txt2img', json=payload)
        
        del payload['prompt']
        del payload['negative_prompt']
        if response.status_code != 200:
            embed = discord.Embed(title='', description='Failed to generate image', color=discord.Color.dark_red())
            return await ctx.send(embed=embed)
        
        num = sorted(map(lambda x: int(os.path.splitext(x)[0]), os.listdir(sd_path)))[-1]
        for i in response.json()['images']:
            num += 1

            image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))
            image.save(os.path.join(sd_path, f'{num}.jpg'))

            embed = discord.Embed(title='', description=f'{payload["sd_model_checkpoint"]} generated', color=discord.Color.green())
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File(os.path.join(sd_path, f'{num}.jpg')))

    @commands.command('sd_options', aliases=aliases['sd_options'], help='Set options')
    async def sd_options_(self, ctx, key=None, value=None):
        if key not in img_config.valid_options.keys():
            embed = discord.Embed(title='', description=f'Please enter valid options {list(img_config.valid_options.keys())}', color=discord.Color.dark_red())
            return await ctx.send(embed=embed)
        
        if key == 'cfg_scale':
            try:
                value = float(value)
            except:
                pass
        elif key in ['steps', 'height', 'width']:
            try:
                value = int(value)
            except:
                pass           

        if value not in img_config.valid_options[key]:
            embed = discord.Embed(title='', description=f'Please enter valid value {img_config.valid_options[key]}', color=discord.Color.dark_red())
            return await ctx.send(embed=embed)

        payload = await self.get_payload(ctx)
        payload[key] = value

        embed = discord.Embed(title='', description=f'{key} is set to {value}', color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command('sd_print_options', aliases=aliases['sd_print_options'], help='Print options')
    async def sd_print_options_(self, ctx):
        payload = await self.get_payload(ctx)
        await ctx.send(payload)

    @commands.command('sd_loras', aliases=aliases['sd_loras'], help='List loras available')
    async def sd_loras_(self, ctx):
        await ctx.send(img_config.loras)

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageCog())