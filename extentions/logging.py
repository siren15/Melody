from dataclasses import MISSING
import math
import re

from dis_snek import Snake, slash_command, InteractionContext, OptionTypes, Permissions, Scale, Embed, check, listen
from dis_snek.models.discord.enums import AuditLogEventType
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *
from dis_snek.api.events.discord import MemberRemove

class Logging(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @slash_command(name='logchannel', description="set up a logging channel")
    @channel()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def logchannel(self, ctx, channel:OptionTypes.CHANNEL=None):
        if channel == None:
            embed = Embed(
                description=":x: Please provide a channel",
                color=0xDD2222)
            await ctx.send(embed=embed)
            return

        db = await odm.connect()
        log_entry = await db.find_one(logs, {"guild_id":ctx.guild.id})
        if log_entry == None:
            await db.save(logs(guild_id=ctx.guild.id, channel_id=channel.id))
            embed = Embed(description=f"I have assigned {channel.mention} as a log channel.",
                                  color=0x0c73d3)
            await ctx.send(embed=embed)
        else:
            log_entry.channel_id = channel.id
            await db.save(log_entry)
            embed = Embed(description=f"I have updated {channel.mention} as a log channel.",
                                  color=0x0c73d3)
            await ctx.send(embed=embed)
    
    @listen()
    async def on_message_delete(self, event):
        message = event.message
        if message.author.bot:
            return
        if await is_event_active(message.guild, 'message_deleted'):
            db = await odm.connect()
            channelid = await db.find_one(logs, {"guild_id":message.guild.id})
            id = channelid.channel_id
            log_channel = message.guild.get_channel(id)

            def geturl(string):
                regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
                url = re.findall(regex,string)
                return [x[0] for x in url]

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
                        await log_channel.send(embed=embed)
                        return
            else:
                url = geturl(message.content)
                for url in url:
                    url = url
                if url:
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
                    await log_channel.send(embed=embed)
    
    @listen()
    async def on_message_update(self, event):
        before = event.before
        after = event.after
        if before.author.bot:
            return
        if await is_event_active(before.guild, 'message_edited'):
            db = await odm.connect()
            channelid = await db.find_one(logs, {"guild_id":before.guild.id})
            id = channelid.channel_id
            log_channel = before.guild.get_channel(id)

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
            await log_channel.send(embed=embed)
    
    @listen()
    async def on_member_add(self, event):
        member = event.member
        
        if await is_event_active(member.guild, 'member_join') == True:
            db = await odm.connect()
            channelid = await db.find_one(logs, {"guild_id":member.guild.id})
            id = channelid.channel_id
            log_channel = member.guild.get_channel(id)

            embed = Embed(description=f"{member.mention} **|** {member.display_name} **joined** {member.guild.name}",
                                    timestamp=datetime.utcnow(),
                                    color=0x4ba567)
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Account created:", value=f"<t:{math.ceil(member.created_at.timestamp())}:R>")
            embed.set_footer(text=f'User ID: {member.id}')
            await log_channel.send(embed=embed)
    
    @listen()
    async def on_member_remove(self, event):
        member = event.member
        if await is_event_active(member.guild, 'member_leave') == True:
            roles = [role.mention for role in member.roles if role.name != '@everyone']
            rolecount = len(roles)
            if rolecount == 0:
                roles = 'None'
            else:
                roles = ' '.join(roles)
            db = await odm.connect()
            channelid = await db.find_one(logs, {"guild_id":member.guild.id})
            log_channel = member.guild.get_channel(channelid.channel_id)
            embed = Embed(description=f"{member.mention} **|** {member} **left** {member.guild.name}",
                                    timestamp=datetime.utcnow(),
                                    color=0xda4d50)
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name=f'Roles: [{rolecount}]', value=roles)
            embed.set_footer(text=f'User ID: {member.id}')
            await log_channel.send(embed=embed)
        if await is_event_active(member.guild, 'member_kick'):
            db = await odm.connect()
            last_au_entry = await db.find_one(auditlogs, {'guildid':member.guild.id, 'action_type':20})
            if last_au_entry == None:
                last_entry = MISSING
            else:
                last_entry = last_au_entry.last_entry
            audit_log_entry = await member.guild.get_audit_log(action_type=20, limit=1, after=last_entry)
            for au_entry in audit_log_entry.entries:
                if (int(au_entry.id) != int(last_au_entry.last_entry)) and (int(member.id) == int(au_entry.target_id)):
                    reason = au_entry.reason
                    for au_user in audit_log_entry.users:
                        if au_entry.target_id == au_user.id:
                            target = au_user
                        elif au_entry.user_id == au_user.id:
                            moderator = au_user
                    
                    if last_au_entry == None:
                        await db.save(auditlogs(guildid=member.guild.id, action_type=20, last_entry=au_entry.id))
                    else:
                        last_au_entry.last_entry = au_entry.id
                        await db.save(last_au_entry)
                    
                    channelid = await db.find_one(logs, {"guild_id":member.guild.id})
                    log_channel = member.guild.get_channel(channelid.channel_id)
                
                    embed = Embed(description=f'{moderator.mention}**[**{moderator}**|**{moderator.id}**]** **kicked** {target.mention}**[**{target}**|**{target.id}**]** **|** `{reason}`',
                                            timestamp=datetime.utcnow(),
                                            color=0xdd8d2c)
                    embed.set_thumbnail(url=target.avatar.url)
                    await log_channel.send(embed=embed)
    
    @listen()
    async def on_ban_create(self, event):
        member = event.user
        guild = event.guild
        if await is_event_active(guild, 'member_ban'):
            db = await odm.connect()
            last_au_entry = await db.find_one(auditlogs, {'guildid':guild.id, 'action_type':22})
            if last_au_entry == None:
                last_entry = MISSING
            else:
                last_entry = last_au_entry.last_entry
            audit_log_entry = await guild.get_audit_log(action_type=22, limit=1, after=last_entry)
            for au_entry in audit_log_entry.entries:
                if (int(au_entry.id) != int(last_au_entry.last_entry)) and (int(member.id) == int(au_entry.target_id)):
                    reason = au_entry.reason
                    for au_user in audit_log_entry.users:
                        if au_entry.target_id == au_user.id:
                            target = au_user
                        elif au_entry.user_id == au_user.id:
                            moderator = au_user
                    
                    if last_au_entry == None:
                        await db.save(auditlogs(guildid=guild.id, action_type=22, last_entry=au_entry.id))
                    else:
                        last_au_entry.last_entry = au_entry.id
                        await db.save(last_au_entry)
                    
                    channelid = await db.find_one(logs, {"guild_id":guild.id})
                    log_channel = guild.get_channel(channelid.channel_id)
                
                    embed = Embed(description=f'{moderator.mention}**[**{moderator}**|**{moderator.id}**]** **banned** {target.mention}**[**{target}**|**{target.id}**]** **|** `{reason}`',
                                            timestamp=datetime.utcnow(),
                                            color=0xdd352c)
                    embed.set_thumbnail(url=target.avatar.url)
                    await log_channel.send(embed=embed)
    
    @listen()
    async def on_ban_remove(self, event):
        member = event.user
        guild = event.guild
        if await is_event_active(guild, 'member_unban'):
            db = await odm.connect()
            last_au_entry = await db.find_one(auditlogs, {'guildid':guild.id, 'action_type':23})
            if last_au_entry == None:
                last_entry = MISSING
            else:
                last_entry = last_au_entry.last_entry
            audit_log_entry = await guild.get_audit_log(action_type=23, limit=1, after=last_entry)
            for au_entry in audit_log_entry.entries:
                if (int(au_entry.id) != int(last_au_entry.last_entry)) and (int(member.id) == int(au_entry.target_id)):
                    reason = au_entry.reason
                    for au_user in audit_log_entry.users:
                        if au_entry.target_id == au_user.id:
                            target = au_user
                        elif au_entry.user_id == au_user.id:
                            moderator = au_user
                    
                    if last_au_entry == None:
                        await db.save(auditlogs(guildid=guild.id, action_type=23, last_entry=au_entry.id))
                    else:
                        last_au_entry.last_entry = au_entry.id
                        await db.save(last_au_entry)
                    
                    channelid = await db.find_one(logs, {"guild_id":guild.id})
                    log_channel = guild.get_channel(channelid.channel_id)
                
                    embed = Embed(description=f'{moderator.mention}**[**{moderator}**|**{moderator.id}**]** **unbanned** {target.mention}**[**{target}**|**{target.id}**]** **|** `{reason}`',
                                            timestamp=datetime.utcnow(),
                                            color=0xe5bb3b)
                    embed.set_thumbnail(url=target.avatar.url)
                    await log_channel.send(embed=embed)

def setup(bot):
    Logging(bot)