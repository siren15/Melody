import asyncio
from datetime import datetime, timezone
import math
from dateutil.relativedelta import relativedelta
from naff import Client, Extension, Permissions, Embed, slash_command, InteractionContext, OptionTypes, check, ModalContext, Guild, listen, SlashCommand, modal
from naff.models.naff.tasks import Task
from naff.models.naff.tasks.triggers import IntervalTrigger
from utils.slash_options import *
from utils.customchecks import *
from duckpy import AsyncClient
from naff.client.const import MISSING

duckduckgo = AsyncClient()

all_commands = ['echo', 'userinfo', 'botinfo', 'avatar', 'useravatar', 'embed create', 'embed edit', 't', 'tag recall', 'tag create', 'tag edit', 'tag delete', 'tag claim', 'tag list', 'tag aedit', 'tag gift', 'tag info', 'ban', 'mute', 'delete', 'kick', 'unban', 'warn add', 'warn remove', 'limbo', 'userpurge', 'warnings', 'strikes', 'rank', 'ranklist', 'leveling addrole', 'leveling removerole', 'leaderboard', 'giveyou _', 'giveyou create', 'giveyou delete', 'giveyou list', 'uptime', 'reactionrole create', 'reactionrole delete']

async def guild_owner(ctx) -> bool:
    members = [m for m in ctx.guild.members]
    for member in members:
        if ctx.guild.is_owner(member) == True:
            return member


class Basic(Extension):
    def __init__(self, bot: Client):
        self.bot = bot

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
            color = 0xffcc50
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
        embed = Embed(title=f"Server Info", color=0xffcc50)
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
            color = 0xffcc50
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
        embed.add_field(name="Library:", value="[NAFF](https://naff.info/)")
        embed.add_field(name="Servers:", value=len(self.bot.user.guilds))
        embed.add_field(name="Bot Latency:", value=f"{self.bot.latency * 1000:.0f} ms")
        embed.add_field(name='GitHub: https://github.com/siren15/melody', value='‎')
        embed.set_footer(text="Melody | powered by NAFF")
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
        
        embed = Embed(description=member.display_name, color=0xffcc50)
        embed.set_image(url=avatarurl)
        await ctx.send(embed=embed)

    @slash_command(name='useravatar', description="Show's you your avatar, or users, if provided")
    @member()
    async def useravatar(self, ctx:InteractionContext, member:OptionTypes.USER=None):
        
        if member is None:
            member = ctx.author

        avatarurl = member.avatar.url
        
        embed = Embed(description=member.display_name, color=0xffcc50)
        embed.set_image(url=avatarurl)
        await ctx.send(embed=embed)
    
    @slash_command(name='search', description="Search with DuckDuckGo, returns the first result.")
    @text()
    async def duckduckgosearch(self, ctx:InteractionContext, text: str):
        await ctx.defer()
        results = await duckduckgo.search(text)
        embed = Embed(
            title=results[0].title,
            description=results[0].description,
            color=0xdb4b26
        )
        embed.set_footer(text=results[0].url)
        await ctx.send(embed=embed)
    
    @slash_command(name='ping', description="Ping! Pong!")
    async def ping(self, ctx:InteractionContext):
        
        await ctx.send(f"Pong! \nBot's latency: {self.bot.latency * 1000} ms")
    
    create_embed = SlashCommand(name='embed', description='Create and edit embeds.', default_member_permissions=Permissions.ADMINISTRATOR)
    
    @create_embed.subcommand(sub_cmd_name='create', sub_cmd_description='Create embeds')
    async def embed(self, ctx:InteractionContext):
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
            ),
            modal.InputText(
                label="Embed Image",
                style=modal.TextStyles.SHORT,
                custom_id=f'embed_image',
                required=False,
                placeholder='Image URL'
            ),
            modal.InputText(
                label="Embed Colour",
                style=modal.TextStyles.SHORT,
                custom_id=f'embed_colour',
                required=False,
                placeholder='Colour HEX code'
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
        if embed_title is None:
            embed_title = MISSING
        embed_text = modal_recived.responses.get('embed_text')
        if embed_text is None:
            embed_text = MISSING
        embed_image = modal_recived.responses.get('embed_image')
        if embed_image is None:
            embed_image = MISSING
        if (embed_title is None) and (embed_text is None):
            await ctx.send('You must include either embed title or text', ephemeral=True)
            return
        embed_colour = modal_recived.responses.get('embed_colour')
        if embed_colour is None or embed_colour == '':
            embed_colour = 0xffcc50
        else:
            from utils import utils
            if not utils.is_hex_valid(embed_colour):
                await modal_recived.send('Colour HEX not valid. Using default embed colour.', ephemeral=True)
                embed_colour = 0xffcc50
        embed=Embed(color=embed_colour,
        description=embed_text,
        title=embed_title)
        embed.set_image(embed_image)
        await modal_recived.send(embed=embed)

    @create_embed.subcommand(sub_cmd_name='edit', sub_cmd_description='Edit embeds')
    @embed_message_id()
    @channel()
    async def embed_edit(self, ctx:InteractionContext, embed_message_id:str=None, channel:OptionTypes.CHANNEL=None):
        if embed_message_id is None:
            await ctx.send('You have to include the embed message ID, so that I can edit the embed', ephemeral=True)
            return
        elif channel is None:
            channel = ctx.channel
        from naff.models.discord import modal
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
            ),
            modal.InputText(
                label="Embed Image",
                style=modal.TextStyles.SHORT,
                custom_id=f'embed_image',
                required=False,
                placeholder='Image URL'
            ),
            modal.InputText(
                label="Embed Colour",
                style=modal.TextStyles.SHORT,
                custom_id=f'embed_colour',
                required=False,
                placeholder='Colour HEX code'
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
        if embed_title is None:
            embed_title = MISSING
        embed_text = modal_recived.responses.get('embed_text')
        if embed_text is None:
            embed_text = MISSING
        embed_image = modal_recived.responses.get('embed_image')
        if embed_image is None:
            embed_image = MISSING
        if (embed_title is None) and (embed_text is None):
            await ctx.send('You must include either embed title or text', ephemeral=True)
            return
        embed_colour = modal_recived.responses.get('embed_colour')
        if embed_colour is None:
            embed_colour = 0xffcc50
        else:
            from utils import utils
            if not utils.is_hex_valid(embed_colour):
                await modal_recived.send('Colour HEX not valid. Using default embed colour.', ephemeral=True)
                embed_colour = 0xffcc50
        message_to_edit = await channel.fetch_message(embed_message_id)
        embed=Embed(color=embed_colour,
        description=embed_text,
        title=embed_title)
        embed.set_image(embed_image)
        await message_to_edit.edit(embed=embed)
        await modal_recived.send('Message edited', ephemeral=True)

import os
from importlib import import_module
from inspect import isclass
from naff import ComponentContext, Button, ButtonStyles, ActionRow, spread_to_rows, errors
from naff.api.events.internal import Component
from inspect import getmembers

def get_commands():
    """Goes through extensions folder and returns a list of Extensions.
    Return class names and path.
    """
    commands = []
    command_path = ""
    for root, dirs, files in os.walk('extentions'):
        for file in files:
            if file.endswith(".py") and not file.startswith("__init__") and not file.startswith("__"):
                file = file.removesuffix(".py")
                path = os.path.join(root, file)
                command_path = path.replace("/", ".").replace("\\", ".")
                modname = import_module(command_path)
                for name, obj in getmembers(modname):
                    if isclass(obj) and issubclass(obj, Extension):
                        if obj.__name__ == "Extension":
                            continue
                        else:
                            commands.append((obj.__name__, command_path))
    return commands
   
class Update(Extension):
    from naff.models.naff.checks import is_owner
    @slash_command(
        "reloader",
        description="Reloads an extension.",
        scopes=[435038183231848449, 149167686159564800],
        default_member_permissions=Permissions.ADMINISTRATOR
    )
    @check(is_owner())
    async def _reloader(self, ctx: ComponentContext):
        await ctx.defer(ephemeral=True)
        commands = get_commands()
        command_buttons = []

        try:
            for command in commands:
               command_buttons.append(
                Button(
                    style=ButtonStyles.BLURPLE,
                    label=command[0],
                    custom_id=command[0],
                )
               )
               
            component: list[ActionRow] = spread_to_rows(*command_buttons)
            await ctx.send("Select Extension", components=component)          
        except Exception as e:
            print(e)

    @listen()
    async def on_component(self, event: Component):
        ctx = event.ctx
        await ctx.defer(edit_origin=True)
        embed = Embed(title="Extension Reloader", color=0x808080)
        command_list = get_commands()
        for command in command_list:
            if command[0] == ctx.custom_id:
                try:
                    self.bot.reload_extension(command[1])
                    embed.add_field("Reloaded Extension", value=f"**{ctx.custom_id}**", inline=False)
                    await ctx.edit_origin(embeds=[embed], components=[])
                    return
                except errors.ExtensionNotFound:
                    pass
                except errors.ExtensionLoadException:
                    await ctx.edit_origin(f"Failed to reload {ctx.custom_id}", components=[])

def setup(bot):
    Basic(bot)
    Update(bot)