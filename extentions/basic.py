import re

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.discord import DiscordObject
from dis_snek.models.scale import Scale
from dis_snek.models.enums import Permissions
from dis_snek import Snake, slash_command, InteractionContext, slash_option, OptionTypes
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *


class Basic(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot

    @slash_command("echo", description="echo your messages", scopes=[435038183231848449, 149167686159564800])
    @text()
    @channel()
    async def echo(self, ctx: InteractionContext, text: str, channel:OptionTypes.CHANNEL=None):
        perms = await has_perms(ctx.author, Permissions.ADMINISTRATOR)
        if (perms == True):
            if (channel is None):
                channel = ctx.channel
            await channel.send(text)
            message = await ctx.send(f'{ctx.author.mention} message `{text}` in {channel.mention} echoed!', ephemeral=True)
            #await channel.delete_message(message, 'message for echo command')
    
    @slash_command(name='userinfo', description="let's me see info about server members", scopes=[435038183231848449, 149167686159564800])
    @member()
    async def userinfo(self, ctx:InteractionContext, member:OptionTypes.USER=None):
        await ctx.defer()
        if member == None:
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

        embed = Embed(color=color,
                      title=f"User Info - {member}")
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="ID(snowflake):", value=member.id, inline=False)
        embed.add_field(name="Nickname:", value=member.display_name, inline=False)
        embed.add_field(name="Created account on:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC")+f" [{creation_time}]", inline=False)
        embed.add_field(name="Joined server on:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC")+f" [{join_time}]", inline=False)
        embed.add_field(name=f"Roles: [{rolecount}]", value=roles, inline=False)
        embed.add_field(name="Highest role:", value=toprole, inline=False)
        await ctx.send(embed=embed)
    
    @slash_command(name='botinfo', description="let's me see info about the bot", scopes=[435038183231848449, 149167686159564800])
    async def botinfo(self, ctx: InteractionContext):
        await ctx.defer()
        def getmember(ctx):
            members = ctx.guild.members
            for m in members:
                if m.id == self.bot.user.id:
                    return m
            return None

        member = getmember(ctx)

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

        embed = Embed(color=color,
                      title=f"Bot Info - {member}")
        embed.set_thumbnail(url=member.avatar.url)
        #embed.set_author(name=member, icon_url=member.avatar.url)
        embed.add_field(name="ID(snowflake):", value=member.id, inline=False)
        embed.add_field(name="Nickname:", value=member.display_name, inline=False)
        embed.add_field(name="Created account on:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC")+f" [{creation_time}]", inline=False)
        embed.add_field(name="Joined server on:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC")+f" [{join_time}]", inline=False)
        embed.add_field(name=f"Roles: [{rolecount}]", value=roles, inline=False)
        embed.add_field(name="Highest role:", value=toprole, inline=False)
        embed.add_field(name="Library:", value="[dis-snek](https://dis-snek.readthedocs.io/)")
        embed.add_field(name="Servers:", value=len(self.bot.user.guilds))
        embed.add_field(name="Bot Latency:", value=f"{self.bot.ws.latency * 1000:.0f} ms")
        embed.add_field(name='[GitHub](https://github.com/siren15/pinetree-dis-snek)', value='‎')
        embed.set_footer(text=".GIFfany-bot | Powered by Sneks")
        await ctx.send(embed=embed)
    
    @slash_command(name='avatar', description="Show's you your avatar, or members, if provided", scopes=[435038183231848449, 149167686159564800])
    @member()
    async def avatar(self, ctx:InteractionContext, member:OptionTypes.USER=None):
        await ctx.defer()
        if member == None:
            member = ctx.author
        embed = Embed(color=0x0c73d3)
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)
    
    @slash_command(name='ping', description="Ping! Pong!", scopes=[435038183231848449, 149167686159564800])
    async def ping(self, ctx:InteractionContext):
        await ctx.defer()
        await ctx.send(f"Pong! \nBot's latency: {self.bot.ws.latency * 1000:.0f} ms")
    
    @slash_command(name='embed', sub_cmd_name='create' , sub_cmd_description='[admin]Create embeds', description="[admin]Create and edit embeds", scopes=[435038183231848449, 149167686159564800])
    @embed_title()
    @embed_text()
    async def embed(self, ctx:InteractionContext, embed_title:str=None, embed_text:str=None):
        perms = await has_perms(ctx.author, Permissions.ADMINISTRATOR)
        if (perms == True):
            if (embed_title == None) and (embed_text == None):
                await ctx.send('You must include either embed title or text', ephemeral=True)
                return
            embed=Embed(color=0x0c73d3,
            description=embed_text,
            title=embed_title)
            await ctx.send(embed=embed)

    @embed.subcommand(sub_cmd_name='edit' ,sub_cmd_description='[admin]Edit embeds')
    @embed_title()
    @embed_text()
    @embed_message_id()
    @channel()
    async def embed_edit(self, ctx:InteractionContext, embed_message_id:int=None, embed_title:str=None, embed_text:str=None, channel:OptionTypes.CHANNEL=None):
        perms = await has_perms(ctx.author, Permissions.ADMINISTRATOR)
        if (perms == True):
            if embed_message_id == None:
                await ctx.send('You have to include the embed message ID, so that I can edit the embed', ephemeral=True)
                return
            elif (embed_title == None) and (embed_text == None):
                await ctx.send('You must include either embed title or text', ephemeral=True)
                return
            elif channel == None:
                channel = ctx.channel
            message_to_edit = await channel.get_message(embed_message_id)
            if message_to_edit.id == embed_message_id:
                embed=Embed(color=0x0c73d3,
            description=embed_text,
            title=embed_title)
            await channel.message_to_edit.edit(embed=embed)
            await ctx.send('Message edited', ephemeral=True)


def setup(bot):
    Basic(bot)