import asyncio
import json
import math
import random
import requests

from naff.client.const import MISSING
from naff.models.discord import modal
from rapidfuzz import fuzz, process
from dateutil.relativedelta import *
from datetime import date, datetime, timedelta
from naff import Client, Extension, listen, Embed, Permissions, slash_command, InteractionContext,  OptionTypes, check, ModalContext, SlashCommandChoice
from naff.ext.paginators import Paginator
from naff.models.discord.base import DiscordObject
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *
from naff.api.events.discord import MemberRemove, MessageDelete, MemberUpdate, BanCreate, BanRemove, MemberAdd, MessageCreate
from naff.client.errors import NotFound, BadRequest, HTTPException

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
        embed = Embed(description=f":grey_exclamation: **You have been warned in {guild.name} for:** {reason}",
                color=0x0c73d3)
        await user.send(embed=embed)
    except HTTPException:
        embed = Embed(description=f"Couldn't dm {user.mention}, warn logged and user was given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** [AUTOMOD]{self.bot.user}",
                color=0x0c73d3)
        await log_channel.send(embed=embed)
        return
    else:
        embed = Embed(description=f"{user.mention} warned and given {role.mention} | {reason} \n**User ID:** {user.id} \n**Actioned by:** [AUTOMOD]{self.bot.user}",
                    color=0x0c73d3)
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
                            color=0x0c73d3,
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

    @slash_command(name='settings', sub_cmd_name='automod', sub_cmd_description="[ADMIN]Configure the automod", scopes=[435038183231848449,149167686159564800])
    @check(member_permissions(Permissions.ADMINISTRATOR))
    @slash_option(
        name="automod_options",
        description="Choose what you want to configure",
        required=True,
        opt_type=OptionTypes.STRING,
        choices=[
            SlashCommandChoice(name="violation_punishments", value='violation_punishments'),
            SlashCommandChoice(name="banned_words", value='banned_words'),
            SlashCommandChoice(name="ignored_channels", value='ignored_channels'),
            SlashCommandChoice(name="ignored_roles", value='ignored_roles'),
            SlashCommandChoice(name="ignored_users", value='ignored_users')
        ]
    )
    async def automod_settings_cmd(self, ctx:InteractionContext, automod_options:OptionTypes.STRING):
        if automod_options == "violation_punishments":
            settings = await db.automod_config.find_one({"guildid":ctx.guild_id})
            if settings.ban_time is None:
                bantime_prefill = MISSING
            else:
                bantime_prefill = settings.ban_time
            if settings.mute_time is None:
                mutetime_prefill = MISSING
            else:
                mutetime_prefill = settings.mute_time
            if settings.phishing.violation_count is None:
                ph_vc_pf = MISSING
            else:
                ph_vc_pf = settings.phishing.violation_count
            if settings.phishing.violation_punishment is None:
                ph_vp_pf = MISSING
            else:
                ph_vp_pf = settings.phishing.violation_punishment
            
            m = modal.Modal(title='Configure the automatic moderation', components=[
                modal.InputText(
                    label="Ban Time",
                    style=modal.TextStyles.SHORT,
                    custom_id=f'bantime',
                    placeholder="Must be min 10 s and max 28 d[`10 S`, `10 M`, `10 H`, `10 D`]",
                    value=bantime_prefill,
                    required=False
                ),
                modal.InputText(
                    label="Mute Time",
                    style=modal.TextStyles.SHORT,
                    custom_id=f'mutetime',
                    placeholder="Must be min 10 s and max 28 d[`10 S`, `10 M`, `10 H`, `10 D`]",
                    value=mutetime_prefill,
                    required=False
                ),
                modal.InputText(
                    label="Phishing Violation Count",
                    style=modal.TextStyles.SHORT,
                    custom_id=f'ph_vc',
                    placeholder="Must be between 0-10.",
                    value=ph_vc_pf,
                    required=False
                ),
                modal.InputText(
                    label="Phishing Violation Punishments",
                    style=modal.TextStyles.SHORT,
                    custom_id=f'ph_vp',
                    placeholder="warn, mute, kick, ban",
                    value=ph_vp_pf,
                    required=False
                )
            ],custom_id=f'{ctx.author.id}_automod_config_modal')
            
            await ctx.send_modal(modal=m)
            try:
                modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
            except asyncio.TimeoutError:
                return await modal_recived.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond.", ephemeral=True)
            
            bt_response = await bm_time_to_sec(ctx, modal_recived.responses.get('bantime'))
            mt_response = await bm_time_to_sec(ctx, modal_recived.responses.get('mutetime'))
            ph_vc_response = get_num(modal_recived.responses.get('ph_vc'))
            if (ph_vc_response > 10) or (ph_vc_response < 0):
                await modal_recived.send(f"{ph_vc_response} is not a valid violation count. Violation count has to be between 0-10.")
            ph_vp_response = modal_recived.responses.get('ph_vp')
            if ph_vp_response == '':
                ph_vp_response = None
            
            settings.ban_time = bt_response
            settings.mute_time = mt_response
            settings.phishing.violation_count = ph_vc_response
            settings.phishing.violation_punishment = ph_vp_response
            await settings.save()

            embed=Embed(color=0x0c73d3,
            description=f'Ban time: {bt_response} s\nMute time: {mt_response} s\nPhishing violation count: {ph_vc_response}\n Phishing punishments: {ph_vp_response}')
            await modal_recived.send(embed=embed)
            
        elif automod_options == 'banned_words':
            banned_words = await db.banned_words.find_one({'guildid':ctx.guild_id})
            settings = await db.automod_config.find_one({"guildid":ctx.guild_id})
            if settings.banned_words.violation_count is None:
                bw_vc_pf = MISSING
            else:
                bw_vc_pf = settings.banned_words.violation_count
            if settings.banned_words.violation_punishment is None:
                bw_vp_pf = MISSING
            else:
                bw_vp_pf = settings.banned_words.violation_punishment

            if banned_words is None:
                exact_prefill = MISSING
                partial_prefill = MISSING
            else:
                if (banned_words.exact is None) or (banned_words.exact == ''):
                    exact_prefill = MISSING
                else:
                    exact_prefill = banned_words.exact
                if (banned_words.partial is None) or (banned_words.partial == ''):
                    partial_prefill = MISSING
                else:
                    partial_prefill = banned_words.partial
            m = modal.Modal(title='Configure the automatic moderation', components=[
                modal.InputText(
                    label="Banned Words - Exact Match",
                    style=modal.TextStyles.PARAGRAPH,
                    custom_id=f'exact_match',
                    placeholder='Words, seperated by a comma(,). They should have minimum 3 characters.',
                    value=exact_prefill,
                    required=False
                ),
                modal.InputText(
                    label="Banned Words - Partial Match",
                    style=modal.TextStyles.PARAGRAPH,
                    custom_id=f'partial_match',
                    placeholder="Words, seperated by a comma(,). They should have minimum 3 characters.",
                    value=partial_prefill,
                    required=False
                ),
                modal.InputText(
                    label="Violation Count",
                    style=modal.TextStyles.SHORT,
                    custom_id=f'bw_vc',
                    placeholder="Must be between 0-10.",
                    value=bw_vc_pf,
                    required=False
                ),
                modal.InputText(
                    label="Punishments",
                    style=modal.TextStyles.SHORT,
                    custom_id=f'bw_vp',
                    placeholder="warn, mute, kick, ban",
                    value=bw_vp_pf,
                    required=False
                )
            ],custom_id=f'{ctx.author.id}_automod_config_modal')
            
            await ctx.send_modal(modal=m)
            try:
                modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
            except asyncio.TimeoutError:
                return await modal_recived.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond to this modal.", ephemeral=True)
            
            em_words = modal_recived.responses.get('exact_match')
            if em_words == '':
                em_words = None
            pm_words = modal_recived.responses.get('partial_match')
            if pm_words == '':
                pm_words = None
            
            bw_vc_response = modal_recived.responses.get('bw_vc')
            if (bw_vc_response == '') or (bw_vc_response is None):
                bw_vc_response = None
            elif (get_num(bw_vc_response) > 10) or (get_num(bw_vc_response) < 0):
                await modal_recived.send(f"{ph_vc_response} is not a valid violation count. Violation count has to be between 0-10.")
            bw_vp_response = modal_recived.responses.get('bw_vp')
            if bw_vp_response == '':
                bw_vp_response = None
            
            settings.banned_words.violation_count = get_num(bw_vc_response)
            settings.banned_words.violation_punishment = bw_vp_response
            await settings.save()

            if banned_words is None:
                await db.banned_words(guildid=ctx.guild_id, partial=pm_words, exact=em_words).insert()
            else:
                banned_words.exact = em_words
                banned_words.partial = pm_words
                await banned_words.save()
            
            embed=Embed(color=0x0c73d3,
            description=f'Current banned words:\nExact match:\n{em_words}\n\nPartial match:\n{pm_words}\nViolation count: {bw_vc_response}\nPunishments: {bw_vp_response}')
            await modal_recived.send(embed=embed)

        elif automod_options == 'ignored_channels':
            settings = await db.automod_config.find_one({'guildid':ctx.guild_id})
            if settings.ignored_channels is None:
                channels_prefill = MISSING
            else:
                if (settings.ignored_channels is None) or (settings.ignored_channels == ''):
                    channels_prefill = MISSING
                else:
                    channels_prefill = settings.ignored_channels
            m = modal.Modal(title='Configure the automatic moderation', components=[
                modal.InputText(
                    label="Ignored Channels",
                    style=modal.TextStyles.PARAGRAPH,
                    custom_id=f'ignored_channels',
                    placeholder="Channel ID's, seperated by a comma(,)",
                    value=channels_prefill,
                    required=False
                )
            ],custom_id=f'{ctx.author.id}_automod_ign_ch_config_modal')
            
            await ctx.send_modal(modal=m)
            try:
                modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
            except asyncio.TimeoutError:
                return await ctx.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond.", ephemeral=True)
            
            ign_ch = modal_recived.responses.get('ignored_channels')
            if ign_ch == '':
                ign_ch = None
            
            settings.ignored_channels=ign_ch
            await settings.save()
            
            embed=Embed(color=0x0c73d3,
            description=f'Current ignored channels:\n```\n{ign_ch}\n```')
            await modal_recived.send(embed=embed)

        elif automod_options == 'ignored_roles':
            settings = await db.automod_config.find_one({'guildid':ctx.guild_id})
            if settings.ignored_roles is None:
                roles_prefill = MISSING
            else:
                if (settings.ignored_roles is None) or (settings.ignored_roles == ''):
                    roles_prefill = MISSING
                else:
                    roles_prefill = settings.ignored_roles
            m = modal.Modal(title='Configure the automatic moderation', components=[
                modal.InputText(
                    label="Ignored Roles",
                    style=modal.TextStyles.PARAGRAPH,
                    custom_id=f'ignored_roles',
                    placeholder="Roles ID's, seperated by a comma(,)",
                    value=roles_prefill,
                    required=False
                )
            ],custom_id=f'{ctx.author.id}_automod_ign_r_config_modal')
            
            await ctx.send_modal(modal=m)
            try:
                modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
            except asyncio.TimeoutError:
                return await ctx.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond.", ephemeral=True)
            
            ign_r = modal_recived.responses.get('ignored_roles')
            if ign_r == '':
                ign_r = None
            
            settings.ignored_channels=ign_r
            await settings.save()
            
            embed=Embed(color=0x0c73d3,
            description=f'Current ignored roles:\n```\n{ign_r}\n```')
            await modal_recived.send(embed=embed)

        elif automod_options == 'ignored_users':
            settings = await db.automod_config.find_one({'guildid':ctx.guild_id})
            if settings.ignored_users is None:
                users_prefill = MISSING
            else:
                if (settings.ignored_users is None) or (settings.ignored_users == ''):
                    users_prefill = MISSING
                else:
                    users_prefill = settings.ignored_users
            m = modal.Modal(title='Configure the automatic moderation', components=[
                modal.InputText(
                    label="Ignored Users",
                    style=modal.TextStyles.PARAGRAPH,
                    custom_id=f'ignored_users',
                    placeholder="User ID's, seperated by a comma(,)",
                    value=users_prefill,
                    required=False
                )
            ],custom_id=f'{ctx.author.id}_automod_ign_u_config_modal')
            
            await ctx.send_modal(modal=m)
            try:
                modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
            except asyncio.TimeoutError:
                return await ctx.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond.", ephemeral=True)
            
            ign_u = modal_recived.responses.get('ignored_users')
            if ign_u == '':
                ign_u = None
            
            settings.ignored_channels=ign_u
            await settings.save()
            
            embed=Embed(color=0x0c73d3,
            description=f'Current ignored users:\n```\n{ign_u}\n```')
            await modal_recived.send(embed=embed)

    @listen()
    async def exact_match_banned_words(self, event: MessageCreate):
        message = event.message
        user = message.author
        guild = event.message.guild
        channel = message.channel
        if await is_event_active(guild, 'banned_words'):
            settings = await db.automod_config.find_one({'guildid':guild.id})
            if settings.ignored_users is not None:
                if (user.id in settings.ignored_users.split(',')):
                    return
            elif settings.ignored_channels is not None:
                if (channel.id in settings.ignored_channels.split(',')):
                    return
            elif settings.ignored_roles is not None:
                if any(role for role in user.roles if role.id in settings.ignored_roles.split(',')):
                    return
            elif (user.has_permission(Permissions.ADMINISTRATOR) == True):
                return
            is_banned_word = False
            banned_words = await db.banned_words.find_one({'guildid':guild.id})
            for bw in banned_words.exact.lower().split(','):
                bw = bw.replace(' ', '')
                bw = bw.replace('_', ' ')
                if bw.startswith('*') and bw.endswith('*'):
                    cbw = bw.replace('*', '')
                    if cbw in event.message.content.lower():
                        is_banned_word = True
                elif bw.startswith('*') and not bw.endswith('*'):
                    cbw = bw.replace('*', '')
                    for cmw in event.message.content.lower().split(','):
                        if cmw.startswith(cbw):
                            is_banned_word = True
                elif bw.endswith('*') and not bw.startswith('*'):
                    cbw = bw.replace('*', '')
                    for cmw in event.message.content.lower().split(','):
                        if cmw.endswith(cbw):
                            is_banned_word = True
                for mw in event.message.content.lower().split(','):
                    if mw == bw:
                        is_banned_word = True
            if is_banned_word == True:
                await message.delete()
                automod_reply = await channel.send(f"Hey {user.mention}! Watch your language!", ephemeral=True)
                
                reason = f'[AUTOMOD]banned words sent in {channel.name}'
                
                await automod_strike(self, event, "Automod Log (Banned Words)", reason)
                
                channelid = await db.logs.find_one({"guild_id":guild.id})
                log_channel = guild.get_channel(channelid.channel_id)
                
                violation_entries = []
                async for entry in db.strikes.find({'guildid':guild.id, 'user':user.id, 'action':"Automod Log (Banned Words)", 'automod':True}):
                    violation_entries.append(entry.user)
                if (settings.phishing.violation_count is not None) and len(violation_entries) > settings.banned_words.violation_count:
                    if 'warn' in settings.banned_words.violation_punishment:
                        await automod_warn(event, log_channel, reason)
                    
                    if 'mute' in settings.banned_words.violation_punishment:
                        await automod_mute(event, settings, reason)
                        
                    if 'kick' in settings.banned_words.violation_punishment:
                        await guild.kick(user, reason)
            
                    if 'ban' in settings.banned_words.violation_punishment:
                        await automod_ban(event, settings, log_channel, reason)
                await asyncio.sleep(3)
                await automod_reply.delete()

    @listen()
    async def partial_match_banned_words(self, event: MessageCreate):
        message = event.message
        user = message.author
        guild = event.message.guild
        channel = message.channel
        if await is_event_active(guild, 'banned_words'):
            settings = await db.automod_config.find_one({'guildid':guild.id})
            if settings.ignored_users is not None:
                if (user.id in settings.ignored_users.split(',')):
                    return
            elif settings.ignored_channels is not None:
                if (channel.id in settings.ignored_channels.split(',')):
                    return
            elif settings.ignored_roles is not None:
                if any(role for role in user.roles if role.id in settings.ignored_roles.split(',')):
                    return
            elif (user.has_permission(Permissions.ADMINISTRATOR) == True):
                return
            banned_words = await db.banned_words.find_one({'guildid':guild.id})
            for bw in banned_words.partial.split(','):
                ratio = fuzz.ratio(bw.lower(), event.message.content.lower())
                if ratio >= 80:
                    await message.delete()
                    automod_reply = await channel.send(f"Hey {user.mention}! Watch your language!", ephemeral=True)
                    
                    reason = f'[AUTOMOD]banned word sent in {channel.name}'
                    await automod_strike(self, event, "Automod Log (Banned Words)", reason)
                    
                    channelid = await db.logs.find_one({"guild_id":guild.id})
                    log_channel = guild.get_channel(channelid.channel_id)
                    
                    violation_entries = []
                    async for entry in db.strikes.find({'guildid':guild.id, 'user':user.id, 'action':"Automod Log (Banned Words)", 'automod':True}):
                        violation_entries.append(entry.user)
                    if settings.phishing.violation_count is not None:
                        if len(violation_entries) > settings.banned_words.violation_count:
                            if 'warn' in settings.banned_words.violation_punishment:
                                await automod_warn(event, log_channel, reason)
                            
                            if 'mute' in settings.banned_words.violation_punishment:
                                await automod_mute(event, settings, reason)
                                
                            if 'kick' in settings.banned_words.violation_punishment:
                                await guild.kick(user, reason)
                    
                            if 'ban' in settings.banned_words.violation_punishment:
                                await automod_ban(event, settings, reason)
                    await asyncio.sleep(3)
                    await automod_reply.delete()
    
    @listen()
    async def phishing_links_filter(self, event: MessageCreate):
        message = event.message
        user = message.author
        guild = event.message.guild
        channel = message.channel
        reason = f'[AUTOMOD]phishing link sent in {channel.name}'
        if await is_event_active(guild, 'phishing_filter'):
            settings = await db.automod_config.find_one({'guildid':guild.id})
            if settings.ignored_users is not None:
                if (user.id in settings.ignored_users.split(',')):
                    return
            if settings.ignored_channels is not None:
                if (channel.id in settings.ignored_channels.split(',')):
                    return
            if settings.ignored_roles is not None:
                if any(role for role in user.roles if role.id in settings.ignored_roles.split(',')):
                    return
            if (user.has_permission(Permissions.ADMINISTRATOR) == True):
                return
            urls = geturl(message.content)
            if urls is not None:
                for url in urls:
                    for link in self.phishing_links:
                        if link == url:
                            await message.delete()
                            automod_reply = await channel.send(f"Hey {user.mention}! That link is banned here!", ephemeral=True)
                
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
                            await asyncio.sleep(3)
                            await automod_reply.delete()

def setup(bot):
    AutoMod(bot)