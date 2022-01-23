import re
import asyncio

from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone
from dis_snek.models.discord.components import ActionRow, Button, spread_to_rows
from dis_snek.models.discord.enums import ButtonStyles
from dis_snek.models.snek.scale import Scale
from dis_snek import Snake, slash_command, InteractionContext,  OptionTypes
from dis_snek.models.discord.embed import Embed
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *

def geturl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    return [x[0] for x in url]

def checktagowner(guild, userid):
    members = guild.members
    for m in members:
        if m.id == userid:
            return m
    return None

class Tags(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @slash_command(name='t', description="allow's me to recall tags")
    @tagname()
    async def t(self, ctx:InteractionContext, tagname:str):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            db = await odm.connect()
            regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tags = await db.find_one(tag, {"names":regx, "guild_id":ctx.guild_id})
            if tags == None:
                embed = Embed(
                    description=f":x: `{tagname}` is not a tag",
                    color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(tags.content)
                uses = tags.no_of_times_used
                if uses == None:
                    uses = 0
                else:
                    uses = tags.no_of_times_used
                tags.no_of_times_used = uses + 1
                await db.save(tags)

    @slash_command(name='tag', sub_cmd_name='recall', sub_cmd_description="allow's me to recall tags")
    @tagname()
    async def tag(self, ctx:InteractionContext, tagname:str):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            db = await odm.connect()
            regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tags = await db.find_one(tag, {"names":regx, "guild_id":ctx.guild_id})
            if tags == None:
                embed = Embed(
                    description=f":x: `{tagname}` is not a tag",
                    color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(tags.content)
                uses = tags.no_of_times_used
                if uses == None:
                    uses = 0
                else:
                    uses = tags.no_of_times_used
                tags.no_of_times_used = uses + 1
                await db.save(tags)

    @slash_command(name='tag', sub_cmd_name='create', sub_cmd_description="allow's me to store tags")
    @tagname()
    @content()
    async def tag_create(self, ctx:InteractionContext, tagname:str=None, content:str=None):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            if tagname == None:
                embed = Embed(description=f":x: You must include tag's name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            elif (content == None) and (ctx.attachments == None):
                embed = Embed(description=f":x: You must include tag's content",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            elif (tagname == None) and (content == None):
                embed = Embed(description=f":x: You must include tag's name and content",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            db = await odm.connect()
            tagname_regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            check = await db.find_one(tag, {'guild_id':ctx.guild_id, 'names':tagname_regx})
            if check==None:
                await db.save(tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, creation_date=datetime.utcnow()))
                url = geturl(content)
                for url in url:
                    url = url
                if url:
                    embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:**{content}",
                                color=0x0c73d3)
                    embed.set_image(url=url)
                    await ctx.send(embed=embed)
                else:
                    embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:** \n{content}",
                                color=0x0c73d3)
                    await ctx.send(embed=embed)
            else:
                embed = Embed(description=f":x: The tag `{tagname}` already exists",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
    
    @slash_command(name='tag', sub_cmd_name='delete', sub_cmd_description="allow's me to delete tags that you own")
    @tagname()
    async def tag_delete(self, ctx:InteractionContext, tagname:str=None):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            if tagname == None:
                embed = Embed(description=f":x: You must include tag's name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

            db = await odm.connect()
            tagname_regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tag_to_delete = await db.find_one(tag, {'guild_id':ctx.guild_id, 'names':tagname_regx, 'author':ctx.author.id})
            if tag_to_delete == None:
                embed = Embed(description=f":x: You don't own a tag called  `{tagname}`",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            url = geturl(tag_to_delete.content)
            for url in url:
                url = url
            if url:
                embed = Embed(description=f"__**Tag deleted!**__ \n\n**Tag's name:** {tag_to_delete.names} \n**Tag's content:**{tag_to_delete.content}",
                            color=0x0c73d3)
                embed.set_image(url=url)
                await ctx.send(embed=embed)
                await db.delete(tag_to_delete)
            else:
                embed = Embed(description=f"__**Tag deleted!**__ \n\n**Tag's name:** {tag_to_delete.names} \n**Tag's content:**{tag_to_delete.content}",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
                await db.delete(tag_to_delete)
    
    @slash_command(name='tag', sub_cmd_name='admindelete', sub_cmd_description="[ADMIN ONLY]allow's me to delete any tag")
    @tagname()
    async def tag_admin_delete(self, ctx:InteractionContext, tagname:str=None):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            if tagname == None:
                embed = Embed(description=f":x: You must include tag's name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

            db = await odm.connect()
            tagname_regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tag_to_delete = await db.find_one(tag, {'guild_id':ctx.guild_id, 'names':tagname_regx})
            if tag_to_delete == None:
                embed = Embed(description=f":x: You don't own a tag called  `{tagname}`",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            url = geturl(tag_to_delete.content)
            for url in url:
                url = url
            if url:
                embed = Embed(description=f"__**Tag deleted!**__ \n\n**Tag's name:** {tag_to_delete.names} \n**Tag's content:**{tag_to_delete.content}",
                            color=0x0c73d3)
                embed.set_image(url=url)
                await ctx.send(embed=embed)
                await db.delete(tag_to_delete)
            else:
                embed = Embed(description=f"__**Tag deleted!**__ \n\n**Tag's name:** {tag_to_delete.names} \n**Tag's content:**{tag_to_delete.content}",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
                await db.delete(tag_to_delete)

    @slash_command(name='tag', sub_cmd_name='edit', sub_cmd_description="allow's me to delete tags that you own")
    @tagname()
    @content()
    async def tag_edit(self, ctx:InteractionContext, tagname:str=None, content:str=None):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            if tagname == None:
                embed = Embed(description=f":x: You must include tag's name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

            db = await odm.connect()
            tagname_regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tag_to_edit = await db.find_one(tag, {'guild_id':ctx.guild_id, 'names':tagname_regx, 'author':ctx.author.id})
            if tag_to_edit == None:
                embed = Embed(description=f":x: You don't own a tag called  `{tagname}`",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            tag_to_edit.content = content
            await db.save(tag_to_edit)
            url = geturl(content)
            for url in url:
                url = url
            if url:
                embed = Embed(description=f"__**Tag edited!**__ \n\n**Tag's name:** {tag_to_edit.names} \n**Tag's new content:**{content}",
                            color=0x0c73d3)
                embed.set_image(url=url)
                await ctx.send(embed=embed)
            else:
                embed = Embed(description=f"__**Tag edited!**__ \n\n**Tag's name:** {tag_to_edit.names} \n**Tag's new content:**{content}",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
    
    @slash_command(name='tag', sub_cmd_name='info', sub_cmd_description="allow's me to see information about a tag")
    @tagname()
    async def tag_info(self, ctx:InteractionContext, tagname:str=None):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            if tagname == None:
                embed = Embed(description=f":x: You must include tag's name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

            db = await odm.connect()
            tagname_regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tag_to_view = await db.find_one(tag, {'guild_id':ctx.guild_id, 'names':tagname_regx})
            if tag_to_view == None:
                embed = Embed(description=f":x: I couldn't find a tag called `{tagname}`",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

            if tag_to_view.owner_id != None:
                tag_owner = await self.bot.get_user(tag_to_view.owner_id)
            else:
                tag_owner = 'UNKNOWN'

            current_owner = 'Current owner'
            last_owner = tag_owner

            in_guild = checktagowner(ctx.guild, tag_to_view.owner_id)
            if in_guild == None:
                current_owner = 'Currently Orphaned'
                last_owner = f'Last owner: {tag_owner}'
            
            total_uses = tag_to_view.no_of_times_used
            uses = total_uses

            if total_uses == None:
                uses = 'UNKNOWN'

            creation_date = tag_to_view.creation_date
            if creation_date == None:
                date = 'UNKNOWN'
            else:
                cdiff = relativedelta(datetime.now(tz=timezone.utc), tag_to_view.creation_date.replace(tzinfo=timezone.utc))
                creation_time = f"{cdiff.years} Y, {cdiff.months} M, {cdiff.days} D"
                date = tag_to_view.creation_date.strftime("%a, %#d %B %Y, %I:%M %p UTC")+f' [{creation_time}]'

            embed = Embed(title=f"Info about [{tag_to_view.names}] tag",
                        color=0x0c73d3)
            embed.add_field(name=current_owner, value=last_owner)
            embed.add_field(name="Total uses", value=uses)
            embed.add_field(name="Created", value=date)
            embed.add_field(name="Content", value=tag_to_view.content)
            await ctx.send(embed=embed)
    
    @slash_command(name='tag', sub_cmd_name='list', sub_cmd_description="allow's me to see all tags for this server")
    async def tag_list(self, ctx:InteractionContext):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            from dis_snek.ext.paginators import Paginator
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

            def newpage(title, names):
                embed = Embed(title=title,
                color=0x0c73d3)
                embed.add_field(name='Tag Names', value=names, inline=True)
                return embed

            db = await odm.connect()
            tag_names = await db.find(tag, {"guild_id":ctx.guild_id})
            
            if tag_names == None:
                embed = Embed(description=f"There are no tags for {ctx.guild}.",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
                return

            names = [str(name.names)+"\n" for name in tag_names if name.names != None]

            s = -1
            e = 0
            embedcount = 1
            nc = list(chunks(names, 20))
            
            embeds = []
            while embedcount <= len(nc):
                s = s+1
                e = e+1
                embeds.append(newpage(f'List of tags for {ctx.guild.name}', mlis(names, s, e)))
                embedcount = embedcount+1
                
            paginator = Paginator(
                client=self.bot, 
                pages=embeds,
                timeout_interval=80,
                show_select_menu=False,
                wrong_user_message="You're not the one destined for this list.")
            await paginator.send(ctx)
                
    
    @slash_command(name='tag', sub_cmd_name='claim', sub_cmd_description="claim orphaned tags")
    @tagname()
    async def tag_claim(self, ctx:InteractionContext, tagname:str=None):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            if tagname == None:
                embed = Embed(description=f":x: You must include tag's name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

            db = await odm.connect()
            tagname_regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tag_to_claim = await db.find_one(tag, {'guild_id':ctx.guild_id, 'names':tagname_regx})
            if tag_to_claim.owner_id == ctx.author.id:
                embed = Embed(description=f":x: You can't claim a tag you already own",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            if checktagowner(ctx.guild, tag_to_claim.owner_id) == None:
                tag_to_claim.owner_id = ctx.author.id
                await db.save(tag_to_claim)
                embed = Embed(description=f"{ctx.author.mention} You are now owner of {tag_to_claim.names}",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
            else:
                embed = Embed(description=f":x: You can't claim a tag that's not orphaned",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)

    @slash_command(name='tag', sub_cmd_name='gift', sub_cmd_description="gift your tags")
    @tagname()
    @member()
    async def tag_gift(self, ctx:InteractionContext, tagname:str=None, member:OptionTypes.USER=None):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            if tagname == None:
                embed = Embed(description=f":x: You must include tag's name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            if member == None:
                embed = Embed(description=f":x: You must include a member",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            if member == ctx.author:
                embed = Embed(description=f":x: You can't gift to yourself, egomaniac...",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

            db = await odm.connect()
            tagname_regx = re.compile(f"^{tagname}$", re.IGNORECASE)
            tag_to_claim = await db.find_one(tag, {'guild_id':ctx.guild_id, 'names':tagname_regx, 'owner_id':ctx.author.id})
            if tag_to_claim == None:
                embed = Embed(description=f":x: You don't own a tag with that name",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
            aceept_button_id = f'{member.id}_accept_tag_gift_button'
            cancel_button_id = f'{ctx.author.id}_accept_tag_gift_button'
            accept_button: list[ActionRow] = spread_to_rows(
                Button(
                    style=ButtonStyles.GREEN,
                    label="GIMME!",
                    custom_id=aceept_button_id
                ),
                Button(
                    style=ButtonStyles.RED,
                    label="Cancel!",
                    custom_id=cancel_button_id
                )
            )
            def check(component: Button) -> bool:
                return (component.context.author == ctx.author) or (component.context.author == member)

            gift_question = await ctx.send(f'Hey {member.mention}! {ctx.author.mention} is gifting you a {tag_to_claim.names}, do you accept the gift?', components=accept_button)
            while True:
                try:
                    reaction = await self.bot.wait_for_component(components=accept_button, timeout=30)
                except asyncio.TimeoutError:
                    accept_button[0].components[0].disabled = True
                    accept_button[0].components[1].disabled = True
                    await gift_question.edit('Time ran out to accept the gift.', components=accept_button)
                    return
                if (reaction.context.custom_id == aceept_button_id) and (member == reaction.context.author):
                    tag_to_claim.owner_id = member.id
                    await db.save(tag_to_claim)
                    accept_button[0].components[0].disabled = True
                    accept_button[0].components[1].disabled = True
                    await gift_question.edit(f'Gift for a tag {tag_to_claim.names} accepted!', components=accept_button)
                    return
                elif (reaction.context.custom_id == aceept_button_id) and (member != reaction.context.author):
                    await ctx.send(f"{reaction.context.author.mention} You can't accept gifts not menat for you!", ephemeral=True)

                if (reaction.context.custom_id == cancel_button_id) and (ctx.author == reaction.context.author):
                    accept_button[0].components[0].disabled = True
                    accept_button[0].components[1].disabled = True
                    await gift_question.edit(f'Gift for a tag {tag_to_claim.names} cancelled!', components=accept_button)
                    return
                elif (reaction.context.custom_id == cancel_button_id) and (ctx.author != reaction.context.author):
                    await ctx.send(f"{reaction.context.author.mention} Only owners can cancel gifting!", ephemeral=True)

def setup(bot):
    Tags(bot)