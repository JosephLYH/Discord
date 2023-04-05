import os

import poe

from config import config, chat_config
from discord.ext import commands

aliases = {
    'message': ['m', 'msg'],
    'purge': ['p', 'prg', 'reset'],
    'model': ['mdl'],
    'dnd': ['d', 'play'],
}

class ChatCog(commands.Cog, name='Chatbot'):
    def __init__(self):
        super()
        self.client = poe.Client(os.getenv('POE_TOKEN'))
        self.history = {}
        self.model = 'chinchilla'
        
        self.client.send_chat_break(self.model)
        self.client.send_message(self.model, chat_config.starting_prompt, with_chat_break=False)

    @commands.command('message', aliases=aliases['message'], help='Send message')
    async def message_(self, ctx, *args):
        message = f'{ctx.author.name}: '
        message += ' '.join(args)
        
        for chunk in self.client.send_message(self.model, message, with_chat_break=False):
            pass
        await ctx.send(chunk['text'])

    @commands.command('purge', aliases=aliases['purge'], help='Purge conversation')
    async def purge_(self, ctx, *args):
        self.client.send_chat_break(self.model)

        message = 'Conversation purged' if not config.be_funny else 'You have bonked me so hard, I have forgetten everything.'
        await ctx.send(message)

        self.client.send_message(self.model, chat_config.starting_prompt, with_chat_break=False)

    @commands.command('model', aliases=aliases['model'], help='Select model')
    async def model_(self, ctx, *args):
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
    async def dnd_(self, ctx, *args):
        self.client.send_chat_break(self.model)
        await ctx.invoke(self.message_, chat_config.dnd_prompt)

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatCog())