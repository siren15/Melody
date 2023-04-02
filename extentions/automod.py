import asyncio
import json
import math
import random
import requests

from interactions.client.const import MISSING
from rapidfuzz import fuzz, process
from dateutil.relativedelta import *
from datetime import datetime, timedelta
from interactions import Client, Extension, StringSelectMenu, StringSelectOption, listen, Embed, Permissions, InteractionContext, OptionType, ModalContext, SlashCommand, InputText, TextStyles, Modal
from interactions.models.discord.base import DiscordObject
from extentions.touk import BeanieDocuments as db, violation_settings
from utils.slash_options import *
from utils.customchecks import *
from interactions.api.events.discord import MemberUpdate, MemberAdd, MessageCreate, AutoModExec
from interactions.client.errors import  HTTPException

def geturl(string):
    url = re.compile(r"(?:https?:\/\/(?:www\.)?)?(?P<domain>[-a-z0-9@:%._\+~#=]{1,256}\.[a-z0-9()]{1,6})\b(?:[-a-z0-9()@:%_\+.~#?&//=]*)",flags=re.IGNORECASE,)
    url = url.findall(string)
    if url != []:
        return url
    return None

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

def get_num(self):
    """Get a number from string."""
    num = [int(i) for i in self.lower().split() if i.isdigit()]
    if num != []:
        for n in num:
            return int(n)
    return None

w = ['w', 'week', 'weeks']
d = ['d', 'day', 'days']
h = ['h', 'hour', 'hours']
m = ['m', 'min', 'minute', 'minutes']
s = ['s', 'sec', 'second', 'seconds']

async def bm_time_to_sec(self, bmtime):
    if bmtime == '':
        return None
    ban_time = [int(i) for i in bmtime.lower().split() if i.isdigit()]
    if ban_time == []:
        embed = Embed(description=f":x: Ban/Mute time formatting not correct. Try again. \n\n[Examples: `10 S`, `10 M`, `10 H`, `10 D`]",
                        color=0xDD2222)
        await self.send(embed=embed, ephemeral=True)
        return None
    else:
        for num in ban_time:
            time = num
        ban_time_type = [str(t) for t in bmtime.lower().split() if not t.isdigit()]
        for time_type in ban_time_type:
            time_type = time_type

    if time_type in d:
        seconds = time * 86400

    elif time_type in h:
        seconds = time * 3600

    elif time_type in m:
        seconds = time * 60

    elif time_type in s:
        seconds = time
    
    else:
        embed = Embed(description=f":x: Time type not supported. You can use: {d}, {h}, {m}, {s}",
                    color=0xDD2222)
        await self.send(embed=embed, ephemeral=True)
        return None
    if (seconds < 3600) or (seconds > 94672800):
        await self.send("Ban time can't be shorter than 1 hour and longer than 3 years and mute time can't be shorter than 10 seconds and longer than 28 days.", ephemeral=True)
        return None
    return seconds

async def automod_warn(self, log_channel, reason):
    """
    Warns the user when used.
    """
    message = self.message
    user = message.author
    guild = self.message.guild
    while True:
        warnid = random_string_generator()
        warnid_db = await db.strikes.find_one({'guildid':guild.id, 'strikeid':warnid})
        if warnid_db is None:
            break
        else:
            continue
    warnings = db.strikes.find({'guildid':guild.id, 'user':user.id, 'action':{'$regex':'^warn$', '$options':'i'}})
    warncount = []
    async for warn in warnings:
        warncount.append(warn.strikeid)
    if warncount == []:
        warnrolename = 'Warning-1'
    else:
        warnrolename = f'Warning-{len(warncount)+1}'
    
    warn_role = [role for role in guild.roles if role.name == warnrolename]
    if warn_role == []:
        role = await guild.create_role(name=warnrolename, reason='[automod]|[warn]created new warnrole as warnrole with this number did not exist yet')
    else:
        for role in warn_role:
            role = role
    
    await user.add_role(role, reason)

    daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
    await db.strikes(strikeid=warnid, guildid=guild.id, user=user.id, moderator=self.bot.user.id, action="Warn", day=daytime, reason=reason).insert()
    
    try:
        embed = Embed(description=f":grey_exclamation: **[AUTOMOD]You have been warned in {guild.name} for:** {reason}",
                color=0xffcc50)
        await user.send(embed=embed)
    except HTTPException:
        embed = Embed(description=f"Couldn't dm {user.mention}, warn logged and user was given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** [AUTOMOD]{self.bot.user}",
                color=0xffcc50)
        await log_channel.send(embed=embed)
        return
    else:
        embed = Embed(description=f"{user.mention} warned and given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** [AUTOMOD]{self.bot.user}",
                    color=0xffcc50)
        await log_channel.send(embed=embed)

async def automod_mute(self, settings, reason):
    """
    Mutes the user when used.
    """
    user = self.message.author
    
    if settings.mute_time is not None:
        time = settings.mute_time
    else:
        time = 3600
    endtime = datetime.now() + timedelta(seconds=int(time))
    await user.timeout(endtime, reason)

async def automod_ban(self, settings, log_channel, reason):
    """
    Bans the user when used.
    """
    message = self.message
    user = message.author
    guild = self.message.guild
    
    banned = await guild.fetch_ban(user)
    if banned is None:
        if settings.ban_time is not None:
            tempbanned = await db.tempbans.find_one({"user":user.id, "guildid":guild.id})
            if tempbanned is not None:
                await tempbanned.delete()
            time = settings.ban_time
            endtime = datetime.now() + timedelta(seconds=int(time))
            await db.tempbans(guildid=guild.id, user=user.id, starttime=datetime.now(), endtime=endtime, banreason=reason).insert()
            embed = Embed(description=f"{user} **was temporarily banned** | {reason} \n**User ID:** {user.id} \n**Actioned by:** [AUTOMOD]{self.bot.user}\n**End time:**<t:{math.ceil(endtime.timestamp())}:R>",
                            color=0xffcc50,
                            timestamp=datetime.utcnow())
            embed.set_thumbnail(url=user.avatar.url)
            await log_channel.send(embed=embed)
        await guild.ban(DiscordObject(id=int(user.id), client=self.bot), reason=reason, delete_message_days=0)

async def automod_strike(self, event, action_msg, reason):
    message = event.message
    user = message.author
    guild = event.message.guild
    while True:
        avid = random_string_generator()
        strikes_db = await db.strikes.find_one({'guildid':guild.id, 'strikeid':avid})
        if strikes_db is None:
            break
        else:
            continue
    daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
    await db.strikes(strikeid=avid, guildid=guild.id, user=user.id, moderator=self.bot.user.id, action=action_msg, day=daytime, reason=reason, automod=True).insert()

class AutoMod(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
        self.phishing_links = list()
        plinks = requests.get('https://raw.githubusercontent.com/Discord-AntiScam/scam-links/main/urls.json')
        for link in json.loads(plinks.text):
            self.phishing_links.append(link)

    @listen()
    async def discord_automod_log(self, event: AutoModExec):
        if event.execution.action.type == 1:
            trigger_type = event.execution.rule_trigger_type
            content = event.execution.content
            guild = event.guild
            if trigger_type == 1:
                trigger = "BANNED WORD"
                reason = f"Message contains a banned word set by this community: {content}"
            elif trigger_type == 3:
                trigger = "SPAM"
                reason = f"Message contains spam: {content}"
            elif trigger_type == 4:
                trigger = "DISCORD BANNED WORD"
                reason = f"Message contains a banned word set by discord: {content}"
            elif trigger_type == 5:
                trigger = "MENTION SPAM"
                reason = f"Message exceeds the mention limit set by this community"
            audit_log_entry = await guild.fetch_audit_log(action_type=143, limit=1)
            for user in audit_log_entry.users:
                while True:
                    avid = random_string_generator()
                    strikes_db = await db.strikes.find_one({'guildid':guild.id, 'strikeid':avid})
                    if strikes_db is None:
                        break
                    else:
                        continue
                daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
                await db.strikes(strikeid=avid, guildid=guild.id, user=user.id, moderator=self.bot.user.id, action=f"Automod Message Block ({trigger})", day=daytime, reason=reason, automod=True).insert()

                settings = await db.amConfig.find_one({'guild':guild.id})
                channelid = await db.logs.find_one({"guild_id":guild.id})
                log_channel = guild.get_channel(channelid.channel_id)

                violation_entries = []
                async for entry in db.strikes.find({'guildid':guild.id, 'user':user.id, 'action':f"Automod Message Block ({trigger})", 'automod':True}):
                    violation_entries.append(entry.user)
                if settings.phishing.violation_count is not None:
                    if len(violation_entries) > settings.phishing.violation_count:
                        
                        warnreason = f"{reason}. You've done this {len(violation_entries)} times, which exceeds our violations limit for {trigger} of {settings.phishing.violation_count}"

                        if 'warn' in settings.phishing.violation_punishment:
                            await automod_warn(event, log_channel, warnreason)
                        
                        if 'mute' in settings.phishing.violation_punishment:
                            await automod_mute(event, settings, warnreason)
                            
                        if 'kick' in settings.phishing.violation_punishment:
                            await guild.kick(user, warnreason)
                
                        if 'ban' in settings.phishing.violation_punishment:
                            await automod_ban(event, settings, warnreason)
    @listen()
    async def phishing_links_filter(self, event: MessageCreate):
        message = event.message
        user = message.author
        member = user
        guild = event.message.guild
        channel = message.channel
        if user.bot:
            return
        reason = f'[AUTOMOD]phishing link sent in {channel.name}'
        if await is_automod_event_active(guild, 'phishing_filter'):
            settings = await db.amConfig.find_one({'guild':guild.id})
            if settings.ignored_users is not None:
                if member.id in settings.ignored_users:
                    return
            if settings.ignored_roles is not None:
                if any(role for role in member.roles if role.id in settings.ignored_roles):
                    return
            if member.has_permission(Permissions.ADMINISTRATOR) == True:
                return
            if settings.ignored_channels is not None:
                if channel.id in settings.ignored_channels:
                    return
            urls = geturl(message.content)
            if urls is not None:
                for url in urls:
                    for link in self.phishing_links:
                        if link == url:
                            await message.delete()
                            await channel.send(f"Hey {user.mention}! That link is banned here!", delete_after=3)
                
                            await automod_strike(self, event, "Automod Log (Phishing Links)", reason)
                                    
                            channelid = await db.logs.find_one({"guild_id":guild.id})
                            log_channel = guild.get_channel(channelid.channel_id)
                            
                            violation_entries = []
                            async for entry in db.strikes.find({'guildid':guild.id, 'user':user.id, 'action':"Automod Log (Phishing Links)", 'automod':True}):
                                violation_entries.append(entry.user)
                            if settings.phishing.violation_count is not None:
                                if len(violation_entries) > settings.phishing.violation_count:
                                    if 'warn' in settings.phishing.violation_punishment:
                                        await automod_warn(event, log_channel, reason)
                                    
                                    if 'mute' in settings.phishing.violation_punishment:
                                        await automod_mute(event, settings, reason)
                                        
                                    if 'kick' in settings.phishing.violation_punishment:
                                        await guild.kick(user, reason)
                            
                                    if 'ban' in settings.phishing.violation_punishment:
                                        await automod_ban(event, settings, reason)
    
    psc = SlashCommand(name = 'phishing_links', description="Configure Melodys phishing links automod.", default_member_permissions=Permissions.ADMINISTRATOR)
    
    @psc.subcommand('violation_count', sub_cmd_description='How many violations before punishment.')
    @slash_option('violations_count', 'Must be between 0-10.', OptionType.INTEGER)
    async def phishing_links_violation_count(self, ctx: InteractionContext, violations_count:int=0):
        """
        /phishing_links violation_count
        Description:
            Configure how many violations are needed before Melody gives out a punishment.

        Args:
            violations_count: Must be between 0-10
        """
        # violations_count = get_num(violations_count)
        if (int(violations_count) > 10) or (int(violations_count) < 0):
            await ctx.send(f"{violations_count} is not a valid violation count. Violation count has to be between 0-10.")
        if violations_count is None:
            violations_count = 0
        settings = await db.automod_config.find_one({"guildid":ctx.guild_id})
        settings.phishing.violation_count = int(violations_count)
        await settings.save()
        await ctx.send(f'Violation count set to: {violations_count}')
    
    @psc.subcommand('punishments', sub_cmd_description='What punishments to use?')
    async def phishing_links_punishments(self, ctx: InteractionContext):
        """
        /phishing_links punishments
        Description:
            Configure what punishments will Melody give out.
        Usage:
            There are no parameters in this command, you just have to use it, and it will send you a configuration selection menu. Selections are automatically saved. Config time limit is 2 minutes.
        """
        settings = await db.amConfig.find_one({'guildid':ctx.guild_id})
        if settings.phishing.violation_punishment is None:
            events_log_list = ''
        else:
            events_log_list = settings.phishing.violation_punishment

        if 'warn' in events_log_list:
            warn_status = True
        else:
            warn_status = False

        if 'mute' in events_log_list:
            mute_status = True
        else:
            mute_status = False

        if 'kick' in events_log_list:
            kick_status = True
        else:
            kick_status = False

        if 'ban' in events_log_list:
            ban_status = True
        else:
            ban_status = False
        
        select_options = [
            StringSelectOption(label="Warn", value="warn", default=warn_status),
            StringSelectOption(label="Mute", value="mute", default=mute_status),
            StringSelectOption(label="Kick", value="kick", default=kick_status),
            StringSelectOption(label="Ban", value="ban", default=ban_status)
        ]

        select_menu = StringSelectMenu(select_options, min_values=0, max_values=2)

        message = await ctx.send('Configure to what automod reacts to:', components=select_menu)

        while True:
            try:
                select = await self.bot.wait_for_component(components=select_menu, timeout=120)
            except asyncio.TimeoutError:
                await message.edit('Config closed due to 2 minutes of inactivity.', components=[])
            else:
                values = ','.join(select.ctx.values)
                settings.phishing.violation_punishment = values
                await settings.save()

    @listen()
    async def onNameChange_banned_name_exact(self, event: MemberUpdate):
        member =  event.after
        if await is_automod_event_active(event.guild, 'banned_names'):
            old_name =  event.before.display_name
            new_name = event.after.display_name
            if old_name != new_name:
                settings = await db.amConfig.find_one({'guild':event.guild.id})
                if settings.ignored_users is not None:
                    if member.id in settings.ignored_users:
                        return
                if settings.ignored_roles is not None:
                    if any(role for role in member.roles if role.id in settings.ignored_roles):
                        return
                if member.has_permission(Permissions.ADMINISTRATOR) == True:
                    return
                bn = await db.bannedNames.find_one({'guild':event.guild.id})
                if bn is None:
                    await db.bannedNames(guild=event.guild.id).insert()
                banned_names = bn.names
                new_name_result = process.extract(new_name, banned_names, scorer=fuzz.token_sort_ratio, limit=1)
                names = [t[0] for t in new_name_result if t[1] >= 90]
                username_result = process.extract(member.username, banned_names, scorer=fuzz.token_sort_ratio, limit=1)
                usernames = [t[0] for t in username_result if t[1] >= 90]
                if names != []:
                    name = ' '.join(names)
                    reason = f'Automod detected a banned name {name} in {new_name} for {member}({member.id})'
                    if usernames == []:
                        await member.edit_nickname(member.username, reason)
                    else:
                        await member.edit_nickname(bn.default_name, reason)
                    embed = Embed(description=reason,
                                            color=0xffcc50)
                    embed.set_thumbnail(url=member.avatar.url)
                    embed.add_field(name="Old Name", value=old_name)
                    embed.add_field(name="New Name", value=new_name)
                    
                    channelid = await db.logs.find_one({"guild_id":member.guild.id})
                    log_channel = member.guild.get_channel(channelid.channel_id)
                    try:
                        await member.send(f"Your name or part of your name were flagged in banned names in `{event.guild.name}` server.\nI've flagged `{name}` in `{new_name}`")
                        await log_channel.send(f'I DMed {member}', embed=embed)
                    except Exception:
                        await log_channel.send(f"Couldn't DM {member}", embed=embed)
                    
                    violation_count = await db.strikes.find({'guildid':event.guild.id, 'user':member.id, 'action':"Automod Log (Banned Name)", 'automod':True}).count()
                    if settings.banned_names.violation_count is not None:
                        if violation_count > settings.banned_names.violation_count:
                            if 'warn' in settings.banned_names.violation_punishment:
                                await automod_warn(event, log_channel, reason)
                            
                            if 'mute' in settings.banned_names.violation_punishment:
                                await automod_mute(event, settings, reason)
                                
                            if 'kick' in settings.banned_names.violation_punishment:
                                await event.guild.kick(member, reason)
                    
                            if 'ban' in settings.banned_names.violation_punishment:
                                await automod_ban(event, settings, reason)
    
    @listen()
    async def onMemAdd_banned_name_exact(self, event: MemberAdd):
        member =  event.member
        if await is_automod_event_active(event.guild, 'banned_names'):
            new_name = member.display_name
            settings = await db.amConfig.find_one({'guild':event.guild.id})
            if settings.ignored_users is not None:
                if member.id in settings.ignored_users:
                    return
            if settings.ignored_roles is not None:
                if any(role for role in member.roles if role.id in settings.ignored_roles):
                    return
            if member.has_permission(Permissions.ADMINISTRATOR) == True:
                return
            bn = await db.bannedNames.find_one({'guild':event.guild.id})
            if bn is None:
                await db.bannedNames(guild=event.guild.id).insert()
            banned_names = bn.names
            new_name_result = process.extract(new_name, banned_names, scorer=fuzz.token_sort_ratio, limit=1)
            names = [t[0] for t in new_name_result if t[1] >= 90]
            if names != []:
                name = ' '.join(names)
                reason = f'Automod detected a banned name {name} in {new_name} for {member}({member.id})'
                await member.edit_nickname(bn.default_name, reason)
                embed = Embed(description=reason,
                                        color=0xffcc50)
                embed.set_thumbnail(url=member.avatar.url)
                
                channelid = await db.logs.find_one({"guild_id":member.guild.id})
                log_channel = member.guild.get_channel(channelid.channel_id)
                try:
                    await member.send(f"Your name or part of your name were flagged in banned names in `{event.guild.name}` server.\nI've flagged `{name}` in `{new_name}`")
                    await log_channel.send(f'I DMed {member}', embed=embed)
                except Exception:
                    await log_channel.send(f"Couldn't DM {member}", embed=embed)
                
                violation_count = await db.strikes.find({'guildid':event.guild.id, 'user':member.id, 'action':"Automod Log (Banned Name)", 'automod':True}).count()
                if settings.banned_names.violation_count is not None:
                    if violation_count > settings.banned_names.violation_count:
                        if 'warn' in settings.banned_names.violation_punishment:
                            await automod_warn(event, log_channel, reason)
                        
                        if 'mute' in settings.banned_names.violation_punishment:
                            await automod_mute(event, settings, reason)
                            
                        if 'kick' in settings.banned_names.violation_punishment:
                            await event.guild.kick(member, reason)
                
                        if 'ban' in settings.banned_names.violation_punishment:
                            await automod_ban(event, settings, reason)
    
    BannedNames = SlashCommand(name='banned_names', default_member_permissions=Permissions.ADMINISTRATOR, description='Manage banned names.')

    @BannedNames.subcommand('manage')
    async def banned_names_manage(self, ctx:InteractionContext):
        """
        /banned_names manage
        Description:
            Manage banned names.
        Usage:
            Use the command to get a muodal menu for configuration. Config will be saved on modal submit. Config time limit is 10 minutes.
        """
        bn = await db.bannedNames.find_one({'guild':ctx.guild.id})
        settings = await db.amConfig.find_one({"guild":ctx.guild_id})
        if settings.banned_names.violation_count is None:
            bw_vc_pf = MISSING
        else:
            bw_vc_pf = settings.banned_names.violation_count

        if bn is None:
            exact_prefill = MISSING
            defname_prefill = MISSING
        else:
            if bn.names is None:
                exact_prefill = MISSING
            else:
                exact_prefill = ','.join(bn.names)
            if bn.default_name is None:
                defname_prefill = MISSING
            else:
                defname_prefill = bn.default_name
        m = Modal(title='Configure the automatic moderation', components=[
            InputText(
                label="Banned Names",
                style=TextStyles.PARAGRAPH,
                custom_id=f'exact_match',
                placeholder='Words, seperated by a comma(,). They should have minimum 3 characters.',
                value=exact_prefill,
                required=False
            ),
            InputText(
                label="Fallback Name",
                style=TextStyles.SHORT,
                custom_id=f'defname',
                placeholder="One name that will be act as a fallback",
                value=defname_prefill,
                required=True,
                max_length=32,
                min_length=2
            ),
            InputText(
                label="Violation Count",
                style=TextStyles.SHORT,
                custom_id=f'bw_vc',
                placeholder="Must be between 0-10.",
                value=bw_vc_pf,
                required=False
            )
        ],custom_id=f'{ctx.author.id}_automod_config_modal')
    
        await ctx.send_modal(modal=m)
        try:
            modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
        except asyncio.TimeoutError:
            return await modal_recived.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond to this ", ephemeral=True)
        
        em_words = modal_recived.responses.get('exact_match')
        defName = modal_recived.responses.get('defname')
        
        bw_vc_response = modal_recived.responses.get('bw_vc')
        if (bw_vc_response == '') or (bw_vc_response is None):
            bw_vc_response = None
        elif (get_num(bw_vc_response) > 10) or (get_num(bw_vc_response) < 0):
            await modal_recived.send(f"{bw_vc_response} is not a valid violation count. Violation count has to be between 0-10.")
        
        settings.banned_names.violation_count = get_num(bw_vc_response)
        await settings.save()

        if bn is None:
            await db.bannedNames(guild=ctx.guild_id, names=em_words.split(','), default_name=defName).insert()
        else:
            bn.default_name = defName
            bn.names = em_words.split(',')
            await bn.save()
        
        embed=Embed(color=0xffcc50,
        description=f'**Current banned names:**\n{em_words}\n**Violation count:** {bw_vc_response}')
        await modal_recived.send(embed=embed)
    
    @BannedNames.subcommand('punishments', sub_cmd_description='What punishments to use?')
    async def banned_names_punishments(self, ctx: InteractionContext):
        """
        /banned_names punishments
        Description:
            Configure what punishments will Melody give out.
        Usage:
            There are no parameters in this command, you just have to use it, and it will send you a configuration selection menu. Selections are automatically saved. Config time limit is 2 minutes.
        """
        settings = await db.amConfig.find_one({'guildid':ctx.guild_id})
        if settings.banned_names.violation_punishment is None:
            events_log_list = ''
        else:
            events_log_list = settings.banned_names.violation_punishment

        if 'warn' in events_log_list:
            warn_status = True
        else:
            warn_status = False

        if 'mute' in events_log_list:
            mute_status = True
        else:
            mute_status = False

        if 'kick' in events_log_list:
            kick_status = True
        else:
            kick_status = False

        if 'ban' in events_log_list:
            ban_status = True
        else:
            ban_status = False
        
        select_options = [
            StringSelectOption(label="Warn", value="warn", default=warn_status),
            StringSelectOption(label="Mute", value="mute", default=mute_status),
            StringSelectOption(label="Kick", value="kick", default=kick_status),
            StringSelectOption(label="Ban", value="ban", default=ban_status)
        ]

        select_menu = StringSelectMenu(select_options, min_values=0, max_values=2)

        message = await ctx.send('Configure to what automod reacts to:', components=select_menu)

        while True:
            try:
                select = await self.bot.wait_for_component(components=select_menu, timeout=120)
            except asyncio.TimeoutError:
                await message.edit('Config closed due to 2 minutes of inactivity.', components=[])
            else:
                values = ','.join(select.ctx.values)
                settings.banned_names.violation_punishment = values
                await settings.save()
    
    AutoModSettings = SlashCommand(name='automod', default_member_permissions=Permissions.ADMINISTRATOR, description='Manage the automod.')

    @AutoModSettings.subcommand(sub_cmd_name='listen_to_events', sub_cmd_description='Activate parts of the automod')
    async def automod_events(self, ctx: InteractionContext):
        """
        /automod listen_to_events
        Description:
            Configure what AutoMod events will Melody listen to in the server.
        Usage:
            There are no parameters in this command, you just have to use it, and it will send you a configuration selection menu. Selections are automatically saved. Config time limit is 2 minutes.
        """
        await ctx.defer(ephemeral=True)
        events = await db.amConfig.find_one({'guildid':ctx.guild_id})
        if events.active_events is None:
            events_log_list = []
        else:
            events_log_list = events.active_events
        if 'banned_names' in events_log_list:
            bn_status = True
        else:
            bn_status = False

        if 'phishing_filter' in events_log_list:
            pf_status = True
        else:
            pf_status = False
        
        select_options = [
            StringSelectOption(label="Banned Names", value="banned_names", default=bn_status),
            StringSelectOption(label="phishing_filter", value="phishing_filter", default=pf_status),
        ]

        select_menu = StringSelectMenu(select_options, min_values=0, max_values=2)

        message = await ctx.send('Configure to what automod reacts to:', components=select_menu)

        while True:
            try:
                select = await self.bot.wait_for_component(components=select_menu, timeout=120)
            except asyncio.TimeoutError:
                await message.edit('Config closed due to 2 minutes of inactivity.', components=[])
            else:
                events.active_events = select.ctx.values
                await events.save()

    @AutoModSettings.subcommand(sub_cmd_name='ban_mute_times', sub_cmd_description='Define a ban and mute times.')
    @slash_option(name="bantime", description="tempban time, examples: 10 S, 10 M, 10 H, 10 D", opt_type=OptionType.INTEGER, required=False)
    @slash_option(name="mutetime", description="mute time, examples: 10 S, 10 M, 10 H, 10 D", opt_type=OptionType.INTEGER, required=False)
    async def automod_ban_mute_times(self, ctx:InteractionContext, bantime:int=0, mutetime:int=0):
        """
        /automod ban_mute_times
        Description:
            Configure the temp ban and mute times Melody will use in automod.

        Args:
            bantime (int, optional): tempban time, examples: 10 S, 10 M, 10 H, 10 D" Defaults to 0.
            mutetime (int, optional): mute time, examples: 10 S, 10 M, 10 H, 10 D Defaults to 0.
        """
        if bantime is not None:
            bt = await bm_time_to_sec(ctx, bantime)
        else:
            bt = bantime
        if mutetime is not None:
            mt = await bm_time_to_sec(ctx, mutetime)
        else:
            mt = mutetime
        settings = await db.automod_config.find_one({"guildid":ctx.guild_id})
        settings.ban_time = bt
        settings.mute_time = mt
        await settings.save()
        await ctx.send(f'Ban time: {bantime}\nMute time: {mutetime}')

    @AutoModSettings.subcommand('ignored_channel', 'add', 'Add a channel to ignored channels.')
    @channel()
    async def AutomodAddIgnoredChannels(self, ctx:InteractionContext, channel: OptionType.CHANNEL=None):
        """
        /automod ignored_channel add
        Description:
            Add a channel to channels ignored by AutoMod.

        Args:
            channel (OptionType.CHANNEL, optional): The channel you want to add. Defaults to channel you're executing the command from.
        """
        await ctx.defer(ephemeral=True)
        if channel is None:
            channel = ctx.channel
        settings = await db.amConfig.find_one({"guild":ctx.guild.id})
        if settings is None:
            await db.amConfig(guild=ctx.guild.id, phishing=violation_settings, banned_words=violation_settings, banned_names=violation_settings).insert()
        ignored_channels = settings.ignored_channels
        if ignored_channels is None:
            ignored_channels = list()
        if channel.id in ignored_channels:
            await ctx.send(f'{channel.mention} is already ignored.', ephemeral=True)
        ignored_channels.append(channel.id)
        await settings.save()
        channel_mentions = [ctx.guild.get_channel(id) for id in ignored_channels]
        channel_mentions = [ch.mention for ch in channel_mentions if ch is not None]
        channel_mentions = ' '.join(channel_mentions)
        embed = Embed(description=f"Channel {channel.mention} set to be ignored.")
        embed.add_field('Ignored Channels', channel_mentions)
        await ctx.send(embed=embed, ephemeral=True)

    @AutoModSettings.subcommand('ignored_channel', 'remove', 'Remove a channel from ignored channels.')
    @channel()
    async def AutomodRemoveIgnoredChannels(self, ctx:InteractionContext, channel: OptionType.CHANNEL=None):
        """
        /automod ignored_channel remove
        Description:
            Remove a channel from channels ignored by AutoMod.

        Args:
            channel (OptionType.CHANNEL, optional): The channel you want to remove. Defaults to channel you're executing the command from.
        """
        await ctx.defer(ephemeral=True)
        if channel is None:
            channel = ctx.channel
        settings = await db.amConfig.find_one({"guild":ctx.guild.id})
        if settings is None:
            await db.amConfig(guild=ctx.guild.id, phishing=violation_settings, banned_words=violation_settings, banned_names=violation_settings).insert()
        ignored_channels = settings.ignored_channels
        if ignored_channels is None:
            ignored_channels = list()
        if channel.id not in ignored_channels:
            await ctx.send(f'{channel.mention} is not being ignored by automod.', ephemeral=True)
        ignored_channels.remove(channel.id)
        await settings.save()
        channel_mentions = [ctx.guild.get_channel(id) for id in ignored_channels]
        channel_mentions = [ch.mention for ch in channel_mentions if ch is not None]
        channel_mentions = ' '.join(channel_mentions)
        embed = Embed(description=f"Channel {channel.mention} removed from ignored channels.")
        embed.add_field('Ignored Channels', channel_mentions)
        await ctx.send(embed=embed, ephemeral=True)
    
    @AutoModSettings.subcommand('ignored_role', 'add', 'Make a role to be ignored by automod.')
    @role()
    async def AutomodAddIgnoredRoles(self, ctx:InteractionContext, role: OptionType.ROLE):
        """
        /automod ignored_role add
        Description:
            Add a role to roles ignored by AutoMod.

        Args:
            role (OptionType.ROLE): The role you want to add.
        """
        await ctx.defer(ephemeral=True)
        settings = await db.amConfig.find_one({"guild":ctx.guild.id})
        if settings is None:
            await db.amConfig(guild=ctx.guild.id, phishing=violation_settings, banned_words=violation_settings, banned_names=violation_settings).insert()
        ignored_roles = settings.ignored_roles
        if ignored_roles is None:
            ignored_roles = list()
        if role.id in ignored_roles:
            await ctx.send(f'{role.mention} is already ignored.', ephemeral=True)
        ignored_roles.append(role.id)
        await settings.save()
        role_mentions = [ctx.guild.get_role(id) for id in ignored_roles]
        role_mentions = [r.mention for r in role_mentions if r is not None]
        role_mentions = ' '.join(role_mentions)
        embed = Embed(description=f"Role {role.mention} was added to roles ignored by automod.")
        embed.add_field('Ignored Roles', role_mentions)
        await ctx.send(embed=embed, ephemeral=True)

    @AutoModSettings.subcommand('ignored_role', 'remove', 'Remove a role from ignored roles.')
    @role()
    async def AutomodRemoveIgnoredRoles(self, ctx:InteractionContext, role: OptionType.ROLE):
        """
        /automod ignored_role remove
        Description:
            Remove a role from roles ignored by AutoMod.

        Args:
            role (OptionType.ROLE): The role you want to remove.
        """
        await ctx.defer(ephemeral=True)
        settings = await db.amConfig.find_one({"guild":ctx.guild.id})
        if settings is None:
            await db.amConfig(guild=ctx.guild.id, phishing=violation_settings, banned_words=violation_settings, banned_names=violation_settings).insert()
        ignored_roles = settings.ignored_roles
        if ignored_roles is None:
            ignored_roles = list()
        if role.id not in ignored_roles:
            await ctx.send(f'{role.mention} is not being ignored by automod.', ephemeral=True)
        ignored_roles.remove(role.id)
        await settings.save()
        role_mentions = [ctx.guild.get_role(id) for id in ignored_roles]
        role_mentions = [r.mention for r in role_mentions if r is not None]
        role_mentions = ' '.join(role_mentions)
        embed = Embed(description=f"Role {role.mention} was removed from roles ignored by automod.")
        embed.add_field('Ignored Roles', role_mentions)
        await ctx.send(embed=embed, ephemeral=True)
    
    @AutoModSettings.subcommand('ignored_member', 'add', 'Make a member to be ignored by automod.')
    @user()
    async def AutomodAddIgnoredMember(self, ctx:InteractionContext, user: OptionType.USER):
        """
        /automod ignored_member add
        Description:
            Add a member to members ignored by AutoMod.

        Args:
            user (OptionType.USER): member to be ignored by automod
        """
        await ctx.defer(ephemeral=True)
        settings = await db.amConfig.find_one({"guild":ctx.guild.id})
        if settings is None:
            await db.amConfig(guild=ctx.guild.id, phishing=violation_settings, banned_words=violation_settings, banned_names=violation_settings).insert()
        ignored_users = settings.ignored_users
        if ignored_users is None:
            ignored_users = list()
        if user.id in ignored_users:
            await ctx.send(f'{user}|{user.id} is already ignored.', ephemeral=True)
        ignored_users.append(user.id)
        await settings.save()
        users = [ctx.guild.get_member(id) for id in ignored_users]
        users = [f'{r}({r.id})' for r in users if r is not None]
        users = ' '.join(users)
        embed = Embed(description=f"Member {user}({user.id}) was added to members ignored by automod.")
        embed.add_field('Ignored Members', users)
        await ctx.send(embed=embed, ephemeral=True)

    @AutoModSettings.subcommand('ignored_member', 'remove', 'Remove a member from ignored members.')
    @user()
    async def AutomodRemoveIgnoredMember(self, ctx:InteractionContext, user: OptionType.USER):
        """
        /automod ignored_member remove
        Description:
            Remove a member from members ignored by AutoMod.

        Args:
            user (OptionType.USER): member to be removed from ignored members by automod
        """
        await ctx.defer(ephemeral=True)
        settings = await db.amConfig.find_one({"guild":ctx.guild.id})
        if settings is None:
           await db.amConfig(guild=ctx.guild.id, phishing=violation_settings, banned_words=violation_settings, banned_names=violation_settings).insert()
        ignored_users = settings.ignored_users
        if ignored_users is None:
            ignored_users = list()
        if user.id not in ignored_users:
            await ctx.send(f'{user}|{user.id} is not being ignored by automod.', ephemeral=True)
        ignored_users.remove(user.id)
        await settings.save()
        users = [ctx.guild.get_member(id) for id in ignored_users]
        users = [f'{r}({r.id})' for r in users if r is not None]
        users = ' '.join(users)
        embed = Embed(description=f"Member {user}({user.id}) was removed from members ignored by automod.")
        embed.add_field('Ignored Members', users)
        await ctx.send(embed=embed, ephemeral=True)

def setup(bot):
    AutoMod(bot)