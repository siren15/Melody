import asyncio
import math
import random

from dateutil.relativedelta import *
from datetime import datetime, timedelta
from interactions import Client, Extension, listen, Embed, Permissions, slash_command, SlashContext, InteractionContext,  OptionType, TextStyles, Modal, ModalContext, SlashCommandChoice, SlashCommand, InputText
from interactions.ext.paginators import Paginator
from interactions.models.discord.base import DiscordObject
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *
from interactions.client.errors import NotFound, BadRequest, HTTPException


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
    return ctx.guild.get_member(userid)

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

class Moderation(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
    
    @listen()
    async def on_ready(self):
        self.unban_task.start()
    
    @slash_command(name='modapp', description="Apply to be a moderator", scopes=[435038183231848449,149167686159564800])
    async def modapps_modal(self, ctx:SlashContext):
        await ctx.defer()
        m = Modal(title='Mod Application', components=[
            InputText(
                label="Age & Country (Looking for variety!)",
                style=TextStyles.SHORT,
                custom_id=f'age_country',
                placeholder="What is your age and what country are you from?",
                required=True,
                max_length=100
            ),
            InputText(
                label="Can you handle uneasy/difficult situations?",
                style=TextStyles.SHORT,
                custom_id=f'wimp',
                placeholder="Can you handle uncomfortable and difficult situations?",
                required=True,
                max_length=100
            ),
            InputText(
                label="How yould you handle this?",
                style=TextStyles.PARAGRAPH,
                custom_id=f'situation',
                placeholder="How would you handle the situation described in the announcement?(https://pastebin.com/raw/MSa1Gbjn)",
                required=True,
                max_length=1024
            ),
            InputText(
                label="Why do you want to be part of our staff?",
                style=TextStyles.PARAGRAPH,
                custom_id=f'reason',
                placeholder="Why do you want to be part of our staff?",
                required=True,
                max_length=1024
            )
        ],custom_id=f'{random_string_generator()}_modapp_modal')
    
        await ctx.send_modal(modal=m)
        try:
            modal_recived: ModalContext = await ctx.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
        except asyncio.TimeoutError:
            return await ctx.author.send(f":x: You took longer than 10 minutes to respond to the mod application  Please try again.")
        age_country = modal_recived.responses.get('age_country')
        wimp = modal_recived.responses.get('wimp')
        situation = modal_recived.responses.get('situation')
        reason = modal_recived.responses.get('reason')

        embed = Embed(title=f"Mod Application - {ctx.author.display_name}",
                      thumbnail=ctx.author.display_avatar.url,
                      color=0xf6cd4f)
        embed.add_field(name='Age & Country (Looking for variety!)', value=age_country, inline=False)
        embed.add_field(name='Can you handle uncomfortable and difficult situations?', value=wimp, inline=False)
        embed.add_field(name='How yould you handle the situation described in the announcement?', value=situation, inline=False)
        embed.add_field(name='Why do you want to be part of our staff?', value=reason, inline=False)
        embed.set_footer(text=f"{ctx.author}|{ctx.author.id}")
        channel = await self.bot.fetch_channel(639258147734683659)
        await channel.send(embed=embed)
        await modal_recived.author.send(f"Your mod application has been sent to the staff team.", embed=embed)
        await modal_recived.send(f"Your mod application has been sent to the staff team.", ephemeral=True)


    @slash_command(name='delete', description="Allows you to delete messages, max: 700",
        default_member_permissions=Permissions.MANAGE_MESSAGES
    )
    @amount()
    @reason()
    async def delete_messages(self, ctx:InteractionContext, amount:int=0, reason:str='MISSING'):
        """/delete
        Description:
            Allows you to delete messages, max: 700

        Args:
            amount (int, optional): Amount of messages to delete, max 700
            reason (str, optional): Reason
        """
        def chunks(l, n):
            n = max(1, n)
            return (l[i:i+n] for i in range(0, len(l), n))
        await ctx.defer()
        if (amount < 2) or (amount > 700):
            embed = Embed(description=f":x: Amount can't be less than 2 or more than 700",
                        color=0xDD2222)
            await ctx.send(embed=embed)
            return
        messages = await ctx.channel.fetch_messages(limit=(amount+1))
        messages.pop(0)
        new_msgs = []
        old_msgs = []
        for message in messages:
            twa = datetime.now() - timedelta(weeks=2)
            cat = await seperate_string_number(str(message.created_at))
            ca = datetime.fromtimestamp(int(cat[3]))
            if ca > twa:
                new_msgs.append(message)
            elif ca < twa:
                old_msgs.append(message)
        for new_msgs in chunks(new_msgs, 100):
            await ctx.channel.delete_messages(new_msgs, reason)
        for msg in old_msgs:
            await msg.delete()
        embed = Embed(description=f"I've deleted {len(new_msgs)+len(old_msgs)} messages\nReason: {reason}",
                            timestamp=datetime.utcnow(),
                            color=0xffcc50)
        embed.set_footer(text=f"Actioned by: {ctx.author}|{ctx.author.id}")
        await ctx.send(embed=embed)
    
    @slash_command(name='userpurge', description="Allows you to purge users messages",
        default_member_permissions=Permissions.MANAGE_MESSAGES
    )
    @user()
    @amount()
    @reason()
    async def userpurge(self, ctx:InteractionContext, user:OptionType.USER=None, amount:int=0, reason:str='No reason given'):
        """/userpurge
        Description:
            Allows you to purge users messages
        Args:
            user (OptionType.USER, optional): User
            amount (int, optional): Amount of messages to purge, per channel, max 300
            reason (str, optional): Reason
        """
        def chunks(l, n):
            n = max(1, n)
            return (l[i:i+n] for i in range(0, len(l), n))
        await ctx.defer()
        if user is ctx.author:
            await ctx.send("You can't purge yourself", ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member is not None:
            if member.has_permission(Permissions.ADMINISTRATOR) == True:
                await ctx.send("You can't purge an admin", ephemeral=True)
                return
            elif member.has_permission(Permissions.BAN_MEMBERS) == True:
                await ctx.send("You can't purge users with ban perms", ephemeral=True)
                return
            elif member.has_permission(Permissions.MANAGE_MESSAGES) == True:
                await ctx.send("You can't purge users with manage messages perms", ephemeral=True)
                return
        if (amount < 2) or (amount > 300):
            embed = Embed(description=f":x: Amount can't be less than 2 or more than 300",
                        color=0xDD2222)
            await ctx.send(embed=embed)
            return

        for channel in ctx.guild.channels:
            messages = await channel.fetch_messages(limit=(amount+1))
            messages.pop(0)
            new_msgs = []
            old_msgs = []
            for message in messages:
                twa = datetime.now() - timedelta(weeks=2)
                cat = await seperate_string_number(str(message.created_at))
                ca = datetime.fromtimestamp(int(cat[3]))
                if ca > twa:
                    new_msgs.append(message)
                elif ca < twa:
                    old_msgs.append(message)
            for new_msgs in chunks(new_msgs, 100):
                await ctx.channel.delete_messages(new_msgs, reason)
            for msg in old_msgs:
                await msg.delete()
        embed = Embed(description=f"I've purged {len(new_msgs)+len(old_msgs)} messages from {user}\nReason: {reason}",
                            timestamp=datetime.utcnow(),
                            color=0xffcc50)
        embed.set_footer(text=f"Actioned by: {ctx.author}|{ctx.author.id}")
        await ctx.send(embed=embed)
    
    @slash_command(name='ban', description="Allows you to ban users from the server",
        default_member_permissions=Permissions.BAN_MEMBERS
    )
    @user()
    @bantime()
    @deletedays()
    @reason()
    async def ban(self, ctx:InteractionContext, user:OptionType.USER=None, reason:str='No reason given', bantime:str=None, deletedays:int=0):
        """/ban
        Description:
            Ban a user from the server. 
        
        Args:
            user: User
            reason: Set the reason for the ban
            bantime: Optionally specify ban time Examples: `10 S`, `10 M`, `10 H`, `10 D`. It can't be shorter than 1 hour and longer than 3 years
            deletedays: Delete the last x days of messages from that user. You can choose from 0 to 7.
        """
        await ctx.defer()
        if user is ctx.author:
            await ctx.send("You can't ban yourself", ephemeral=True)
            return
        banned = await ctx.guild.fetch_ban(user)
        if banned is None:     
            member = find_member(ctx, user.id)
            if member is not None:
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

            # while True:
            #     banid = random_string_generator()
            #     banid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':banid})
            #     if banid_db is None:
            #         break
            #     else:
            #         continue
            # daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            if bantime is None:
                # await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Ban", day=daytime, reason=reason))
                embed = Embed(description=f"{user} **was banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                                color=0xffcc50,
                                timestamp=datetime.utcnow())
                embed.set_thumbnail(url=user.avatar.url)
                await ctx.send(embed=embed)
            else:
                tempbanned = await db.tempbans.find_one({"user":user.id, "guildid":ctx.guild_id})
                if tempbanned is not None:
                    await tempbanned.delete()
                
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
                
                # await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Temp Ban", day=daytime, reason=reason))
                await db.tempbans(guildid=ctx.guild_id, user=user.id, starttime=datetime.now(), endtime=endtime, banreason=reason).insert()
                
                embed = Embed(description=f"{user} **was temporarily banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}\n**End time:**<t:{math.ceil(endtime.timestamp())}:R>",
                                color=0xffcc50,
                                timestamp=datetime.utcnow())
                embed.set_thumbnail(url=user.avatar.url)
                await ctx.send(embed=embed)
            await ctx.guild.ban(DiscordObject(id=int(user.id), client=self.bot), reason=reason, delete_message_days=deletedays)
        else:
            await ctx.send(f'{user} already banned')
    
    @slash_command(name='unban', description="Allows you to unban users from the server",
        default_member_permissions=Permissions.BAN_MEMBERS
    )
    @user()
    @reason()
    async def unban(self, ctx:InteractionContext, user:OptionType.USER=None, reason:str='No reason given'):
        """/unban
        Description:
            Unban a user from the server.
        
        Args:
            user: User to unban
            reason: Specify the reason for the unban
        """
        await ctx.defer()
        if user == ctx.author:
            embed = Embed(description=f":x: This is not how that works buddy...",
                        color=0xDD2222)
            await ctx.send(embed=embed)
            return
        banned = await ctx.guild.fetch_ban(user)
        if banned is None:
            embed = Embed(description=f":x: {user} not banned",
                        color=0xDD2222)
            await ctx.send(embed=embed)
            return
        else:
            await ctx.guild.unban(user, reason)
            embed = Embed(description=f"{user} **was unbanned by {ctx.author.mention}** | {reason} \n**User ID:** {user.id}",
                                color=0xffcc50,
                                timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
            # 
            # while True:
            #     banid = random_string_generator()
            #     banid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':banid})
            #     if banid_db is None:
            #         break
            #     else:
            #         continue
            # daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            # await db.save(strikes(strikeid=banid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Unban", day=daytime, reason=reason))

    @slash_command(name='kick', description="[MOD]allows me to kick users from the server",
        default_member_permissions=Permissions.KICK_MEMBERS
    )
    @user()
    @reason()
    async def kick(self, ctx:InteractionContext, user:OptionType.USER=None, reason:str='No reason given'):
        """/kick
        Description:
            The kick function kicks a user from the server.
            
        
        Args:
            user: User to kick
            reason: Specify the reason for the kick
        """
        await ctx.defer()
        member = find_member(ctx, user.id)
        if member is not None:
            # if user is None:
            #     await ctx.send('You have to include a user', ephemeral=True)
            #     return
            if user is ctx.author:
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
            # 
            # while True:
            #     kickid = random_string_generator()
            #     kickid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':kickid})
            #     if kickid_db is None:
            #         break
            #     else:
            #         continue
            # daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            # await db.save(strikes(strikeid=kickid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Kick", day=daytime, reason=reason))
            await ctx.guild.kick(user, reason)
            embed = Embed(description=f"{user} **was kicked** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0xffcc50,
                        timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
        else:
            raise UserNotFound()
    
    @slash_command(name='mute', description="Allows you to mute users",
        default_member_permissions=Permissions.MODERATE_MEMBERS
    )
    @user()
    @mutetime()
    @reason()
    async def mute(self, ctx:InteractionContext, user:OptionType.USER=None, mutetime:str=None, reason:str='No reason given'):
        """/mute
        Description:
            Mutes a user for a specified amount of time. Mute time can't be shorter than 10 seconds and longer than 28 days.
                
        Args:
            user: User that you want to mute
            mutetime: Specify the time, Examples: `10 S`, `10 M`, `10 H`, `10 D`
            reason: Specify the reason for muting a user
        """
        await ctx.defer()
        if user is ctx.author:
            await ctx.send("You can't mute yourself", ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member is not None:
            
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
            # daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            # 
            # while True:
            #     muteid = random_string_generator()
            #     muteid_db = await db.find_one(strikes, {'guildid':ctx.guild_id, 'strikeid':muteid})
            #     if muteid_db is None:
            #         break
            #     else:
            #         continue
            # await db.save(strikes(strikeid=muteid, guildid=ctx.guild_id, user=member.id, moderator=ctx.author.id, action="Mute", day=daytime, reason=reason))
            await member.timeout(endtime, reason)
            embed = Embed(description=f"{member} **was muted** | {reason} \n**User ID:** {member.id} \n**Actioned by:** {ctx.author.mention}\n**End time:**<t:{math.ceil(endtime.timestamp())}:R>",
                            color=0xffcc50,
                            timestamp=datetime.utcnow())
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.send(embed=embed)
        else:
            raise UserNotFound()
    
    @slash_command(name='unmute', description="[MOD]allows me to unmute users",
        default_member_permissions=Permissions.MODERATE_MEMBERS
    )
    @user()
    @reason()
    async def unmute(self, ctx:InteractionContext, user:OptionType.USER=None, reason:str='No reason given'):
        """/unmute
        Description:
            Unmute a user.
            
        
        Args:
            user: User
            reason: Set the reason for unmuting a user
        """
        await ctx.defer()
        member = find_member(ctx, user.id)
        if member is not None:
            await member.timeout(None, '[UNMUTE] '+reason)
            embed = Embed(description=f"{user} **was unmuted** | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                            color=0xffcc50,
                            timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
        else:
            raise UserNotFound()
    
    warn = SlashCommand(name='warn', default_member_permissions=Permissions.MODERATE_MEMBERS)

    @warn.subcommand('add', sub_cmd_description='Add a warn to a member.')
    @slash_option(
        name="type",
        description="Warn type",
        required=True,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Minor", value='Minor'),
            SlashCommandChoice(name="Major", value='Major'),
        ]
    )
    @user()
    @reason()
    async def warnadd(self, ctx:InteractionContext, type:str, user:OptionType.USER, reason:str=None):
        """/warn add
        Description:
            Gives user a warning, depending on type it gives them a warn role, It also sends them a warn DM if available.
        
        Args:
            type: Specify the type of warning, either major or minor
            user: User
            reason: Reason for the warning
        """
        await ctx.defer()
        if user is ctx.author:
            await ctx.send("You can't warn yourself", ephemeral=True)
            return
        elif reason is None:
            await ctx.send("You have to include a reason", ephemeral=True)
            return
        member = ctx.guild.get_member(user.id)
        if member is not None:
            while True:
                warnid = random_string_generator()
                warnid_db = await db.strikes.find_one({'guildid':ctx.guild_id, 'strikeid':warnid})
                if warnid_db is None:
                    break
                else:
                    continue
            
            if type == 'Major':
                warnings = db.strikes.find({'guildid':ctx.guild_id, 'user':user.id, 'action':{'$regex':'^warn$', '$options':'i'}, 'type':'Major'})
                warncount = []
                async for warn in warnings:
                    warncount.append(warn.strikeid)
                if warncount == []:
                    warnrolename = 'Warning-1'
                else:
                    warnrolename = f'Warning-{len(warncount)+1}'
                
                warn_role = [role for role in ctx.guild.roles if role.name == warnrolename]
                if warn_role == []:
                    role = await ctx.guild.create_role(name=warnrolename, reason='[automod]|[warn]created new warnrole as warnrole with this number did not exist yet')
                else:
                    for role in warn_role:
                        role = role
                
                await user.add_role(role, reason)

                try:
                    embed = Embed(
                        title='Major Warning',
                        description=f":grey_exclamation: **You've been given a major warning in {ctx.guild.name} for:** {reason}",
                        color=0xffcc50)
                    await user.send(embed=embed)
                except HTTPException:
                    embed = Embed(
                        title='Major Warning',
                        description=f"Couldn't dm {user.mention}, major warn logged and user was given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0xffcc50)
                    await ctx.send(embed=embed)
                else:
                    embed = Embed(
                        title='Major Warning',
                        description=f"{user.mention} warned and given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0xffcc50)
                    await ctx.send(embed=embed)
            elif type == 'Minor':
                try:
                    embed = Embed(
                        title='Minor Warning',
                        description=f":grey_exclamation: **You've been given a minor warning in {ctx.guild.name} for:** {reason}",
                        color=0xffcc50)
                    await user.send(embed=embed)
                except HTTPException:
                    embed = Embed(
                        title='Minor Warning',
                        description=f"Couldn't dm {user.mention}, minor warn logged | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0xffcc50
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = Embed(
                        title='Minor Warning', 
                        description=f"{user.mention} warned | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0xffcc50)
                    await ctx.send(embed=embed)

            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.strikes(type=type, strikeid=warnid, guildid=ctx.guild_id, user=user.id, moderator=ctx.author.id, action="Warn", day=daytime, reason=reason).insert()

            mw = db.strikes.find({'type':'Minor', 'guildid':ctx.guild_id, 'user':user.id, 'action':{'$regex':'^warn$', '$options':'i'}})
            mwc = []
            counter = []
            i = 1
            while i < 11:
                v = 3 * i
                counter.append(v)
                i = i + 1
            async for warn in mw:
                mwc.append(warn.strikeid)
            if len(mwc) in counter:
                await ctx.send(f'**[REMINDER]** {user} now has {len(mwc)} minor warnings.')
        else:
            raise UserNotFound()
    
    @warn.subcommand('remove', sub_cmd_description='Remove a warn from a member.')
    @user()
    @warnid()
    @reason()
    async def warn_remove(self, ctx:InteractionContext, user:OptionType.USER=None, warnid:str=None, reason:str=None):
        """/warn remove
        Description:
            Remove a warn from a user.
        
        Args:
            user: User to remove a warn from
            warnid: warnID
            reason: Specify the reason for removing the warn
        """
        await ctx.defer()
        if user is ctx.author:
            await ctx.send("You can't remove a warn from yourself", ephemeral=True)
            return
        elif reason is None:
            await ctx.send("You have to include a reason", ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member is not None:
            warning = await db.strikes.find_one({'guildid':ctx.guild_id, 'user':user.id, 'action':{'$regex':'^warn$', '$options':'i'}, 'strikeid':warnid})
            if warning is None:
                return await ctx.send(f'Warning not found for {user}', ephemeral=True)
            warncount = []
            async for warn in db.strikes.find({'guildid':ctx.guild_id, 'user':user.id, 'action':{'$regex':'^warn$', '$options':'i'}}):
                warncount.append(warn.strikeid)
            warnrolename = f'Warning-{len(warncount)}'
            warn_role = [role for role in ctx.guild.roles if role.name == warnrolename]
            for role in warn_role:
                await user.remove_role(role, reason)
                await warning.delete()
                embed = Embed(description=f"warn removed from {user.mention}, {role.mention} was taken away | {reason} \n**User ID:** {user.id} \n**Actioned by:** {ctx.author.mention}",
                            color=0xffcc50)
                await ctx.send(embed=embed)
        else:
            raise UserNotFound()
    
    @warn.subcommand('removeall', sub_cmd_description='Remove all warns from a member.')
    @user()
    async def warnremoveall(self, ctx:InteractionContext, user: OptionType.USER):
        """/warn removeall
        Description:
            Removes all warns from a user.
            
        Args:
            user: The user that you want to remove all warns from
        """
        await ctx.defer()
        if ctx.author != 400713431423909889:
            await ctx.send("This command cannot be used.", ephemeral=True)
            return
        if user is ctx.author:
            await ctx.send("You can't remove a warn from yourself", ephemeral=True)
            return
        await db.strikes.find({'guildid':ctx.guild_id, 'user':user.id, 'action':'Warn'}).delete_many()
        await ctx.send(f'All warns removed from {user}')

    @slash_command(name='warnings', description="shows you a users warn list",
        default_member_permissions=Permissions.MODERATE_MEMBERS
    )
    @user()
    async def warn_list(self, ctx:InteractionContext, user:OptionType.USER):
        """/warnings
        Description:
            Display a list of warnings for a user.
        
        Args:
            user: User
        """
        await ctx.defer()
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
                color=0xffcc50)
            return embed
        
        warnings = db.strikes.find({'guildid':ctx.guild_id, 'user':user.id, 'action':'Warn'})
        warns = []
        async for warn in warnings:
            if warn.type is None:
                warntype = 'Major'
            else:
                warntype = warn.type
            warns.append(f"**Type:** {warntype} | **Warning ID:** {warn.strikeid} | **Reason:** {warn.reason} | **Moderator:** {warn.moderator} | **Day:** {warn.day}\n\n")
        if warns == []:
            embed = Embed(description=f"There are no warnings for {user}.",
                        color=0xffcc50)
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
    
    @slash_command(name='strikes', description="shows you a users strike list",
        default_member_permissions=Permissions.MODERATE_MEMBERS
    )
    @user()
    async def strikes_list(self, ctx:InteractionContext, user:OptionType.USER=None):
        """/strikes
        Description:
            List all strikes for a user.
        
        Args:
            user: Specify that the user parameter is an optional parameter
        """
        await ctx.defer()
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
                color=0xffcc50)
            return embed
        
        all_strikes = db.strikes.find({'guildid':ctx.guild_id, 'user':user.id})
        allstrikes = []
        async for s in all_strikes:
            if s.action.lower() != 'warn':
                allstrikes.append(f"**Strike ID:** {s.strikeid} | **Action:** {s.action} | **Reason:** {s.reason} | **Moderator:** {s.moderator} | **Day:** {s.day}\n\n")
            else:
                if s.type is None:
                    warntype = 'Major'
                else:
                    warntype = s.type
                allstrikes.append(f"**Strike ID:** {s.strikeid} | **Action:** {warntype} {s.action} | **Reason:** {s.reason} | **Moderator:** {s.moderator} | **Day:** {s.day}\n\n")

        if allstrikes == []:
            embed = Embed(description=f"There are no strikes for {user}.",
                        color=0xffcc50)
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
    
    @slash_command('removeallstrikes', description='Remove all strikes from a member.')
    @member()
    async def strikesremoveall(self, ctx:InteractionContext, user: OptionType.USER):
        """/removeallstrikes
        Description:
            Remove all strikes from a user.
        
        Args:
            user: Specify the user that is being removed from the database
        """
        
        await ctx.defer()
        if ctx.author.id != 400713431423909889:
            await ctx.send("This command cannot be used.", ephemeral=True)
            return
        print(user.id)
        await db.strikes.find({'guildid':ctx.guild_id, 'user':user.id}).delete_many()
        await ctx.send(f'All strikes removed from {user}')
    
    @slash_command(name='strike', description="look at a strike info",
        default_member_permissions=Permissions.MODERATE_MEMBERS,
    )
    @warnid()
    async def strike_info(self, ctx:InteractionContext, warnid:str=None):
        """/strike
        Description:
            Display information about a specific strike.
        
        Args:
            warnid: WarnID
        """
        await ctx.defer()
        s = await db.strikes.find_one({'guildid':ctx.guild_id, 'strikeid':warnid})
        if s is None:
            return await ctx.send(f'Strike not found', ephemeral=True)
        if s.action.lower() != 'warn':
            info = f"**Strike ID:** {s.strikeid} | **Action:** {s.action} | **Reason:** {s.reason} | **Moderator:** {s.moderator} | **Day:** {s.day}"
        else:
            if s.type is None:
                warntype = 'Major'
            else:
                warntype = s.type
            info = f"**Strike ID:** {s.strikeid} | **Action:** {warntype} {s.action} | **Reason:** {s.reason} | **Moderator:** {s.moderator} | **Day:** {s.day}"
        embed = Embed(
            description=info,
            color=0xffcc50)
        await ctx.send(embed=embed)
    
    @slash_command(name='reason', description="allows me to modify reasons of strikes",
        default_member_permissions=Permissions.MODERATE_MEMBERS,
    )
    @warnid()
    @reason()
    async def strike_reason(self, ctx:InteractionContext, warnid:str=None, reason:str=None):
        """/reason
        Description:
            Allows a user to change the reason of a strike.
            This is useful if the original reason was not clear enough or if it was changed by mistake.
            The function takes in two arguments: ctx and warnid, with an optional third argument being reason.
            If no reason is provided, then the user will be prompted to provide one.
        
        Args:
            warnid: warnID
            reason: Set the reason for the strike
        """
        await ctx.defer()
        if reason is None:
            await ctx.send("You have to include a reason", ephemeral=True)
            return
        strike = await db.strikes.find_one({'guildid':ctx.guild_id, 'strikeid':warnid})
        if strike is None:
            return await ctx.send(f'Strike not found', ephemeral=True)
        if strike.user == ctx.author.id:
            await ctx.send("You can't change a reason on a strike directed at you", ephemeral=True)
            return
        embed = Embed(
            description=f"Strike reason changed from `{strike.reason}` to `{reason}`\n**Strike ID:** {strike.strikeid}\n**Action:** {strike.action}\n**User ID:** {strike.user} \n**Actioned by:** {ctx.author.mention}",
            color=0xffcc50)
        await ctx.send(embed=embed)
        strike.reason = reason
        await strike.save()
    
    @slash_command(name='limbo', sub_cmd_name='add', sub_cmd_description="[MOD]allows me to limbo users", scopes=[435038183231848449,149167686159564800],
        default_member_permissions=Permissions.BAN_MEMBERS
    )
    @user()
    @reason()
    async def limbo_add(self, ctx:InteractionContext, user:OptionType.USER=None, reason:str=None):
        await ctx.defer()
        if reason is None:
            await ctx.send('You have to include a reason', ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member is not None:
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
            
            limboed = await db.limbo.find_one({'guildid':ctx.guild_id, 'userid':member.id})
            if limboed is not None:
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
            await db.limbo(guildid=ctx.guild_id, userid=member.id, roles=ur, reason=reason).insert()
            for user_role in user_roles:
                await member.remove_role(user_role)
            await member.add_role(limborole)
            embed = Embed(description=f"{member.mention} put in limbo | {reason} \n**User ID:** {member.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0xffcc50)
            await ctx.send(embed=embed)
            while True:
                warnid = random_string_generator()
                warnid_db = await db.strikes.find_one({'guildid':ctx.guild_id, 'strikeid':warnid})
                if warnid_db is None:
                    break
                else:
                    continue
            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.strikes(strikeid=warnid, guildid=ctx.guild_id, user=member.id, moderator=ctx.author.id, action="Limbo", day=daytime, reason=reason).insert()
        else:
            raise UserNotFound()
    
    @slash_command(name='limbo', sub_cmd_name='remove', sub_cmd_description="[MOD]allows me to let users out of limbo", scopes=[435038183231848449,149167686159564800],
        default_member_permissions=Permissions.BAN_MEMBERS
    )
    @user()
    @reason()
    async def limbo_remove(self, ctx:InteractionContext, user:OptionType.USER=None, reason:str=None):
        await ctx.defer()
        if reason is None:
            await ctx.send('You have to include a reason', ephemeral=True)
            return
        member = find_member(ctx, user.id)
        if member is not None:
            
            limboed = await db.limbo.find_one({'guildid':ctx.guild_id, 'userid':member.id})
            if limboed is None:
                await ctx.send(f'{member.mention} is not in limbo', ephemeral=True)
                return

            limborole = [role for role in member.roles if role.name == 'Limbo']
            for limborole in limborole:
                limborole = limborole

            user_limbo_data = await db.limbo.find_one({"guildid":ctx.guild_id, "userid":member.id})
            roles = [ctx.guild.get_role(int(id_)) for id_ in user_limbo_data.roles.split(",") if len(id_)]
            for r in roles:
                await member.add_role(r)
            await member.remove_role(limborole)

            await user_limbo_data.delete()

            embed = Embed(description=f"{member.mention} let out of limbo | {reason} \n**User ID:** {member.id} \n**Actioned by:** {ctx.author.mention}",
                        color=0xffcc50)
            await ctx.send(embed=embed)
        else:
            raise UserNotFound
    
    # @listen()
    # async def on_message_create(self, event):
    #     message = event.message
    #     if message.guild.id == 149167686159564800:
    #         
    #         channel = await db.find_one(logs, {'guild_id':message.guild.id})
    #         if channel is not None:
    #             log_channel = message.guild.get_channel(int(channel.channel_id))

    #             if message.channel.id == 736680179253903491:
    #                 embed = Embed(title="Limbo log", timestamp=datetime.utcnow(), color=0xffcc50)
    #                 embed.set_thumbnail(url=f'{message.author.avatar.url}')
    #                 embed.add_field(name=f"{message.author}", value=f"{message.content}", inline=False)
    #                 embed.set_footer(text=f'User ID: {message.author.id}')
    #                 await log_channel.send(embed=embed)

    from interactions.models.internal.tasks import Task
    from interactions.models.internal.tasks.triggers import IntervalTrigger

    @Task.create(IntervalTrigger(seconds=60))
    async def unban_task(self):
        endtimes = db.tempbans.find({'endtime':{'$lte':datetime.now()}})
        async for m in endtimes:
            if m is not None:
                guild = self.bot.get_guild(m.guildid)
                if guild is None:
                    if self.bot.user.id != 785122198247178260:
                        print(f"[automod]|[unban_task]{m.guildid} not found in the guild list")
                        await m.delete()
                        return
                elif guild is not None:
                    banned = await guild.fetch_ban(m.user)
                    if banned is None:
                        print(f"[automod]|[unban_task]{m.user} not found in the ban list")
                        await m.delete()
                        return
                    await guild.unban(m.user, '[automod]|[unban_task] ban time expired')
                    await m.delete()

def setup(bot):
    Moderation(bot)