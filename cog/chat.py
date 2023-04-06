import copy
import os
import random

import poe

from config import chat_config, config
from discord.ext import commands

CHUNK_MAX_SIZE = 2000

aliases = {
    'message': ['m', 'msg'],
    'purge': ['p', 'prg', 'reset'],
    'model': ['mdl'],
    'dnd': ['d', 'play'],
    'world': ['w', 'wrld'],
    'character': ['c', 'char'],
    'view': ['v', 'show'],
    'new': ['n', 'create'],
    'roll': ['r', 'dice'],
}

def nested_get(dictionary, keys):    
    for key in keys:
        dictionary = dictionary.get(key, None)
        if dictionary is None:
            break

    return dictionary

def nested_set(dictionary, keys, value):
    for key in keys[:-1]:
        dictionary = dictionary.setdefault(key, {})
    dictionary[keys[-1]] = value

class ChatCog(commands.Cog, name='Chatbot'):
    def __init__(self):
        super()
        self.client = poe.Client(os.getenv('POE_TOKEN'))
        self.model = 'chinchilla' # ChatGPT
        
        # DnD settings
        self.in_dnd = False
        self.world = 'Forgotten Realms'
        self.characters = {}
        
        self.client.send_chat_break(self.model)

    async def send_chat_break(self):
        try:
            self.client.send_chat_break(self.model)
        except:
            self.client = poe.Client(os.getenv('POE_TOKEN'))
            self.client.send_chat_break(self.model)

    async def send_message(self, message):
        if self.in_dnd:
            message = chat_config.dnd_prompt + chat_config.dnd_worlds[self.world] + message

        try:
            for chunk in self.client.send_message(self.model, message, with_chat_break=False):
                pass
        except:
            self.client = poe.Client(os.getenv('POE_TOKEN'))
            for chunk in self.client.send_message(self.model, message, with_chat_break=False):
                pass

        return chunk['text']
    
    async def create_default_character(self, ctx: commands.Context):
        if not self.characters.get(ctx.author.id):
            self.characters[ctx.author.id] = copy.deepcopy(chat_config.character_template)
            self.characters[ctx.author.id]['name'] = ctx.author.display_name
            await ctx.send('Character created')

    def roll_dice(self, dice):
        if dice.startswith('d'):
            dice = dice[1:]
        
        try:
            dice = int(dice)
        except:
            return None

        return random.randint(1, dice)   

    @commands.command('message', aliases=aliases['message'], help='Send message')
    async def message_(self, ctx: commands.Context, *args):
        message = ''
        if self.in_dnd:
            await ctx.invoke(self.create_default_character)
            message = f"{str(self.characters[ctx.author.id])} \n{self.characters[ctx.author.id]['name']}: "
        
        message += ' '.join(args)
        reply = await self.send_message(message)
        for chunk in [reply[i:i+CHUNK_MAX_SIZE] for i in range(0, len(reply), CHUNK_MAX_SIZE)]:
            await ctx.send(chunk)

    @commands.command('purge', aliases=aliases['purge'], help='Purge conversation')
    async def purge_(self, ctx: commands.Context, *args):
        self.in_dnd = False
        self.client.send_chat_break(self.model)

        message = 'Conversation purged' if not config.be_funny else 'You have bonked me so hard, I have forgetten everything.'
        await ctx.send(message)

    @commands.command('model', aliases=aliases['model'], help='Select model')
    async def model_(self, ctx: commands.Context, *args):
        model = ' '.join(args)

        if model in ['beaver', 'a2_2']:
            await ctx.send('Model not available')
            return

        if model not in self.client.bot_names:
            await ctx.send(self.client.bot_names)
            return
        
        self.model = model
        await ctx.send(f'Model set to {self.client.bot_names[model]}')

    @commands.command('dnd', aliases=aliases['dnd'], help='Start DnD session')
    async def dnd_(self, ctx: commands.Context, *args):
        self.in_dnd = True
        await self.send_chat_break()
        reply = await self.send_message(chat_config.dnd_starting_prompt)
        await ctx.send(reply)

    @commands.command('world', aliases=aliases['world'], help='Select world')
    async def world_(self, ctx: commands.Context, *args):
        world = ' '.join(args)

        if world not in chat_config.dnd_worlds:
            await ctx.send(f'Choose from {list(chat_config.dnd_worlds.keys())}')
            return

        self.world = world
        await ctx.send(f'World set to {world}')

    @commands.command('character', aliases=aliases['character'], help='Create character or modify character')
    async def character_(self, ctx: commands.Context, key=None, *values):
        value = ' '.join(values) if values else None

        await ctx.invoke(self.create_default_character)

        keys = key.split('.') if key else None
        if keys is None:
            await ctx.send('Please select a setting to change')
            await ctx.send(self.characters[ctx.author.id])
            return

        if type(nested_get(self.characters[ctx.author.id], keys)) == type([]):
            value = value.split(',')
            value = [v.strip() for v in value]

        if type(nested_get(self.characters[ctx.author.id], keys)) != type(value) and (len(keys) != 2 and keys[0] != 'skills'):
            await ctx.send('Please enter valid new value')
            await ctx.send(nested_get(self.characters[ctx.author.id], keys))
            return

        nested_set(self.characters[ctx.author.id], keys, value)
        await ctx.send(f'{key} set to {value}')

    @commands.command('view', aliases=aliases['view'], help='View character')
    async def view_(self, ctx: commands.Context, *args):
        await ctx.invoke(self.create_default_character)
        await ctx.send(self.characters[ctx.author.id])

    @commands.command('new', aliases=aliases['new'], help='Generate new character')
    async def view_(self, ctx: commands.Context, *args):
        if self.characters.get(ctx.author.id):
            del self.characters[ctx.author.id]
        await ctx.invoke(self.create_default_character)
        await ctx.send(self.characters[ctx.author.id])

    @commands.command('roll', aliases=aliases['roll'], help='Roll dice')
    async def roll_(self, ctx: commands.Context, *args):
        dices = ' '.join(args).split(',').strip()
        rolls = list(map(self.roll_dice, dices))

        if None in rolls:
            await ctx.send('Please enter valid dice')
            return

        await ctx.invoke(self.message_, 'I rolled ' + ', '.join(rolls))

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatCog())