import asyncio
import math
from pyexpat.errors import messages
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
    
    @slash_command(name='delete', description="[MOD]allows me to delete messages", scopes=[435038183231848449, 149167686159564800])
    @amount()
    @reason()
    async def delete_messages(self, ctx:InteractionContext, amount:int=0, reason:str='No reason given'):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.MANAGE_MESSAGES)
        if (perms == True):
            if (amount <= 0) or (amount >= 1000):
                embed = Embed(description=f":x: Amount can't be less than 1 or more than 1000",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return
            deleted = await channel.purge(deletion_limit=amount, search_limit=1000, reason=reason)
            embed = Embed(description=f"Deleted {deleted} messages",
                                timestamp=datetime.utcnow(),
                                color=0x0c73d3)
            embed.set_footer(text=f"Auctioned by: {ctx.author}|{ctx.author.id}")
            await ctx.send(embed=embed)
    
    @slash_command(name='userpurge', description="[MOD]allows me to purge users messages", scopes=[435038183231848449, 149167686159564800])
    @user()
    @amount()
    @reason()
    async def userpurge(self, ctx:InteractionContext, user:OptionTypes.USER=None, amount:int=0, reason:str='No reason given'):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.MANAGE_MESSAGES)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user is ctx.author:
                await ctx.send("You can't purge yourself", ephemeral=True)
                return
            if await user_has_perms(user, Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't purge an admin", ephemeral=True)
                return
            elif await user_has_perms(user, Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't purge users with ban perms", ephemeral=True)
                return
            elif await user_has_perms(user, Permissions.MANAGE_MESSAGES) == True:
                await ctx.send("You can't purge users with manage messages perms", ephemeral=True)
                return
            if (amount <= 0) or (amount >= 300):
                embed = Embed(description=f":x: Amount can't be less than 1 or more than 300",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return

            del_msgs = 0
            from_channels = ''
            for channel in ctx.guild.channels:
                deleted = await channel.purge(deletion_limit=amount, search_limit=3000, predicate=lambda m: m.author == user, reason=reason)
                del_msgs = del_msgs+deleted
                from_channels = from_channels+f"{channel.mention} "
            embed = Embed(description=f"Deleted {del_msgs} messages from {from_channels}",
                                timestamp=datetime.utcnow(),
                                color=0x0c73d3)
            embed.set_footer(text=f"Auctioned by: {ctx.author}|{ctx.author.id}")
            await ctx.send(embed=embed)
    
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
                daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
                if bantime == None:
                    await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Ban", day=daytime, reason=reason))
                    embed = Embed(description=f"{user} **was banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                                  color=0x0c73d3,
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
                        endtime = datetime.now() + timedelta(days=int(time))

                    elif type in h:
                        seconds = time * 3600
                        endtime = datetime.now() + timedelta(hours=int(time))

                    elif type in m:
                        seconds = time * 60
                        endtime = datetime.now() + timedelta(minutes=int(time))

                    elif type in s:
                        seconds = time
                        endtime = datetime.now() + timedelta(seconds=int(time))

                    else:
                        embed = Embed(description=f":x: Time type not supported. You can use: {d}, {h}, {m}, {s}",
                                    color=0xDD2222)
                        await ctx.send(embed=embed)
                        return
                    
                    if seconds < 10:
                        await ctx.send("Ban time can't be shorter than 10 seconds")
                    
                    await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Temp Ban", day=daytime, reason=reason))
                    await db.save(tempbans(guildid=ctx.guild_id, user=user.id, starttime=datetime.now(), endtime=endtime, banreason=reason))
                    
                    embed = Embed(description=f"{user} **was banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}\n**End time:**<t:{math.ceil(endtime.timestamp())}:R>",
                                    color=0x0c73d3,
                                    timestamp=datetime.utcnow())
                    embed.set_thumbnail(url=user.avatar.url)
                    await ctx.send(embed=embed)
                await ctx.guild.ban(DiscordObject(id=int(user.id)), reason=reason, delete_message_days=deletedays)
    
    @slash_command(name='unban', description="[MOD]allows me to unban users from the server", scopes=[435038183231848449, 149167686159564800])
    @user()
    @reason()
    async def unban(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given', bantime:str=None, deletedays:int=0):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.BAN_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user == ctx.author:
                embed = Embed(description=f":x: This is not how that works buddy...",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return
            try:
                await ctx.guild.get_ban(user)
            except NotFound:
                embed = Embed(description=f":x: {user} not banned",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return
            else:
                await ctx.guild.unban(user, reason)
                embed = Embed(description=f"{user} **was unbanned by {ctx.author.mention}** | {reason} \n**User ID:** {user.id}",
                                    colour=0x0c73d3,
                                    timestamp=datetime.utcnow())
                embed.set_thumbnail(url=user.avatar.url)
                await ctx.send(embed=embed)
                db = await odm.connect()
                while True:
                    banid = random_string_generator()
                    banid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':banid})
                    if banid_db == None:
                        break
                    else:
                        continue
                daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
                await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Unban", day=daytime, reason=reason))

    @slash_command(name='kick', description="[MOD]allows me to kick users from the server", scopes=[435038183231848449, 149167686159564800])
    @user()
    @reason()
    async def kick(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given'):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.KICK_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user is ctx.author:
                await ctx.send("You can't kick yourself", ephemeral=True)
                return

            if await user_has_perms(user, Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't kick an admin", ephemeral=True)
                return
            elif await user_has_perms(user, Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't kick users with ban perms", ephemeral=True)
                return
            elif await user_has_perms(user, Permissions.KICK_MEMBERS) == True:
                await ctx.send("You can't kick users with kick perms", ephemeral=True)
                return
            db = await odm.connect()
            if ctx.author.top_role == user.top_role:
                embed = Embed(description=f":x: You can't kick people with the same role as you!",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return

            if ctx.author.top_role.position < user.top_role.position:
                embed = Embed(description=f":x: You can't kick people with roles higher than yours!",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return
            while True:
                kickid = random_string_generator()
                kickid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':kickid})
                if kickid_db == None:
                    break
                else:
                    continue
            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.save(strikes(strikeid=kickid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Kick", day=daytime, reason=reason))
            await ctx.guild.kick(user, reason)
            embed = Embed(description=f"{user} **was kicked** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                          color=0x0c73d3,
                          timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
    
    @slash_command(name='mute', description="[MOD]allows me to mute users", scopes=[435038183231848449, 149167686159564800])
    @user()
    @mutetime()
    @reason()
    async def mute(self, ctx:InteractionContext, user:OptionTypes.USER=None, mutetime:str=None, reason:str='No reason given'):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.MUTE_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user is ctx.author:
                await ctx.send("You can't mute yourself", ephemeral=True)
                return

            if await user_has_perms(user, Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't mute an admin", ephemeral=True)
                return
            elif await user_has_perms(user, Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't mute users with ban perms", ephemeral=True)
                return
            elif await user_has_perms(user, Permissions.KICK_MEMBERS) == True:
                await ctx.send("You can't mute users with kick perms", ephemeral=True)
                return
            
            if ctx.author.top_role == user.top_role:
                embed = Embed(description=f":x: You can't mute people with the same role as you!",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return

            if ctx.author.top_role.position < user.top_role.position:
                embed = Embed(description=f":x: You can't mute people with roles higher than yours!",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return
            
            mute_time = [int(i) for i in mutetime.lower().split() if i.isdigit()]
            if mute_time == []:
                embed = Embed(description=f":x: Mute time formatting not correct. Try again. \n\n[Examples: `10 S`, `10 M`, `10 H`, `10 D`]",
                                color=0xDD2222)
                await ctx.send(embed=embed)
            else:
                for num in mute_time:
                    time = num
                mute_time_type = [str(type) for type in mutetime.lower().split() if not type.isdigit()]
                for time_type in mute_time_type:
                    type = time_type

            if type in d:
                seconds = time * 86400
                endtime = datetime.now() + timedelta(days=int(time))

            elif type in h:
                seconds = time * 3600
                endtime = datetime.now() + timedelta(hours=int(time))

            elif type in m:
                seconds = time * 60
                endtime = datetime.now() + timedelta(minutes=int(time))

            elif type in s:
                seconds = time
                endtime = datetime.now() + timedelta(seconds=int(time))

            else:
                embed = Embed(description=f":x: Time type not supported. You can use: {d}, {h}, {m}, {s}",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return
            
            if (seconds < 10) or (seconds > 2419200):
                await ctx.send("Mute time can't be shorter than 10 seconds and longer than 28 days.", ephemeral=True)
            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            db = await odm.connect()
            while True:
                muteid = random_string_generator()
                muteid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':muteid})
                if muteid_db == None:
                    break
                else:
                    continue
            await db.save(strikes(strikeid=muteid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Mute", day=daytime, reason=reason))
            await user.timeout(endtime, reason)
            embed = Embed(description=f"{user} **was muted** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}\n**End time:**<t:{math.ceil(endtime.timestamp())}:R>",
                            color=0x0c73d3,
                            timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
    
    @slash_command(name='unmute', description="[MOD]allows me to unmute users", scopes=[435038183231848449, 149167686159564800])
    @user()
    @reason()
    async def unmute(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given'):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.MUTE_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            await user.timeout(datetime.now(), '[UNMUTE] '+reason)
            embed = Embed(description=f"{user} **was unmuted** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                            color=0x0c73d3,
                            timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
    
    @slash_command(name='warn', sub_cmd_name='add', sub_cmd_description="[MOD]allows me to warn users", scopes=[435038183231848449, 149167686159564800])
    @user()
    @reason()
    async def warn(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str=None):
        async def ismember(ctx, user):
            for member in ctx.guild.members:
                if member == user:
                    return True
            return False

        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.MUTE_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user is ctx.author:
                await ctx.send("You can't warn yourself", ephemeral=True)
                return
            elif await ismember(ctx, user) == False:
                await ctx.send("User has to be a member of the server", ephemeral=True)
                return
            elif reason == None:
                await ctx.send("You have to include a reason", ephemeral=True)
                return
            db = await odm.connect()
            while True:
                warnid = random_string_generator()
                warnid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':warnid})
                if warnid_db == None:
                    break
                else:
                    continue
            
            warnaction = re.compile(f"^warn$", re.IGNORECASE)
            warnings = await db.find(strikes, {'guildid':ctx.guild_id, 'user':user.id, 'action':warnaction})
            if warnings == None:
                warnrolename = 'Warning-1'
            else:
                warncount = [warning.strikeid for warning in warnings]
                warnrolename = f'Warning-{len(warncount)+1}'
            
            warn_role = [role for role in ctx.guild.roles if role.name == warnrolename]
            if warn_role == []:
                role = await ctx.guild.create_role(name=warnrolename, reason='[automod]|[warn]created new warnrole as warnrole with this number did not exist yet')
            else:
                for role in warn_role:
                    role = role
            
            await user.add_role(role, reason)

            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.save(strikes(strikeid=warnid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Mute", day=daytime, reason=reason))
            try:
                embed = Embed(description=f":grey_exclamation: **You have been warned in {ctx.guild} for:** {reason}",
                          color=0x0c73d3)
                await member.send(embed=embed)
            except:
                embed = Embed(description=f"Couldn't dm {user.mention}, warn logged | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                          color=0x0c73d3)
                await ctx.send(embed=embed)
                return
            else:
                embed = Embed(description=f"{user.mention} warned | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
    
    @slash_command(name='warn', sub_cmd_name='remove', sub_cmd_description="[MOD]allows me to remove warns from users", scopes=[435038183231848449, 149167686159564800])
    @user()
    @warnid()
    @reason()
    async def warn_remove(self, ctx:InteractionContext, user:OptionTypes.USER=None, warnid:str=None, reason:str=None):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.BAN_MEMBERS)
        if (perms == True):
            async def ismember(ctx, user):
                for member in ctx.guild.members:
                    if member == user:
                        return True
                return False

            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user is ctx.author:
                await ctx.send("You can't remove a warn from yourself", ephemeral=True)
                return
            elif await ismember(ctx, user) == False:
                await ctx.send("User has to be a member of the server", ephemeral=True)
                return
            elif reason == None:
                await ctx.send("You have to include a reason", ephemeral=True)
                return
            db = await odm.connect()
            warnaction = re.compile(f"^warn$", re.IGNORECASE)
            warning = await db.find_one(strikes, {'guildid':ctx.guild_id, 'user':user.id, 'action':warnaction, 'strikeid':warnid})
            if warning == None:
                return await ctx.send(f'Warning not found for {user}', ephemeral=True)
            
            warncount = [warn.strikeid for warn in await db.find(strikes, {'guildid':ctx.guild_id, 'user':user.id, 'action':warnaction})]
            warnrolename = f'Warning-{len(warncount)}'
            warn_role = [role for role in ctx.guild.roles if role.name == warnrolename]
            for role in warn_role:
                role=role
            await user.remove_role(role, reason)
            await db.delete(warning)
            embed = Embed(description=f"warn removed from {user.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                          color=0x0c73d3)
            await ctx.send(embed=embed)
    
    @slash_command(name='warnings', description="[MOD]shows you a users warn list", scopes=[435038183231848449, 149167686159564800])
    @user()
    async def warn_list(self, ctx:InteractionContext, user:OptionTypes.USER=None):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.MUTE_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            from dis_snek.models.paginators import Paginator
            def chunks(l, n):
                n = max(1, n)
                return (l[i:i+n] for i in range(0, len(l), n))
            
            def mlis(lst, s, e):
                nc = list(chunks(lst, 20))
                mc = ''
                for testlist in nc[s:e]:
                    for m in testlist:
                        mc = mc + m
                return mc

            def newpage(title, warns):
                embed = Embed(
                    title=title,
                    description=warns,
                    color=0x0c73d3)
                return embed
            
            db = await odm.connect()
            warnaction = re.compile(f"^warn$", re.IGNORECASE)
            warnings = await db.find(strikes, {'guildid':ctx.guild_id, 'user':user.id, 'action':warnaction})
            if warnings == None:
                embed = Embed(description=f"There are no warnings for {user}.",
                          colour=0x0c73d3)
                await ctx.send(embed=embed)
                return
            warns = [f"**Warning ID:** {warn.strikeid} | **Reason:** {warn.reason} | **Moderator:** {warn.moderator} | **Day:** {warn.day}\n\n" for warn in warnings]
            
            s = -1
            e = 0
            embedcount = 1
            nc = list(chunks(warns, 20))
            
            embeds = []
            while embedcount <= len(nc):
                s = s+1
                e = e+1
                embeds.append(newpage(f'Warnings for {user}', mlis(warns, s, e)))
                embedcount = embedcount+1
                
            paginator = Paginator(
                client=self.bot, 
                pages=embeds,
                timeout_interval=80,
                show_select_menu=True)
            await paginator.send(ctx)
    
    @slash_command(name='strikes', description="[MOD]shows you a users strike list", scopes=[435038183231848449, 149167686159564800])
    @user()
    async def strikes_list(self, ctx:InteractionContext, user:OptionTypes.USER=None):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.MUTE_MEMBERS)
        if (perms == True):
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            from dis_snek.models.paginators import Paginator
            def chunks(l, n):
                n = max(1, n)
                return (l[i:i+n] for i in range(0, len(l), n))
            
            def mlis(lst, s, e):
                nc = list(chunks(lst, 20))
                mc = ''
                for testlist in nc[s:e]:
                    for m in testlist:
                        mc = mc + m
                return mc

            def newpage(title, warns):
                embed = Embed(
                    title=title,
                    description=warns,
                    color=0x0c73d3)
                return embed
            
            db = await odm.connect()
            all_strikes = await db.find(strikes, {'guildid':ctx.guild_id, 'user':user.id})
            if all_strikes == None:
                embed = Embed(description=f"There are no strikes for {user}.",
                          colour=0x0c73d3)
                await ctx.send(embed=embed)
                return
            allstrikes = [f"**Strike ID:** {s.strikeid} | **Action:** {s.action} | **Reason:** {s.reason} | **Moderator:** {s.moderator} | **Day:** {s.day}\n\n" for s in all_strikes]
            
            s = -1
            e = 0
            embedcount = 1
            nc = list(chunks(allstrikes, 20))
            
            embeds = []
            while embedcount <= len(nc):
                s = s+1
                e = e+1
                embeds.append(newpage(f'Strikes for {user}', mlis(allstrikes, s, e)))
                embedcount = embedcount+1
                
            paginator = Paginator(
                client=self.bot, 
                pages=embeds,
                timeout_interval=80,
                show_select_menu=True)
            await paginator.send(ctx)
    
def setup(bot):
    Moderation(bot)