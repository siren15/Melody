import math
import random
import re
import os
import requests

from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps
from interactions import Client, slash_command, OptionType, Permissions, Extension, Embed, check, listen, InteractionContext
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *
from interactions.api.events.discord import MemberRemove, MessageDelete, MemberUpdate, BanCreate, BanRemove, MemberAdd, MessageUpdate, GuildAuditLogEntryCreate
from interactions.client.const import MISSING

from utils.utils import strike_id_gen

def random_string_generator():
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    result=''
    for i in range(0, 8):
        result += random.choice(characters)
    return result

def snowflake_time(id: int) -> datetime:
    """
    Parameters
    -----------
    id: :class:`int`
        The snowflake ID.
    Returns
    --------
    :class:`datetime.datetime`
        An aware datetime in UTC representing the creation time of the snowflake.
    """
    timestamp = ((id >> 22) + 1420070400000) / 1000
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

def date_diff_in_Seconds(dt2, dt1):
  timedelta = dt2 - dt1
  return timedelta.days * 24 * 3600 + timedelta.seconds

def geturl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    url_2 = [x[0] for x in url]
    if url_2 != []:
        for url in url_2:
            return url
    return None

class EventLogs(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
    
    @slash_command(name='logchannel', description="set up a logging channel",
        default_member_permissions=Permissions.ADMINISTRATOR
    )
    @channel()
    async def logchannel(self, ctx: InteractionContext, channel:OptionType.CHANNEL=None):
        if channel is None:
            channel = ctx.channel
        
        log_entry = await db.logs.find_one({"guild_id":ctx.guild_id})
        if log_entry is None:
            await db.logs(guild_id=ctx.guild_id, channel_id=channel.id).save()
            embed = Embed(description=f"I have assigned {channel.mention} as a log channel.",
                                  color=0xffcc50)
            await ctx.send(embed=embed)
        else:
            log_entry.channel_id = channel.id
            await log_entry.save()
            embed = Embed(description=f"I have updated {channel.mention} as a log channel.",
                                  color=0xffcc50)
            await ctx.send(embed=embed)
    
    @slash_command(name='welcomemessage', description="set up a welcome message and channel",
        default_member_permissions=Permissions.ADMINISTRATOR
    )
    @welcome_message_text()
    @channel()
    async def welcome_message_cmd(self, ctx: InteractionContext, welcome_message_text:OptionType.STRING=None, channel:OptionType.CHANNEL=None):
        if (channel is None) and (welcome_message_text is None):
            embed = Embed(
                description=":x: Please provide a channel or welcome message",
                color=0xDD2222)
            await ctx.send(embed=embed)
            return
        
        log_entry = await db.welcome_msg.find_one({"guildid":ctx.guild_id})
        if log_entry is None:
            up_msg = ''
            if welcome_message_text is not None:
                up_msg = up_msg + f"I have updated `{welcome_message_text}` as a welcome message.\n"

            if channel is not None:
                up_msg = up_msg + f"I have updated {channel.mention} as a welcome channel."
                channel = channel.id
            elif channel is None:
                channel = None
            await db.welcome_msg(guildid=ctx.guild_id, channelid=channel, message=welcome_message_text).save()
            embed = Embed(description=up_msg,
                                  color=0xffcc50)
            await ctx.send(embed=embed)
        else:
            up_msg = ''
            if welcome_message_text is not None:
                log_entry.message = welcome_message_text
                up_msg = up_msg + f"I have updated `{welcome_message_text}` as a welcome message.\n"

            if channel is not None:
                log_entry.channelid = channel.id
                up_msg = up_msg + f"I have updated {channel.mention} as a welcome channel."

            await log_entry.save()
            embed = Embed(description=up_msg,
                                  color=0xffcc50)
            await ctx.send(embed=embed)

    @slash_command(name='leavemessage', description="set up a leave message and channel",
        default_member_permissions=Permissions.ADMINISTRATOR
    )
    @leave_message_text()
    @channel()
    async def leave_message_cmd(self, ctx: InteractionContext, leave_message_text:OptionType.STRING=None, channel:OptionType.CHANNEL=None):
        if (channel is None) and (leave_message_text is None):
            embed = Embed(
                description=":x: Please provide a channel or leave message",
                color=0xDD2222)
            await ctx.send(embed=embed)
            return
        
        log_entry = await db.leave_msg.find_one({"guildid":ctx.guild_id})
        if log_entry is None:
            up_msg = ''
            if leave_message_text is not None:
                up_msg = up_msg + f"I have updated `{leave_message_text}` as a leave message.\n"

            if channel is not None:
                up_msg = up_msg + f"I have updated {channel.mention} as a leave channel."
                channel = channel.id
            elif channel is None:
                channel = None
            await db.leave_msg(guildid=ctx.guild_id, channelid=channel, message=leave_message_text).save()
            embed = Embed(description=up_msg,
                                  color=0xffcc50)
            await ctx.send(embed=embed)
        else:
            up_msg = ''
            if leave_message_text is not None:
                log_entry.message = leave_message_text
                up_msg = up_msg + f"I have updated `{leave_message_text}` as a leave message.\n"

            if channel is not None:
                log_entry.channelid = channel.id
                up_msg = up_msg + f"I have updated {channel.mention} as a leave channel."

            await log_entry.save()
            embed = Embed(description=up_msg,
                                  color=0xffcc50)
            await ctx.send(embed=embed)
    
    @slash_command(name='specialwelcomemsg', description="set up a special welcome message and channel", scopes=[149167686159564800, 435038183231848449],
        default_member_permissions=Permissions.ADMINISTRATOR
    )
    @welcome_message_text()
    @channel()
    async def specialwelcome_message_cmd(self, ctx: InteractionContext, welcome_message_text:OptionType.STRING=None, channel:OptionType.CHANNEL=None):
        if (channel is None) and (welcome_message_text is None):
            embed = Embed(
                description=":x: Please provide a channel or welcome message",
                color=0xDD2222)
            await ctx.send(embed=embed)
            return
        
        log_entry = await db.special_welcome_msg.find_one({"guildid":ctx.guild_id})
        if log_entry is None:
            up_msg = ''
            if welcome_message_text is not None:
                up_msg = up_msg + f"I have updated `{welcome_message_text}` as a special welcome message.\n"

            if channel is not None:
                up_msg = up_msg + f"I have updated {channel.mention} as a special welcome channel."
                channel = channel.id
            elif channel is None:
                channel = None
            await db.special_welcome_msg(guildid=ctx.guild_id, channelid=channel, message=welcome_message_text).save()
            embed = Embed(description=up_msg,
                                  color=0xffcc50)
            await ctx.send(embed=embed)
        else:
            up_msg = ''
            if welcome_message_text is not None:
                log_entry.message = welcome_message_text
                up_msg = up_msg + f"I have updated `{welcome_message_text}` as special a welcome message.\n"

            if channel is not None:
                log_entry.channelid = channel.id
                up_msg = up_msg + f"I have updated {channel.mention} as a special welcome channel."

            await log_entry.save()
            embed = Embed(description=up_msg,
                                  color=0xffcc50)
            await ctx.send(embed=embed)
    
    @listen()
    async def on_message_delete_attachments(self, event: MessageDelete):
        message = event.message
        if message.author.bot:
            return
        if await is_event_active(message.guild, 'message_deleted'):
            if message.attachments:
                for file in message.attachments:
                    if file.filename.endswith('.jpg') or file.filename.endswith('.jpeg') or file.filename.endswith('.png') or file.filename.endswith('.gif'):
                        url = file.proxy_url
                        if message.content == '':
                            content = "[No written message content]"
                        else:
                            content = message.content

                        embed = Embed(description=f"Message deleted in {message.channel.mention}",
                                                timestamp=datetime.utcnow(),
                                                color=0xfc5f62)
                        embed.set_author(name=message.author.display_name)
                        embed.set_thumbnail(url=message.author.avatar.url)
                        embed.add_field(name="Content:", value=f"{content}", inline=False)
                        embed.set_image(url=f"{url}")
                        embed.set_footer(text=f'User ID: {message.author.id}\nMessage ID: {message.id}')
                        
                        channelid = await db.logs.find_one({"guild_id":message.guild.id})
                        id = channelid.channel_id
                        log_channel = message.guild.get_channel(id)
                        await log_channel.send(embed=embed)
                        return
                    else:
                        url = file.proxy_url
                        if message.content == '':
                            content = "[No written message content]"
                        else:
                            content = message.content

                        embed = Embed(description=f"Message deleted in {message.channel.mention}",
                                                timestamp=datetime.utcnow(),
                                                color=0xfc5f62)
                        embed.set_author(name=message.author.display_name)
                        embed.set_thumbnail(url=message.author.avatar.url)
                        embed.add_field(name="Content:", value=f"{content}\n\n{url}", inline=False)
                        embed.set_footer(text=f'User ID: {message.author.id}\nMessage ID: {message.id}')
                        
                        channelid = await db.logs.find_one({"guild_id":message.guild.id})
                        id = channelid.channel_id
                        log_channel = message.guild.get_channel(id)
                        await log_channel.send(embed=embed)
                        return

    @listen()
    async def on_message_delete_regular(self, event: MessageDelete):
        message = event.message
        if message.author.bot:
            return
        if await is_event_active(message.guild, 'message_deleted'):
            if not message.attachments:
                if geturl(message.content) is None:
                    embed = Embed(description=f"Message deleted in {message.channel.mention}",
                                            timestamp=datetime.utcnow(),
                                            color=0xfc5f62)
                    embed.set_author(name=message.author.display_name)
                    embed.set_thumbnail(url=message.author.avatar.url)
                    embed.add_field(name="Content:", value=message.content, inline=False)
                    embed.set_footer(text=f'User ID: {message.author.id}\nMessage ID: {message.id}')
                    
                    channelid = await db.logs.find_one({"guild_id":message.guild.id})
                    id = channelid.channel_id
                    log_channel = message.guild.get_channel(id)
                    await log_channel.send(embed=embed)

    @listen()
    async def on_message_delete_url(self, event: MessageDelete):
        message = event.message
        if message.author.bot:
            return
        if await is_event_active(message.guild, 'message_deleted'):
            if not message.attachments:
                if geturl(message.content) is not None:
                    url = geturl(message.content)
                    if url.endswith('.jpg') or url.endswith('.jpeg') or url.endswith('.png') or url.endswith('.gif'):
                        content = message.content.replace(f'{url}', '')
                        if content == '':
                            content = "[No written message content]"

                        embed = Embed(description=f"Message deleted in {message.channel.mention}",
                                                timestamp=datetime.utcnow(),
                                                color=0xfc5f62)
                        embed.set_author(name=message.author.display_name)
                        embed.set_thumbnail(url=message.author.avatar.url)
                        embed.add_field(name="Content:", value=content, inline=False)
                        embed.set_image(url=url)
                        embed.set_footer(text=f'User ID: {message.author.id}\nMessage ID: {message.id}')
                        
                        channelid = await db.logs.find_one({"guild_id":message.guild.id})
                        id = channelid.channel_id
                        log_channel = message.guild.get_channel(id)
                        await log_channel.send(embed=embed)
                        return
                    else:
                        embed = Embed(description=f"Message deleted in {message.channel.mention}",
                                                timestamp=datetime.utcnow(),
                                                color=0xfc5f62)
                        embed.set_author(name=message.author.display_name)
                        embed.set_thumbnail(url=message.author.avatar.url)
                        embed.add_field(name="Content:", value=message.content, inline=False)
                        embed.set_footer(text=f'User ID: {message.author.id}\nMessage ID: {message.id}')
                        
                        channelid = await db.logs.find_one({"guild_id":message.guild.id})
                        id = channelid.channel_id
                        log_channel = message.guild.get_channel(id)
                        await log_channel.send(embed=embed)
                        return
    
    @listen()
    async def on_message_update(self, event:MessageUpdate):
        if event.before is None:
            return
        before = event.before
        after = event.after
        if before.author.bot:
            return
        if await is_event_active(before.guild, 'message_edited'):
            if before.content == after.content:
                return

            embed = Embed(description=f"Message edited in {before.channel.mention}\n[[Jump to message.]]({after.jump_url})",
                                    timestamp=datetime.utcnow(),
                                    color=0xfcab5f)
            embed.set_author(name=before.author.display_name)
            embed.set_thumbnail(url=before.author.avatar.url)
            embed.add_field(name="Original message", value=before.content, inline=False)
            embed.add_field(name="Edited message", value=after.content, inline=False)
            embed.set_footer(text=f'User ID: {before.author.id}\nMessage ID: {before.id}')
            
            channelid = await db.logs.find_one({"guild_id":before.guild.id})
            id = channelid.channel_id
            log_channel = before.guild.get_channel(id)
            await log_channel.send(embed=embed)
    
    @listen()
    async def on_member_join(self, event: MemberAdd):
        member = event.member
        
        if await is_event_active(member.guild, 'member_join') == True:
            
            channelid = await db.logs.find_one({"guild_id":member.guild.id})
            id = channelid.channel_id
            log_channel = member.guild.get_channel(id)

            embed = Embed(description=f"{member.mention} **|** {member.display_name} **joined** {member.guild.name}",
                                    timestamp=datetime.utcnow(),
                                    color=0x4d9d54)
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Account created:", value=f"<t:{math.ceil(member.created_at.timestamp())}:R>")
            embed.set_footer(text=f'User ID: {member.id}')
            await log_channel.send(embed=embed)
    
    @listen()
    async def on_member_leave(self, event: MemberRemove):
        member = event.member
        if await is_event_active(member.guild, 'member_leave') == True:
            roles = [role.mention for role in member.roles if role.name != '@everyone']
            rolecount = len(roles)
            if rolecount == 0:
                roles = 'None'
            else:
                roles = ' '.join(roles)
            
            channelid = await db.logs.find_one({"guild_id":member.guild.id})
            log_channel = member.guild.get_channel(channelid.channel_id)
            embed = Embed(description=f"{member.mention} **|** {member} **left** {member.guild.name}",
                                    timestamp=datetime.utcnow(),
                                    color=0xcb4c4c)
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name=f'Roles: [{rolecount}]', value=roles)
            embed.set_footer(text=f'User ID: {member.id}')
            await log_channel.send(embed=embed)
    
    @listen()
    async def on_member_role_remove(self, event: MemberUpdate):
        member = event.after
        if await is_event_active(member.guild, 'member_roles') == True:
            before_roles = event.before.roles
            after_roles = event.after.roles

            roles_list = [role.mention for role in before_roles if role not in after_roles]
            if roles_list != []:
                roles = ''
                for role in roles_list:
                    roles = roles + f'{role} '
                embed = Embed(description=f"`{member}` **got removed** {roles} ",
                                            color=0xffcc50)
                
                channelid = await db.logs.find_one({"guild_id":member.guild.id})
                log_channel = member.guild.get_channel(channelid.channel_id)
                await log_channel.send(embed=embed)
    
    @listen()
    async def on_member_role_add(self, event: MemberUpdate):
        member = event.after
        if await is_event_active(member.guild, 'member_roles') == True:
            before_roles = event.before.roles
            after_roles = event.after.roles

            roles_list = [role.mention for role in after_roles if role not in before_roles]
            if roles_list != []:
                roles = ''
                for role in roles_list:
                    roles = roles + f'{role} '
                embed = Embed(description=f"`{member}` **got assigned** {roles} ",
                                            color=0xffcc50)
                
                channelid = await db.logs.find_one({"guild_id":member.guild.id})
                log_channel = member.guild.get_channel(channelid.channel_id)
                await log_channel.send(embed=embed)
    
    @listen()
    async def on_member_nickname_change(self, event: MemberUpdate):
        member = event.after
        if await is_event_active(member.guild, 'member_nick') == True:
            before = event.before
            after = event.after

            if before.display_name != after.display_name:
                embed = Embed(description=f"`{member}` changed their nickname",
                                        color=0xffcc50)
                embed.set_thumbnail(url=after.avatar.url)
                embed.add_field(name="Before", value=before.display_name)
                embed.add_field(name="After", value=after.display_name)
                
                channelid = await db.logs.find_one({"guild_id":member.guild.id})
                log_channel = member.guild.get_channel(channelid.channel_id)
                await log_channel.send(embed=embed)

    @listen()
    async def on_member_update_timeout_remove(self, event: MemberUpdate):
        member_after = event.after
        if event.after.communication_disabled_until is MISSING and event.before.communication_disabled_until is MISSING:
            return
        if event.after.communication_disabled_until is None and event.before.communication_disabled_until is None:
            return
        if event.after.communication_disabled_until == event.before.communication_disabled_until:
            return
        if (member_after.communication_disabled_until is None) and (await is_event_active(event.guild, 'member_timeout') == True):
            audit_log_entry = await event.guild.fetch_audit_log(action_type=24, limit=1)
            for au_entry in audit_log_entry.entries:
                entry_created_at = snowflake_time(au_entry.id)
                cdiff = date_diff_in_Seconds(datetime.now(tz=timezone.utc), entry_created_at.replace(tzinfo=timezone.utc))
                if cdiff <= 60:
                    reason = au_entry.reason
                    for au_user in audit_log_entry.users:
                        if au_entry.target_id == au_user.id:
                            target = au_user
                        elif au_entry.user_id == au_user.id:
                            moderator = au_user
                    if target.id == member_after.id:
                        embed = Embed(description=f"{target} **was unmuted** | {reason} \n**User ID:** {target.id} \n**Actioned by:** {moderator}",
                                        color=0xffcc50,
                                        timestamp=datetime.utcnow())
                        embed.set_thumbnail(url=target.avatar.url)
                        
                        channelid = await db.logs.find_one({"guild_id":event.guild_id})
                        log_channel = event.guild.get_channel(channelid.channel_id)
                        await log_channel.send(embed=embed)

    @listen()
    async def on_member_update_timeout_add(self, event: MemberUpdate):
        member_after = event.after
        if event.after.communication_disabled_until is MISSING and event.before.communication_disabled_until is MISSING:
            return
        if event.after.communication_disabled_until is None and event.before.communication_disabled_until is None:
            return
        if event.after.communication_disabled_until == event.before.communication_disabled_until:
            return
        if member_after.communication_disabled_until is not None:
            timeout_timestamp = f'{member_after.communication_disabled_until}'.replace('<t:', '')
            timeout_timestamp = timeout_timestamp.replace('>', '')
            timeout_timestamp = int(timeout_timestamp)
            dt = datetime.fromtimestamp(timeout_timestamp)
            dt = dt.replace(tzinfo=timezone.utc)
            audit_log_entry = await event.guild.fetch_audit_log(action_type=24, limit=1)
            for au_entry in audit_log_entry.entries:
                entry_created_at = snowflake_time(au_entry.id)
                cdiff = date_diff_in_Seconds(datetime.now(tz=timezone.utc), entry_created_at.replace(tzinfo=timezone.utc))
                if cdiff <= 60:
                    reason = au_entry.reason
                    for au_user in audit_log_entry.users:
                        if au_entry.target_id == au_user.id:
                            target = au_user
                        elif au_entry.user_id == au_user.id:
                            moderator = au_user
            if target.id == member_after.id:
                if (member_after.communication_disabled_until is not None) and (dt > datetime.now(tz=timezone.utc)):
                    if await is_event_active(event.guild, 'member_timeout') == True:
                        mute_time = f'{member_after.communication_disabled_until}'.replace('>', ':R>')
                        embed = Embed(description=f"{target} **was muted** | {reason} \n**User ID:** {target.id} \n**Actioned by:** {moderator}\n**End time:**{mute_time}",
                                        color=0xffcc50,
                                        timestamp=datetime.utcnow())
                        embed.set_thumbnail(url=target.avatar.url)
                        
                        channelid = await db.logs.find_one({"guild_id":event.guild_id})
                        log_channel = event.guild.get_channel(channelid.channel_id)
                        await log_channel.send(embed=embed)

                    daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
                    
                    while True:
                        muteid = random_string_generator()
                        muteid_db = await db.strikes.find_one({'guildid':event.guild_id, 'strikeid':muteid})
                        if muteid_db is None:
                            break
                        else:
                            continue
                    await db.strikes(strikeid=muteid, guildid=event.guild_id, user=target.id, moderator=moderator.id, action="Mute", day=daytime, reason=reason).insert()

    @listen()
    async def audit_log_kick_create(self, event: GuildAuditLogEntryCreate):
        audit_log = event.audit_log_entry
        guild = event.guild
        if audit_log.action_type == 20:
            moderator = guild.get_member(audit_log.user_id)
            target = guild.get_member(audit_log.target_id)
            if target is None:
                target = await self.bot.fetch_user(audit_log.target_id)
            reason = audit_log.reason
            if await is_event_active(guild, 'member_kick'):
                channelid = await db.logs.find_one({"guild_id":guild.id})
                log_channel = guild.get_channel(channelid.channel_id)
                embed = Embed(description=f'{moderator.mention}**[**{moderator}**|**{moderator.id}**]** **kicked** {target.mention}**[**{target}**|**{target.id}**]** **|** `{reason}`',
                                        timestamp=datetime.utcnow(),
                                        color=0x5c7fb0)
                embed.set_thumbnail(url=target.avatar.url)
                await log_channel.send(embed=embed)

            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.strikes(strikeid=await strike_id_gen(guild), guildid=event.guild_id, user=target.id, moderator=moderator.id, action="Kick", day=daytime, reason=reason).insert()

    @listen()
    async def audit_log_ban_create(self, event: GuildAuditLogEntryCreate):
        audit_log = event.audit_log_entry
        guild = event.guild
        if audit_log.action_type == 22:
            moderator = guild.get_member(audit_log.user_id)
            target = guild.get_member(audit_log.target_id)
            if target is None:
                target = await self.bot.fetch_user(audit_log.target_id)
            reason = audit_log.reason
            if await is_event_active(guild, 'member_ban'):
                channelid = await db.logs.find_one({"guild_id":guild.id})
                log_channel = guild.get_channel(channelid.channel_id)
            
                embed = Embed(description=f'{moderator.mention}**[**{moderator}**|**{moderator.id}**]** **banned** {target.mention}**[**{target}**|**{target.id}**]** **|** `{reason}`',
                                        timestamp=datetime.utcnow(),
                                        color=0x62285e)
                embed.set_thumbnail(url=target.avatar.url)
                await log_channel.send(embed=embed)

            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.strikes(strikeid=await strike_id_gen(guild), guildid=guild.id, user=target.id, moderator=moderator.id, action="Ban", day=daytime, reason=reason).insert()

    @listen()
    async def audit_log_unban_create(self, event: GuildAuditLogEntryCreate):
        audit_log = event.audit_log_entry
        guild = event.guild
        if audit_log.action_type == 23:
            moderator = guild.get_member(audit_log.user_id)
            target = guild.get_member(audit_log.target_id)
            if target is None:
                target = await self.bot.fetch_user(audit_log.target_id)
            reason = audit_log.reason
            if await is_event_active(guild, 'member_unban'):
                channelid = await db.logs.find_one({"guild_id":guild.id})
                log_channel = guild.get_channel(channelid.channel_id)
            
                embed = Embed(description=f'{moderator.mention}**[**{moderator}**|**{moderator.id}**]** **unbanned** {target.mention}**[**{target}**|**{target.id}**]** **|** `{reason}`',
                                        timestamp=datetime.utcnow(),
                                        color=0x9275b2)
                embed.set_thumbnail(url=target.avatar.url)
                await log_channel.send(embed=embed)

            daytime = f'<t:{math.ceil(datetime.now().timestamp())}>'
            await db.strikes(strikeid=await strike_id_gen(guild), guildid=guild.id, user=target.id, moderator=moderator.id, action="Unban", day=daytime, reason=reason).insert()

    @listen()
    async def welcome_message(self, event: MemberAdd):
        member = event.member
        user = event.member
        guild = event.member.guild
        if await is_event_active(member.guild, 'welcome_msg') == True:
            wm = await db.welcome_msg.find_one({"guildid":member.guild.id})
            if wm is not None:
                if wm.channelid is not None:
                    wchannel = member.guild.get_channel(wm.channelid)
                    if wchannel is not None:
                        if await is_event_active(member.guild, 'welcome_msg_card') == True:
                            def round(im):
                                im = im.resize((210*16,210*16), resample=Image.ANTIALIAS)
                                mask = Image.new("L", im.size, 0)
                                draw = ImageDraw.Draw(mask)
                                draw.ellipse((0,0)+im.size, fill=255)
                                out = ImageOps.fit(im, mask.size, centering=(0,0))
                                out.putalpha(mask)
                                image = out.resize((210,210), resample=Image.ANTIALIAS).convert("RGBA")
                                return image

                            IW, IH = (956, 435)

                            if wm.background_url is not None:
                                background = Image.open(requests.get(f'{wm.background_url}', stream=True).raw).crop((0,0,IW,IH)).convert("RGBA")
                            else:
                                background = Image.open(requests.get('https://i.imgur.com/5FL6qEm.png', stream=True).raw).convert("RGBA")

                            overlay = Image.open(requests.get('https://i.imgur.com/Bu4STJz.png', stream=True).raw).convert("RGBA")
                            background.paste(overlay, (0, 0), overlay)

                            pfp = round(Image.open(requests.get(f'{event.member.avatar.url}.png', stream=True).raw).resize((230,230)).convert("RGBA"))
                            background.paste(pfp, (373, 42), pfp)

                            font = ImageFont.truetype('Everson-Mono-Bold.ttf', 45)
                            card = ImageDraw.Draw(background)
                            memname = f"{member.display_name}\nMember #{len(member.guild.members)}"
                            tw, th = card.textsize(memname, font)
                            card.text((((IW-tw)/2),283), memname, font=font, stroke_width=2, align="center", stroke_fill=(30, 27, 26), fill=(255, 255, 255))
                            background.save(f'welcomecard_{member.id}.png')
                            if wm.message  is not None:
                                await wchannel.send(wm.message.format(user=user, member=member, guild=guild), file=f'welcomecard_{member.id}.png')
                            elif wm.message is None:
                                await wchannel.send(file=f'welcomecard_{member.id}.png')
                            os.remove(f'welcomecard_{member.id}.png')
                        else:
                            if wm.message is not None:
                                await wchannel.send(wm.message.format(user=user, member=member, guild=guild))
    
    @listen()
    async def special_welcome_message(self, event: MemberUpdate):
        member = event.after
        user = event.after
        guild = event.after.guild
        if await is_event_active(member.guild, 'special_welcome_msg') == True:
            before_roles = event.before.roles
            after_roles = event.after.roles
            ignore_roles = [role for role in before_roles if role.name in ['Muted', 'Limbo']]
            if ignore_roles == []:
                roles_list = [role for role in after_roles if role not in before_roles if role.name == 'Gravity Falls Citizens']
                if roles_list != []:
                    wm = await db.special_welcome_msg.find_one({"guildid":member.guild.id})
                    if wm is not None:
                        if wm.channelid is not None:
                            wchannel = member.guild.get_channel(wm.channelid)
                            if (wchannel is not None) and (wm.message is not None):
                                return await wchannel.send(wm.message.format(user=user, member=member, guild=guild))

    @listen()
    async def leave_message(self, event: MemberRemove):
        member = event.member
        user = event.member
        guild = event.member.guild
        if await is_event_active(member.guild, 'leave_msg') == True:
            lm = await db.leave_msg.find_one({"guildid":member.guild.id})
            if lm is not None:
                if lm.channelid is not None:
                    lchannel = member.guild.get_channel(lm.channelid)
                    if (lm.message and lchannel) is not None:
                        await lchannel.send(lm.message.format(user=user, member=member, guild=guild))

def setup(bot):
    EventLogs(bot)