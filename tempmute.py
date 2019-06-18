import discord
from pymongo import MongoClient
import datetime
from discord.ext import commands

app = MongoClient('mongo_link')
db = app['Database']
muteds = db['muteds']
guilds = db['guilds']

class Tempmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def check_log(self, guild):
        guild = guilds.find_one({"_id": guild})
        #checando se o modlog está ativado na guilda e se há um canal definido
        if guild['modlog'] and guild['modlog_ch']:
            return True
        else:
            return False

    @commands.command(usage='m!mute <@member> <tempo>(em minutos) <motivo>(opcional)')
    @commands.has_permissions(manage_guild=True)
    #o autor precisará ter permissão de gerenciar servidor na guilda pra executar o comando
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    #o bot precisará ter permissão de gerenciar cargos e canais na guilda pra executar o comando
    async def tempmute(self, ctx, member:discord.Member=None, time:int=None, *, reason:str='Nenhum'):
        guild_db = guilds.find_one({"_id": ctx.guild.id})
        if not guild_db:
            return await ctx.send('Essa guilda não está registrada na minha database, por favor digite `!register` antes de usar esse comando')
        #resolvendo possíveis erros
        if not member or not time:
            return await ctx.send(f'O uso certo desse comando é `{ctx.command.usage}`')
        elif ctx.author == member:
            return await ctx.send('Você não pode mutar a si mesmo.')
        elif member.guild_permissions.administrator:
            return await ctx.send('Você não pode mutar um Adm/Mod.')
        elif ctx.author.top_role <= member.top_role:
            return await ctx.send('Você não pode mutar alguém com um cargo igual ou maior que o seu.')
        role = discord.utils.get(ctx.guild.roles, name='Mutado')
        if not role:
            #caso não exista o cargo, o próprio bot irá criá-lo
            #já mudando suas permissões em todos os canais do servidor
            role = await ctx.guild.create_role(name='Mutado', color=discord.Color(0x2f3136))
            for ch in ctx.guild.channels:
                over = discord.PermissionOverwrite()
                over.send_messages = False
                await ch.set_permissions(overwrite=over, target=role)
        m = muteds.find_one({'_id': member.id})
        if m is None:
            #caso o membro não esteja na database, o bot irá mutá-lo
            guild = ctx.guild 
            embed = discord.Embed(timestamp=ctx.message.created_at)
            moderador = ctx.author
            muteds.insert_one({'_id': member.id, 'guild': ctx.guild.id, 'role': role.id,
                               'timedelta': datetime.datetime.now() + datetime.timedelta(minutes=time)})
            await member.add_roles(role, reason=reason)
            await ctx.send(f'`{member}` foi mutado com sucesso')
            embed.set_author(name=f'{guild.name} - [Mute] | {member}', 
                             icon_url=guild.icon_url)
            embed.set_footer(text=f'ID: {member.id}', icon_url=member.avatar_url)
            embed.add_field(name='Membro', value=member.mention)
            embed.add_field(name='Moderador', value=moderador.mention)
            embed.add_field(name='Tempo', value=f'{time} minutos')
            embed.add_field(name='Motivo', value=reason)
            channel = guild.get_channel(guild_db['modlog_ch'])
            if self.check_log(guild.id) is True:
                await channel.send(embed=embed)
        else:
            #caso o membro esteja na database, o bot enviará uma mensagem de erro
            await ctx.send('Esse membro já está mutado')

def setup(bot):
    bot.add_cog(Tempmute(bot))
    print('Comando Tempmute carregado com sucesso')
