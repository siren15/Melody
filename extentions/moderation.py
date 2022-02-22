import math
import re
import random

from dateutil.relativedelta import *
from datetime import datetime, timedelta
from dis_snek import Snake, Scale, listen, Embed, Permissions, slash_command, InteractionContext,  OptionTypes, check
from dis_snek.models.discord.base import DiscordObject
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *
from dis_snek.client.errors import NotFound


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

def find_member(ctx, userid):
    members = [m for m in ctx.guild.members if m.id == userid]
    if members != []:
        for m in members:
            return m
    return None

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
    
    @listen()
    async def on_ready(self):
        self.unban_task.start()
    
    @slash_command(name='delete', description="[MOD]allows me to delete messages")
    @amount()
    @reason()
    @check(member_permissions(Permissions.MANAGE_MESSAGES))
    async def delete_messages(self, ctx:InteractionContext, amount:int=0, reason:str='No reason given'):
        
        if (amount <= 0) or (amount >= 1000):
            embed = Embed(description=f":x: Amount can't be less than 1 or more than 1000",
                        color=0xDD2222)
            await ctx.send(embed=embed)
            return
        deleted = await ctx.channel.purge(deletion_limit=amount, search_limit=1000, reason=reason)
        embed = Embed(description=f"Deleted {deleted} messages",
                            timestamp=datetime.utcnow(),
                            color=0x0c73d3)
        embed.set_footer(text=f"Auctioned by: {ctx.author}|{ctx.author.id}")
        await ctx.send(embed=embed)
    
    @slash_command(name='userpurge', description="[MOD]allows me to purge users messages")
    @user()
    @amount()
    @reason()
    @check(member_permissions(Permissions.MANAGE_MESSAGES))
    async def userpurge(self, ctx:InteractionContext, user:OptionTypes.USER=None, amount:int=0, reason:str='No reason given'):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        elif user is ctx.author:
            await ctx.send("You can't purge yourself", ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member != None:
            if member.has_permission(Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't purge an admin", ephemeral=True)
                return
            elif member.has_permission(Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't purge users with ban perms", ephemeral=True)
                return
            elif member.has_permission(Permissions.MANAGE_MESSAGES) == True:
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
    
    @slash_command(name='ban', description="[MOD]allows me to ban users from the server")
    @user()
    @bantime()
    @deletedays()
    @reason()
    @check(member_permissions(Permissions.BAN_MEMBERS))
    async def ban(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given', bantime:str=None, deletedays:int=0):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        elif user is ctx.author:
            await ctx.send("You can't ban yourself", ephemeral=True)
            return
        try:
            ctx.guild.get_ban(user)
        except NotFound:
            db = await odm.connect()
            member = find_member(ctx, user.id)
            if member != None:
                if member.has_permission(Permissions.ADMINISTRATOR) == True:
                    await ctx.send("You can't ban an admin", ephemeral=True)
                    return
                elif member.has_permission(Permissions.BAN_MEMBERS) == True:
                    await ctx.send("You can't ban users with ban perms", ephemeral=True)
                    return
                elif ctx.author.top_role == member.top_role:
                    embed = Embed(description=f":x: You can't ban people with the same role as you!",
                                color=0xDD2222)
                    await ctx.send(embed=embed)
                    return

                elif ctx.author.top_role.position < member.top_role.position:
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
                tempbanned = await db.find_one(tempbans, {"user":user.id, "guildid":ctx.guild_id})
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
                
                if (seconds < 3600) or (seconds > 94672800):
                    await ctx.send("Ban time can't be shorter than 1 hour and longer than 3 years")
                    return
                
                await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Temp Ban", day=daytime, reason=reason))
                await db.save(tempbans(guildid=ctx.guild_id, user=user.id, starttime=datetime.now(), endtime=endtime, banreason=reason))
                
                embed = Embed(description=f"{user} **was banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}\n**End time:**<t:{math.ceil(endtime.timestamp())}:R>",
                                color=0x0c73d3,
                                timestamp=datetime.utcnow())
                embed.set_thumbnail(url=user.avatar.url)
                await ctx.send(embed=embed)
            await ctx.guild.ban(DiscordObject(id=int(user.id), client=self.bot), reason=reason, delete_message_days=deletedays)
    
    @slash_command(name='unban', description="[MOD]allows me to unban users from the server")
    @user()
    @reason()
    @check(member_permissions(Permissions.BAN_MEMBERS))
    async def unban(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given', bantime:str=None, deletedays:int=0):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        elif user == ctx.author:
            embed = Embed(description=f":x: This is not how that works buddy...",
                        color=0xDD2222)
            await ctx.send(embed=embed)
            return
        try:
            ctx.guild.get_ban(user)
        except NotFound:
            embed = Embed(description=f":x: {user} not banned",
                        color=0xDD2222)
            await ctx.send(embed=embed)
            return
        else:
            await ctx.guild.unban(user, reason)
            embed = Embed(description=f"{user} **was unbanned by {ctx.author.mention}** | {reason} \n**User ID:** {user.id}",
                                color=0x0c73d3,
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

    @slash_command(name='kick', description="[MOD]allows me to kick users from the server")
    @user()
    @reason()
    @check(member_permissions(Permissions.KICK_MEMBERS))
    async def kick(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given'):
        member = find_member(ctx, user.id)
        if member != None:
            if user == None:
                await ctx.send('You have to include a user', ephemeral=True)
                return
            elif user is ctx.author:
                await ctx.send("You can't kick yourself", ephemeral=True)
                return

            if member.has_permission(Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't kick an admin", ephemeral=True)
                return
            elif member.has_permission(Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't kick users with ban perms", ephemeral=True)
                return
            elif member.has_permission(Permissions.KICK_MEMBERS) == True:
                await ctx.send("You can't kick users with kick perms", ephemeral=True)
                return
            db = await odm.connect()
            if ctx.author.top_role == member.top_role:
                embed = Embed(description=f":x: You can't kick people with the same role as you!",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return

            if ctx.author.top_role.position < member.top_role.position:
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
        else:
            raise UserNotFound()
    
    @slash_command(name='mute', description="[MOD]allows me to mute users")
    @user()
    @mutetime()
    @reason()
    @check(member_permissions(Permissions.MODERATE_MEMBERS))
    async def mute(self, ctx:InteractionContext, user:OptionTypes.USER=None, mutetime:str=None, reason:str='No reason given'):
        
        if user == None:
            await ctx.send('You have to include a member', ephemeral=True)
            return
        elif user is ctx.author:
            await ctx.send("You can't mute yourself", ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member != None:
            
            if member.has_permission(Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't mute an admin", ephemeral=True)
                return
            elif member.has_permission(Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't mute users with ban perms", ephemeral=True)
                return
            elif member.has_permission(Permissions.KICK_MEMBERS) == True:
                await ctx.send("You can't mute users with kick perms", ephemeral=True)
                return
            
            if ctx.author.top_role == member.top_role:
                embed = Embed(description=f":x: You can't mute people with the same role as you!",
                            color=0xDD2222)
                await ctx.send(embed=embed)
                return

            if ctx.author.top_role.position < member.top_role.position:
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
            await db.save(strikes(strikeid=muteid, guildid=ctx.guild_id, user=member.id, moderator=ctx.author.id, action="Mute", day=daytime, reason=reason))
            await member.timeout(endtime, reason)
            embed = Embed(description=f"{member} **was muted** | {reason} \n**User ID:** {member.id} \n**Actioned by:** {ctx.author.mention}\n**End time:**<t:{math.ceil(endtime.timestamp())}:R>",
                            color=0x0c73d3,
                            timestamp=datetime.utcnow())
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.send(embed=embed)
        else:
            raise UserNotFound()
    
    @slash_command(name='unmute', description="[MOD]allows me to unmute users")
    @user()
    @reason()
    @check(member_permissions(Permissions.MODERATE_MEMBERS))
    async def unmute(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str='No reason given'):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member != None:
            await member.timeout(datetime.now(), '[UNMUTE] '+reason)
            embed = Embed(description=f"{user} **was unmuted** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                            color=0x0c73d3,
                            timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
        else:
            raise UserNotFound()
        
    @slash_command(name='warn', sub_cmd_name='add', sub_cmd_description="[MOD]allows me to warn users")
    @user()
    @reason()
    @check(member_permissions(Permissions.MODERATE_MEMBERS))
    async def warn(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str=None):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        elif user is ctx.author:
            await ctx.send("You can't warn yourself", ephemeral=True)
            return
        elif reason == None:
            await ctx.send("You have to include a reason", ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member != None:
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
            await db.save(strikes(strikeid=warnid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Warn", day=daytime, reason=reason))
            try:
                embed = Embed(description=f":grey_exclamation: **You have been warned in {ctx.guild.name} for:** {reason}",
                        color=0x0c73d3)
                await user.send(embed=embed)
            except:
                embed = Embed(description=f"Couldn't dm {user.mention}, warn logged and user was given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0x0c73d3)
                await ctx.send(embed=embed)
                return
            else:
                embed = Embed(description=f"{user.mention} warned and given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
        else:
            raise UserNotFound()
    
    @slash_command(name='warn', sub_cmd_name='remove', sub_cmd_description="[MOD]allows me to remove warns from users")
    @user()
    @warnid()
    @reason()
    @check(member_permissions(Permissions.MODERATE_MEMBERS))
    async def warn_remove(self, ctx:InteractionContext, user:OptionTypes.USER=None, warnid:str=None, reason:str=None):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        elif user is ctx.author:
            await ctx.send("You can't remove a warn from yourself", ephemeral=True)
            return
        elif reason == None:
            await ctx.send("You have to include a reason", ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member != None:
            db = await odm.connect()
            warnaction = re.compile(f"^warn$", re.IGNORECASE)
            warning = await db.find_one(strikes, {'guildid':ctx.guild_id, 'user':user.id, 'action':warnaction, 'strikeid':warnid})
            if warning == None:
                return await ctx.send(f'Warning not found for {user}', ephemeral=True)
            
            warncount = [warn.strikeid for warn in await db.find(strikes, {'guildid':ctx.guild_id, 'user':user.id, 'action':warnaction})]
            warnrolename = f'Warning-{len(warncount)}'
            warn_role = [role for role in ctx.guild.roles if role.name == warnrolename]
            for role in warn_role:
                await user.remove_role(role, reason)
                await db.delete(warning)
                embed = Embed(description=f"warn removed from {user.mention}, {role.mention} was taken away | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
        else:
            raise UserNotFound()
    
    @slash_command(name='warnings', description="[MOD]shows you a users warn list")
    @user()
    @check(member_permissions(Permissions.MODERATE_MEMBERS))
    async def warn_list(self, ctx:InteractionContext, user:OptionTypes.USER=None):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        from .src.paginators import Paginator
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
        warnings = await db.find(strikes, {'guildid':ctx.guild_id, 'user':user.id, 'action':'Warn'})
        warns = [f"**Warning ID:** {warn.strikeid} | **Reason:** {warn.reason} | **Moderator:** {warn.moderator} | **Day:** {warn.day}\n\n" for warn in warnings]
        if warns == []:
            embed = Embed(description=f"There are no warnings for {user}.",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
            return
        
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
            show_select_menu=False)
        await paginator.send(ctx)
    
    @slash_command(name='strikes', description="[MOD]shows you a users strike list")
    @user()
    @check(member_permissions(Permissions.MODERATE_MEMBERS))
    async def strikes_list(self, ctx:InteractionContext, user:OptionTypes.USER=None):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        from .src.paginators import Paginator
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
        allstrikes = [f"**Strike ID:** {s.strikeid} | **Action:** {s.action} | **Reason:** {s.reason} | **Moderator:** {s.moderator} | **Day:** {s.day}\n\n" for s in all_strikes]
        if allstrikes == []:
            embed = Embed(description=f"There are no strikes for {user}.",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
            return

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
            show_select_menu=False)
        await paginator.send(ctx)
    
    @slash_command(name='limbo', sub_cmd_name='add', sub_cmd_description="[MOD]allows me to limbo users", scopes=[435038183231848449,149167686159564800])
    @user()
    @reason()
    @check(member_permissions(Permissions.BAN_MEMBERS))
    async def limbo_add(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str=None):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        if reason == None:
            await ctx.send('You have to include a reason', ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member != None:
            if member.has_permission(Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't limbo an admin", ephemeral=True)
                return
            elif member.has_permission(Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't limbo users with ban perms", ephemeral=True)
                return
            elif member.has_permission(Permissions.KICK_MEMBERS) == True:
                await ctx.send("You can't limbo users with kick perms", ephemeral=True)
                return
            
            if member.roles:
                if ctx.author.top_role == member.top_role:
                    embed = Embed(description=f":x: You can't limbo people with the same role as you!",
                                color=0xDD2222)
                    await ctx.send(embed=embed)
                    return

                if ctx.author.top_role.position < member.top_role.position:
                    embed = Embed(description=f":x: You can't limbo people with roles higher than yours!",
                                color=0xDD2222)
                    await ctx.send(embed=embed)
                    return
            db = await odm.connect()
            limboed = await db.find_one(limbo, {'guildid':ctx.guild_id, 'userid':member.id})
            if limboed != None:
                await ctx.send(f'{member.mention} is already in limbo', ephemeral=True)
                return
            limbo_role = [role for role in ctx.guild.roles if role.name == 'Limbo']
            if limbo_role == []:
                limborole = await ctx.guild.create_role(name='Limbo', reason='[automod]|[limbo]created new limbo role as limbo role did not exist yet')
            else:
                for role in limbo_role:
                    limborole = role
            user_roles = [role for role in member.roles if role.name != '@everyone']
            ur = ''
            for r in user_roles:
                ur = ur+f"{r.id},"
            await db.save(limbo(guildid=ctx.guild_id, userid=member.id, roles=ur, reason=reason))
            for user_role in user_roles:
                await member.remove_role(user_role)
            await member.add_role(limborole)
            embed = Embed(description=f"{member.mention} put in limbo | {reason} \n**User ID:** {member.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
            while True:
                warnid = random_string_generator()
                warnid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':warnid})
                if warnid_db == None:
                    break
                else:
                    continue
            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.save(strikes(strikeid=warnid, guildid=ctx.guild_id, user=member.id, moderator=ctx.author.id, action="Limbo", day=daytime, reason=reason))
        else:
            raise UserNotFound()
    
    @slash_command(name='limbo', sub_cmd_name='remove', sub_cmd_description="[MOD]allows me to let users out of limbo", scopes=[435038183231848449,149167686159564800])
    @user()
    @reason()
    @check(member_permissions(Permissions.BAN_MEMBERS))
    async def limbo_remove(self, ctx:InteractionContext, user:OptionTypes.USER=None, reason:str=None):
        
        if user == None:
            await ctx.send('You have to include a user', ephemeral=True)
            return
        if reason == None:
            await ctx.send('You have to include a reason', ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member != None:
            db = await odm.connect()
            limboed = await db.find_one(limbo, {'guildid':ctx.guild_id, 'userid':member.id})
            if limboed == None:
                await ctx.send(f'{member.mention} is not in limbo', ephemeral=True)
                return

            limborole = [role for role in member.roles if role.name == 'Limbo']
            for limborole in limborole:
                limborole = limborole

            user_limbo_data = await db.find_one(limbo, {"guildid":ctx.guild_id, "userid":member.id})
            roles = [ctx.guild.get_role(int(id_)) for id_ in user_limbo_data.roles.split(",") if len(id_)]
            for r in roles:
                await member.add_role(r)
            await member.remove_role(limborole)

            await db.delete(user_limbo_data)

            embed = Embed(description=f"{member.mention} let out of limbo | {reason} \n**User ID:** {member.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
        else:
            raise UserNotFound
    
    # @listen()
    # async def on_message_create(self, event):
    #     message = event.message
    #     if message.guild.id == 149167686159564800:
    #         db = await odm.connect()
    #         channel = await db.find_one(logs, {'guild_id':message.guild.id})
    #         if channel != None:
    #             log_channel = message.guild.get_channel(int(channel.channel_id))

    #             if message.channel.id == 736680179253903491:
    #                 embed = Embed(title="Limbo log", timestamp=datetime.utcnow(), color=0x0c73d3)
    #                 embed.set_thumbnail(url=f'{message.author.avatar.url}')
    #                 embed.add_field(name=f"{message.author}", value=f"{message.content}", inline=False)
    #                 embed.set_footer(text=f'User ID: {message.author.id}')
    #                 await log_channel.send(embed=embed)

    from dis_snek.models.snek.tasks import Task
    from dis_snek.models.snek.tasks.triggers import IntervalTrigger

    @Task.create(IntervalTrigger(seconds=60))
    async def unban_task(self):
        db = await odm.connect()
        endtimes = await db.find(tempbans, {'endtime':{'$lte':datetime.now()}})
        for m in endtimes:
            try:
                guild = await self.bot.get_guild(m.guildid)
            except NotFound:
                print(f"[automod]|[unban_task]{m.guildid} not found in the guild list")
                await db.delete(m)
                return
            try:
                guild.get_ban(m.user)
            except NotFound:
                print(f"[automod]|[unban_task]{m.user} not found in the ban list")
                await db.delete(m)
                return
            await guild.unban(m.user, '[automod]|[unban_task] ban time expired')
            await db.delete(m)

def setup(bot):
    Moderation(bot)