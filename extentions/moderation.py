import asyncio
import time
import re
import random

from dateutil.relativedelta import *
from random import choice
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from dis_snek.models.discord_objects.embed import Embed, EmbedField
from dis_snek.models.discord_objects.channel import ChannelHistory
from dis_snek.models.discord import DiscordObject
from dis_snek.models.scale import Scale
from dis_snek.models.enums import Permissions
from dis_snek.models.listener import listen
from dis_snek import Snake, slash_command, InteractionContext, slash_option, OptionTypes, slash_permission
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *
from dis_snek.models.discord_objects.components import ActionRow, Button, spread_to_rows
from dis_snek.models.enums import ButtonStyles

def random_string_generator():
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    result=''
    for i in range(0, 8):
        result += random.choice(characters)
    return result

async def user_has_perms(author, perm):
    adminrole = [role for role in author.roles if perm in role.permissions]
    if adminrole != []:
        return True
    return False

async def seperate_string_number(string):
    previous_character = string[0]
    groups = []
    newword = string[0]
    for x, i in enumerate(string[1:]):
        if i.isalpha() and previous_character.isalpha():
            newword += i
        elif i.isnumeric() and previous_character.isnumeric():
            newword += i
        else:
            groups.append(newword)
            newword = i

        previous_character = i

        if x == len(string) - 2:
            groups.append(newword)
            newword = ''
    return groups

w = ['w', 'week', 'weeks']
d = ['d', 'day', 'days']
h = ['h', 'hour', 'hours']
m = ['m', 'min', 'minute', 'minutes']
s = ['s', 'sec', 'second', 'seconds']

class Moderation(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @slash_command(name='ban', description="[MOD]allows me to ban users from the server", scopes=[435038183231848449, 149167686159564800])
    @user()
    @bantime()
    @deletedays()
    @reason()
    async def ban(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given', bantime:str=None, deletedays:int=0):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.BAN_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user is ctx.author:
                await ctx.send("You can't ban yourself", ephemeral=True)
                return

            if await user_has_perms(user, Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't ban an admin", ephemeral=True)
                return
            elif await user_has_perms(user, Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't ban users with ban perms", ephemeral=True)
                return
            
            try:
                await ctx.guild.get_ban(user)
            except NotFound:
                db = await odm.connect()
                member = await ctx.guild.get_member(user.id)
                if user == member:
                    if ctx.author.top_role == member.top_role:
                        embed = Embed(description=f":x: You can't ban people with the same role as you!",
                                    color=0xDD2222)
                        await ctx.send(embed=embed)
                        return

                    if ctx.author.top_role.position < member.top_role.position:
                        embed = Embed(description=f":x: You can't ban people with roles higher than yours!",
                                    color=0xDD2222)
                        await ctx.send(embed=embed)
                        return

                while True:
                    banid = random_string_generator()
                    banid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':banid})
                    if banid_db == None:
                        break
                    else:
                        continue
                daytime = datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
                if bantime == None:
                    await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Ban", day=daytime, reason=reason))
                    embed = Embed(description=f"{user} **was banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                                  colour=0x0c73d3,
                                  timestamp=datetime.utcnow())
                    embed.set_thumbnail(url=user.avatar.url)
                    await ctx.send(embed=embed)
                else:
                    tempbanned = await db.find_one({"user":user.id, "guildid":ctx.guild_id})
                    if tempbanned != None:
                        await db.delete(tempbanned)
                    
                    ban_time = [int(i) for i in bantime.lower().split() if i.isdigit()]
                    if ban_time == []:
                        embed = Embed(description=f":x: Ban time formatting not correct. Try again. \n\n[Examples: `10 S`, `10 M`, `10 H`, `10 D`]",
                                        color=0xDD2222)
                        await ctx.send(embed=embed)
                    else:
                        for num in ban_time:
                            time = num
                        ban_time_type = [str(type) for type in bantime.lower().split() if not type.isdigit()]
                        for time_type in ban_time_type:
                            type = time_type

                    if type in d:
                        seconds = time * 86400
                        endtime = datetime.utcnow() + timedelta(days=int(time))

                    elif type in h:
                        seconds = time * 3600
                        endtime = datetime.utcnow() + timedelta(hours=int(time))

                    elif type in m:
                        seconds = time * 60
                        endtime = datetime.utcnow() + timedelta(minutes=int(time))

                    elif type in s:
                        seconds = time
                        endtime = datetime.utcnow() + timedelta(seconds=int(time))

                    else:
                        embed = Embed(description=f":x: Time type not supported. You can use: {d}, {h}, {m}, {s}",
                                    color=0xDD2222)
                        await ctx.send(embed=embed)
                        return
                    
                    if seconds < 10:
                        await ctx.send("Ban time can't be shorter than 10 seconds")
                    
                    await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Temp Ban", day=daytime, reason=reason))
                    await db.save(tempbans(guildid=ctx.guild_id, user=user.id, starttime=datetime.utcnow(), endtime=endtime, banreason=reason))
                    
                    diff = relativedelta(endtime,  datetime.utcnow())
                    duration = f"{diff.years} Y {diff.months} M {diff.days} D {diff.hours} H {diff.minutes} min"
                    embed = Embed(description=f"{user} **was banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}\n**Duration:**{duration}",
                                    colour=0x0c73d3,
                                    timestamp=datetime.utcnow())
                    embed.set_thumbnail(url=user.avatar.url)
                    await ctx.send(embed=embed)
                await ctx.guild.ban(DiscordObject(id=int(user.id)), reason=reason, delete_message_days=deletedays)

def setup(bot):
    Moderation(bot)