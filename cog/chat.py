import os

import poe

from discord.ext import commands

aliases = {
    'message': ['m', 'msg'],
    'purge': ['p', 'prg', 'reset'],
    'model': ['mdl']
}

class ChatCog(commands.Cog, name='Chatbot'):
    def __init__(self):
        super()
        self.client = poe.Client(os.getenv('POE_TOKEN'))
        self.history = {}
        self.model = 'chinchilla'

    async def get_history(self, ctx: commands.Context):
        if ctx.author.id in self.cfgs.keys():
            return self.history[ctx.author.id]
        
        self.history = []

        return self.history[ctx.author.id]

    @commands.command('message', aliases=aliases['message'], help='Send message')
    async def message_(self, ctx, *args):
        message = ' '.join(args)

        reply = ''.join([chunk['text_new'] for chunk in self.client.send_message('chinchilla', message, with_chat_break=False)])
        await ctx.send(reply)

    @commands.command('purge', aliases=aliases['purge'], help='Purge conversation')
    async def purge_(self, ctx, *args):
        self.client.purge_conversation('chinchilla')
        await ctx.send('Conversation purged')

    @commands.command('model', aliases=aliases['model'], help='Select model')
    async def model_(self, ctx, *args):
        model = ' '.join(args)

        if model in ['beaver', 'a2_2']:
            await ctx.send('Model not available')
            return

        if model not in self.client.bot_names:
            models = self.client.bot_names
            await ctx.send(self.client.bot_names)
            return
        
        self.model = model
        await ctx.send(f'Model set to {self.client.bot_names[model]}')

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatCog())