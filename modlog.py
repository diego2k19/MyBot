import discord
from pymongo import MongoClient
from discord.ext import commands

app = MongoClient('mongo_url')
db = app['database']
guilds = db['guilds']
#gostaria de esclarecer que o formato que uso para as guildas na database é
#{'_id': IDdaGuilda, 'modlog': True/False, 'modlog_ch': IDdoCanal/None}

class Modlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    #o autor precisará ter permissão de gerenciar servidor na guilda pra executar o comando
    async def register(self, ctx):
        guild_db = guilds.find_one({"_id": ctx.guild.id})
        if not guild_db:
            guilds.insert_one({'_id': ctx.guild.id, 'modlog': False, 'modlog_ch': None}).inserted_id
            await ctx.send('Esta guilda foi registrada com sucesso.')
        else:
            await ctx.send('Esta guilda já está registrada')

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    #o autor precisará ter permissão de gerenciar servidor na guilda pra executar o comando
    async def modlog(self, ctx):
        #caso não for dado nenhum subcomando do grupo, o bot irá retornar algo
        if ctx.invoked_subcommand is None:
            guild_db = guilds.find_one({"_id": ctx.guild.id})
            if not guild_db:
                return await ctx.send('Essa guilda não está registrada na minha database, por favor digite `!register` antes de usar esse comando')
            if not guild_db['modlog']:
                msg = f'Atualmente, as mensagens de moderação no servidor estão `desativadas`. \n Digite `!modlog enable <channel>` para ativá-las'
            if guild_db['modlog']:
                channel = ctx.guild.get_channel(guild_db['modlog_ch']).mention
                msg = f'Atualmente, as mensagens de moderação no servidor estão `ativadas` e sendo mandadas no canal {channel}. \n Caso queira desativá-las, digite `!modlog disable`'
            await ctx.send(msg)

    @modlog.command()
    #este é um comando do grupo modlog
    async def enable(self, ctx, channel: discord.TextChannel=None):
        guild_db = guilds.find_one({"_id": ctx.guild.id})
        if not guild_db:
            return await ctx.send('Essa guilda não está registrada na minha database, por favor digite `!register` antes de usar esse comando')
        if not channel:
            await ctx.send('Por favor, especifique um canal')
        if guild_db['modlog'] and guild_db['modlog_ch'] == channel.id:
            await ctx.send('As mensagens de moderação já estão sendo enviadas neste canal.')
        elif channel.permissions_for(ctx.me).send_messages is False:
            await ctx.send('Eu não tenho permissão para enviar mensagens neste canal')
        else:
            guilds.update_one({'_id': ctx.guild.id}, {'$set': {'modlog': True, 'modlog_ch': channel.id}})
            await ctx.send(f'Agora as mensagens de moderação serão enviadas em {channel.mention}')

    @modlog.command()
    #este é um comando do grupo modlog
    async def disable(self, ctx):
        guild_db = guilds.find_one({"_id": ctx.guild.id})
        if not guild_db:
            return await ctx.send('Essa guilda não está registrada na minha database, por favor digite `!register` antes de usar esse comando')
        if not guild_db['modlog']:
            await ctx.send('As mensagens de moderação já estão desativadas.')
        else:
            guilds.update_one({'_id': ctx.guild.id}, {'$set': {'modlog': False, 'modlog_ch': None}})
            await ctx.send('Agora as mensagens de moderação estão desativadas')

def setup(bot):
    bot.add_cog(Modlog(bot))
    print('[Modlog.py] carregado com sucesso!')
