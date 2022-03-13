import asyncio
from datetime import datetime, timezone
import math
from dateutil.relativedelta import relativedelta
from dis_snek import Snake, Scale, Permissions, Embed, slash_command, InteractionContext, OptionTypes, check, ModalContext, Guild
# from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *

all_commands = ['echo', 'userinfo', 'botinfo', 'avatar', 'useravatar', 'embed create', 'embed edit', 't', 'tag recall', 'tag create', 'tag edit', 'tag delete', 'tag claim', 'tag list', 'tag aedit', 'tag gift', 'tag info', 'ban', 'mute', 'delete', 'kick', 'unban', 'warn add', 'warn remove', 'limbo', 'userpurge', 'warnings', 'strikes', 'rank', 'ranklist', 'leveling addrole', 'leveling removerole', 'leaderboard', 'giveyou _', 'giveyou create', 'giveyou delete', 'giveyou list', 'uptime', 'reactionrole create', 'reactionrole delete']

async def guild_owner(ctx) -> bool:
    members = [m for m in ctx.guild.members]
    for member in members:
        if ctx.guild.is_owner(member) == True:
            return member


class Basic(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @slash_command(name='command', sub_cmd_name='restrict', sub_cmd_description='Restrict a commands usage to a specific role', scopes=[435038183231848449, 149167686159564800])
    @slash_option(name='command_name', description='Type the command to restrict', opt_type=OptionTypes.STRING, required=True)
    @role()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def temp_restrict_cmd(self, ctx: InteractionContext, command_name:str=None, role:OptionTypes.ROLE=None):
        cmd = command_name
        if cmd is None:
            return await ctx.send(':x: You have to include a command name', ephemeral=True)
        elif role is None:
            return await ctx.send(':x: You have to include a role', ephemeral=True)

        if cmd.lower() in all_commands:
            
            
            regx = {'$regex': f"^{cmd}$", '$options':'i'}
            restricted_command = await db.hasrole.find_one({"guildid":ctx.guild_id, "command":regx})
            if restricted_command is not None:
                r_role = ctx.guild.get_role(restricted_command.role)
                return await ctx.send(f'`{cmd}` already restricted to {r_role.mention}')
            await db.hasrole(guildid=ctx.guild_id, command=cmd, role=role.id).insert()
            await ctx.send(embed=Embed(color=0x0c73d3,description=f'`{cmd}` restricted to {role.mention}'))
    
    @slash_command(name='command', sub_cmd_name='unrestrict', sub_cmd_description='Lift a command role restriction', scopes=[435038183231848449, 149167686159564800])
    @slash_option(name='command_name', description='Type the command to restrict', opt_type=OptionTypes.STRING, required=True)
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def temp_unrestrict_cmd(self, ctx: InteractionContext, command_name:str=None):
        cmd = command_name
        if cmd is None:
            return await ctx.send(':x: You have to include a command name', ephemeral=True)

        if cmd.lower() in all_commands:
            
            
            regx = {'$regex': f"^{cmd}$", '$options':'i'}
            restricted_command = await db.hasrole.find_one({"guildid":ctx.guild_id, "command":regx})
            if restricted_command is None:
                return await ctx.send(f'`{cmd}` not restricted')
            await restricted_command.delete()
            await ctx.send(embed=Embed(color=0x0c73d3,description=f'Restriction lifted from `{cmd}`'))

    @slash_command("echo", description="echo your messages")
    @text()
    @channel()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def echo(self, ctx: InteractionContext, text: str, channel:OptionTypes.CHANNEL=None):
        if (channel is None):
            channel = ctx.channel
        await channel.send(text)
        message = await ctx.send(f'{ctx.author.mention} message `{text}` in {channel.mention} echoed!', ephemeral=True)
        #await channel.delete_message(message, 'message for echo command')
    
    @slash_command(name='userinfo', description="lets me see info about server members")
    @member()
    async def userinfo(self, ctx:InteractionContext, member:OptionTypes.USER=None):
        
        if member is None:
            member = ctx.author

        if member.top_role.name != '@everyone':
            toprole = member.top_role.mention
        else:
            toprole = 'None'

        roles = [role.mention for role in member.roles if role.name != '@everyone']
        rolecount = len(roles)
        if rolecount == 0:
            roles = 'None'
        else:
            roles = ' '.join(roles)

        if member.top_role.color.value == 0:
            color = 0x0c73d3
        else:
            color = member.top_role.color
        
        cdiff = relativedelta(datetime.now(tz=timezone.utc), member.created_at.replace(tzinfo=timezone.utc))
        creation_time = f"{cdiff.years} Y, {cdiff.months} M, {cdiff.days} D"

        jdiff = relativedelta(datetime.now(tz=timezone.utc), member.joined_at.replace(tzinfo=timezone.utc))
        join_time = f"{jdiff.years} Y, {jdiff.months} M, {jdiff.days} D"

        if member.guild_avatar is not None:
            avatarurl = f'{member.guild_avatar.url}.png'
        else:
            avatarurl = f'{member.avatar.url}.png'

        embed = Embed(color=color,
                      title=f"User Info - {member}")
        embed.set_thumbnail(url=avatarurl)
        embed.add_field(name="ID(snowflake):", value=member.id, inline=False)
        embed.add_field(name="Nickname:", value=member.display_name, inline=False)
        embed.add_field(name="Created account on:", value=f"<t:{math.ceil(member.created_at.timestamp())}> `{creation_time} ago`", inline=False)
        embed.add_field(name="Joined server on:", value=f"<t:{math.ceil(member.joined_at.timestamp())}> `{join_time} ago`", inline=False)
        embed.add_field(name=f"Roles: [{rolecount}]", value=roles, inline=False)
        embed.add_field(name="Highest role:", value=toprole, inline=False)
        await ctx.send(embed=embed)
    
    @slash_command(name='serverinfo', description="lets me see info about the server")
    async def serverinfo(self, ctx:InteractionContext):
        cdiff = relativedelta(datetime.now(tz=timezone.utc), ctx.guild.created_at.replace(tzinfo=timezone.utc))
        creation_time = f"{cdiff.years} Y, {cdiff.months} M, {cdiff.days} D"
        owner = await guild_owner(ctx)
        embed = Embed(title=f"Server Info", color=0x0c73d3)
        embed.set_author(name=f'{ctx.guild.name}', icon_url=f'{ctx.guild.icon.url}')
        embed.set_thumbnail(url=f'{ctx.guild.icon.url}')
        embed.add_field(name='Server owner', value=f'{owner.mention}', inline=False)
        embed.add_field(name='Members', value=f'{ctx.guild.member_count}', inline=False)
        embed.add_field(name="Channels:", value=len(ctx.guild.channels), inline=False)
        embed.add_field(name="Roles:", value=len(ctx.guild.roles), inline=False)
        embed.add_field(name='Boost level', value=f'{ctx.guild.premium_tier}[{ctx.guild.premium_subscription_count} boosts]', inline=False)
        embed.add_field(name='Created at', value=f'<t:{math.ceil(ctx.guild.created_at.timestamp())}> `{creation_time} ago`', inline=False)
        embed.add_field(name='Region', value=f'{ctx.guild.preferred_locale}', inline=False)
        embed.add_field(name='ID', value=f'{ctx.guild_id}', inline=True)
        await ctx.send(embed=embed)
    
    @slash_command(name='botinfo', description="lets me see info about the bot")
    async def botinfo(self, ctx: InteractionContext):
        member = ctx.guild.get_member(self.bot.user.id)

        if member.top_role.name != '@everyone':
            toprole = member.top_role.mention
        else:
            toprole = 'None'

        roles = [role.mention for role in member.roles if role.name != '@everyone']
        rolecount = len(roles)
        if rolecount == 0:
            roles = 'None'
        else:
            roles = ' '.join(roles)

        if member.top_role.color.value == 0:
            color = 0x0c73d3
        else:
            color = member.top_role.color
        
        cdiff = relativedelta(datetime.now(tz=timezone.utc), member.created_at.replace(tzinfo=timezone.utc))
        creation_time = f"{cdiff.years} Y, {cdiff.months} M, {cdiff.days} D"

        jdiff = relativedelta(datetime.now(tz=timezone.utc), member.joined_at.replace(tzinfo=timezone.utc))
        join_time = f"{jdiff.years} Y, {jdiff.months} M, {jdiff.days} D"

        if member.guild_avatar is not None:
            avatarurl = f'{member.guild_avatar.url}.png'
        else:
            avatarurl = f'{member.avatar.url}.png'

        embed = Embed(color=color,
                      title=f"Bot Info - {member}")
        embed.set_thumbnail(url=avatarurl)
        #embed.set_author(name=member, icon_url=member.avatar.url)
        embed.add_field(name="ID(snowflake):", value=member.id, inline=False)
        embed.add_field(name="Nickname:", value=member.display_name, inline=False)
        embed.add_field(name="Created account on:", value=f"<t:{math.ceil(member.created_at.timestamp())}> `{creation_time} ago`", inline=False)
        embed.add_field(name="Joined server on:", value=f"<t:{math.ceil(member.joined_at.timestamp())}> `{join_time} ago`", inline=False)
        embed.add_field(name=f"Roles: [{rolecount}]", value=roles, inline=False)
        embed.add_field(name="Highest role:", value=toprole, inline=False)
        embed.add_field(name="Library:", value="[dis-snek](https://dis-snek.readthedocs.io/)")
        embed.add_field(name="Servers:", value=len(self.bot.user.guilds))
        embed.add_field(name="Bot Latency:", value=f"{self.bot.latency * 1000:.0f} ms")
        embed.add_field(name='GitHub: https://github.com/siren15/pinetree-dis-snek', value='‎')
        embed.set_footer(text="pinetree | Powered by Sneks")
        await ctx.send(embed=embed)
    
    @slash_command(name='avatar', description="Show's you your avatar, or members, if provided")
    @member()
    async def avatar(self, ctx:InteractionContext, member:OptionTypes.USER=None):
        
        if member is None:
            member = ctx.author
        
        if member.guild_avatar is not None:
            avatarurl = member.guild_avatar.url
        else:
            avatarurl = member.avatar.url
        
        embed = Embed(description=member.display_name, color=0x0c73d3)
        embed.set_image(url=avatarurl)
        await ctx.send(embed=embed)

    @slash_command(name='useravatar', description="Show's you your avatar, or users, if provided")
    @member()
    async def useravatar(self, ctx:InteractionContext, member:OptionTypes.USER=None):
        
        if member is None:
            member = ctx.author

        avatarurl = member.avatar.url
        
        embed = Embed(description=member.display_name, color=0x0c73d3)
        embed.set_image(url=avatarurl)
        await ctx.send(embed=embed)
    
    @slash_command(name='ping', description="Ping! Pong!")
    async def ping(self, ctx:InteractionContext):
        
        await ctx.send(f"Pong! \nBot's latency: {self.bot.latency * 1000} ms")
    
    @slash_command(name='embed', sub_cmd_name='create' , sub_cmd_description='[admin]Create embeds', description="[admin]Create and edit embeds")
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def embed(self, ctx:InteractionContext):
        from dis_snek.models.discord import modal
        m = modal.Modal(title='Create an embed', components=[
            modal.InputText(
                label="Embed Title",
                style=modal.TextStyles.SHORT,
                custom_id=f'embed_title',
                required=False
            ),
            modal.InputText(
                label="Embed Text",
                style=modal.TextStyles.PARAGRAPH,
                custom_id=f'embed_text',
                required=False
            )
        ],
        custom_id=f'{ctx.author.id}_embed_modal'
        )
        await ctx.send_modal(modal=m)
        try:
            modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
        except asyncio.TimeoutError:
            return await ctx.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond.", ephemeral=True)
        
        embed_title = modal_recived.responses.get('embed_title')
        embed_text = modal_recived.responses.get('embed_text')
        if (embed_title is None) and (embed_text is None):
            await ctx.send('You must include either embed title or text', ephemeral=True)
            return
        embed=Embed(color=0x0c73d3,
        description=embed_text,
        title=embed_title)
        await modal_recived.send(embed=embed)

    @embed.subcommand(sub_cmd_name='edit' ,sub_cmd_description='[admin]Edit embeds')
    @embed_message_id()
    @channel()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def embed_edit(self, ctx:InteractionContext, embed_message_id:str=None, channel:OptionTypes.CHANNEL=None):
        if embed_message_id is None:
            await ctx.send('You have to include the embed message ID, so that I can edit the embed', ephemeral=True)
            return
        elif channel is None:
            channel = ctx.channel
        from dis_snek.models.discord import modal
        m = modal.Modal(title='Create an embed', components=[
            modal.InputText(
                label="Embed Title",
                style=modal.TextStyles.SHORT,
                custom_id=f'embed_title',
                required=False
            ),
            modal.InputText(
                label="Embed Text",
                style=modal.TextStyles.PARAGRAPH,
                custom_id=f'embed_text',
                required=False
            )
        ],
        custom_id=f'{ctx.author.id}_embed_modal'
        )

        await ctx.send_modal(modal=m)

        try:
            modal_recived: ModalContext = await self.bot.wait_for_modal(modal=m, author=ctx.author.id, timeout=600)
        except asyncio.TimeoutError:
            return await ctx.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 10 minutes to respond.", ephemeral=True)
        
        embed_title = modal_recived.responses.get('embed_title')
        embed_text = modal_recived.responses.get('embed_text')
        if (embed_title is None) and (embed_text is None):
            await ctx.send('You must include either embed title or text', ephemeral=True)
            return
        message_to_edit = channel.get_message(embed_message_id)
        embed=Embed(color=0x0c73d3,
        description=embed_text,
        title=embed_title)
        await message_to_edit.edit(embed=embed)
        await modal_recived.send('Message edited', ephemeral=True)

def setup(bot):
    Basic(bot)