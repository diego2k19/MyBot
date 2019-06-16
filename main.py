import discord
from discord.ext import commands
import asyncio
from pymongo import MongoClient
import datetime

app = MongoClient("mongo_link")
db = app['Database']
muteds = db['muteds']
guilds = db['guilds']

bot = commands.Bot(command_prefix='!')

extensions = ['tempmute']

@bot.event
async def on_ready():
    print('Bot online!')
    bot.loop.create_task(checar_mutes())
    for extension in extensions:
      try:
          bot.load_extension(extension)
      except Exception as e:
          print(repr(e))

def check_log(guild):
    guild = guilds.find_one({"_id": guild})
    #checando se o modlog está ativado na guilda e se há um canal definido
    if guild['modlog'] == 1 and guild['modlog_ch'] != 'Nenhum':
        return True
    else:
        return False
    
async def checar_mutes():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for m in muteds.find():
            guild = bot.get_guild(m['guild'])
            role = guild.get_role(m['role'])
            member = guild.get_member(m['_id'])
            guild_db = guilds.find_one({"_id": guild.id})
            embed = discord.Embed(timestamp=datetime.datetime.now())
            embed.set_author(name=f'{guild.name} - [Unmute] | {member}',
                            icon_url=guild.icon_url)
            embed.set_footer(text=f'ID: {member.id}', icon_url=member.avatar_url)
            embed.add_field(name='Membro', value=member.mention)
            embed.add_field(name='Moderador', value=bot.user.mention)
            channel = guild.get_channel(guild_db['modlog_ch'])
            #checando se a data atual é maior ou igual a data em que o membro deveria ser desmutado
            #para que ele não fique mutado para sempre caso o bot reinicie antes do tempo acabar
            if (datetime.datetime.now()) >= (m['timedelta']):
                await member.remove_roles(role)
                muteds.delete_one({'_id': m['_id']})
                if check_log(guild.id) is True:
                    await channel.send(embed=embed)
            #caso a condição acima não for atendida, o bot checará se o tempo em segundos até o mute
            #acabar é maior do que 0, se sim, ele irá calcular quantos segundos aindam faltam
            #e atualizar na database
            elif m['time'] > 0:
                newtime = ((m['timedelta']) - (datetime.datetime.now())).seconds
                muteds.update_one({'_id': m['_id']}, {'$set': 
                {'time': newtime}})
            #caso o tempo em segundos não for maior que zero, ele já irá desmutar o membro
            else:
                await member.remove_roles(role)
                muteds.delete_one({'_id': m['_id']})
                if check_log(guild.id) is True:
                    await channel.send(embed=embed)
        await asyncio.sleep(1)

bot.run('seu_token')
