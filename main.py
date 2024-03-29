import discord
from discord.ext import commands
import asyncio
from pymongo import MongoClient
import datetime

app = MongoClient("mongo_link")
db = app['Database']
muteds = db['muteds']
guilds = db['guilds']
#gostaria de esclarecer que o formato que uso para as guildas na database é
#{'_id': IDdaGuilda, 'modlog': True/False, 'modlog_ch': IDdoCanal/None}
#o formato para os membros mutados pode ser observado no tempmute.py

bot = commands.Bot(command_prefix='!')

extensions = ['tempmute', 'modlog']

@bot.event
async def on_ready():
    print('Bot online!')
    bot.loop.create_task(checar_mutes())
    for extension in extensions:
      try:
          bot.load_extension(extension)
      except Exception as e:
          print(repr(e))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.BotMissingPermissions):
        perms = '\n'.join([f'`{x}`' for x in error.missing_perms])
        return await ctx.send(f'Eu não tenho as permissões necessárias para executar este comando: \n {perms}')
    elif isinstance(error, commands.MissingPermissions):
        perms = '\n'.join([f'`{x}`' for x in error.missing_perms])
        return await ctx.send(f'Você não tem as permissões necessárias para executar este comando: \n {perms}')
    else:
        raise error

@bot.event
async def on_member_join(member):
    mtd = muteds.find_one({'_id': member.id})
    if not mtd:
        return
    if mtd['guild'] == member.guild.id:
        #caso o membro tenha saído e entrado na guilda novamente
        #pra burlar o mute, ele ganhará o cargo de novo :v
        role = member.guild.get_role(mtd['role'])
        await member.add_roles(role)

def check_log(guild):
    guild = guilds.find_one({"_id": guild})
    #checando se o modlog está ativado na guilda e se há um canal definido
    if guild['modlog'] and guild['modlog_ch']:
        return True
    else:
        return False
    
async def checar_mutes():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for m in muteds.find():
            #checando se a data atual é maior ou igual a data em que o membro deveria ser desmutado
            #para que ele não fique mutado para sempre caso o bot reinicie antes do tempo acabar
            if (datetime.datetime.now()) >= (m['timedelta']):
                guild = bot.get_guild(m['guild'])
                role = guild.get_role(m['role'])
                member = guild.get_member(m['_id'])
                if member:
                    await member.remove_roles(role)
                muteds.delete_one({'_id': m['_id']})
                if check_log(guild.id) is True:
                    user = await bot.fetch_user(m['_id'])
                    embed = discord.Embed(timestamp=datetime.datetime.utcnow())
                    embed.set_author(name=f'{guild.name} - [Unmute] | {user}',
                                    icon_url=guild.icon_url)
                    embed.set_footer(text=f'ID: {user.id}', icon_url=user.avatar_url)
                    embed.add_field(name='Membro', value=user.mention)
                    embed.add_field(name='Moderador', value=bot.user.mention)
                    guild_db = guilds.find_one({"_id": guild.id})
                    channel = guild.get_channel(guild_db['modlog_ch'])
                    await channel.send(embed=embed)
        await asyncio.sleep(1)

bot.run('seu_token')
