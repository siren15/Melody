import math
import re
import asyncio

from utils.catbox import CatBox as catbox
from datetime import datetime, timezone
from interactions import Client, Extension, SlashCommand, slash_command, InteractionContext, OptionType, Embed, Button, ButtonStyle, ActionRow, spread_to_rows, check, AutocompleteContext
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *
from rapidfuzz import fuzz, process

def geturl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    return [x[0] for x in url]

def find_member(ctx, userid):
    return ctx.guild.get_member(userid)

class Tags(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
    
    @slash_command(name='t', description="allow's me to recall tags", scopes=[435038183231848449, 149167686159564800])
    @tagname()
    async def t(self, ctx:InteractionContext, tagname:str):
        await ctx.defer()
        tags = await db.tag.find_one({"names":tagname, "guild_id":ctx.guild_id})
        if tags is None:
            embed = Embed(
                description=f":x: `{tagname}` is not a tag",
                color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
        else:
            if tags.attachment_url is not None:
                if (tags.content is not None) and (tags.content != tags.attachment_url):
                    await ctx.send(f'{tags.content}\n{tags.attachment_url}')
                else:
                    await ctx.send(f'{tags.attachment_url}')
            else:
                await ctx.send(f'{tags.content}')
            uses = tags.no_of_times_used
            if uses is None:
                uses = 0
            else:
                uses = tags.no_of_times_used
            tags.no_of_times_used = uses + 1
            await tags.save()
    
    @t.autocomplete('tagname')
    async def t_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        tags = db.tag.find({"guild_id":ctx.guild_id})
        tagnames = [tag.names async for tag in tags]
        if tagname:
            result = process.extract(tagname, tagnames, scorer=fuzz.partial_token_sort_ratio, limit=25)
            choices = [{'name':f'{t[0]}', 'value':f'{t[0]}'} for t in result if t[1] > 50]
        else:
            choices = [{'name':f'{name}', 'value':f'{name}'} for name in tagnames[:25]]
        await ctx.send(choices=choices)

    tag = SlashCommand(name='tag', description='manage tags')

    @tag.subcommand(sub_cmd_name='recall', sub_cmd_description="allow's me to recall tags")
    @tagname()
    async def tag(self, ctx:InteractionContext, tagname:str):
        """/tag recall
        Description:
            Send the content of a tag.
        
        Args:
            tagname: the tag name
        """
        await ctx.defer()
        tags = await db.tag.find_one({"names":tagname, "guild_id":ctx.guild_id})
        if tags is None:
            embed = Embed(
                description=f":x: `{tagname}` is not a tag",
                color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
        else:
            if tags.attachment_url is not None:
                if (tags.content is not None) and (tags.content != tags.attachment_url):
                    await ctx.send(f'{tags.content}\n{tags.attachment_url}')
                else:
                    await ctx.send(f'{tags.attachment_url}')
            else:
                await ctx.send(f'{tags.content}')
            uses = tags.no_of_times_used
            if uses is None:
                uses = 0
            else:
                uses = tags.no_of_times_used
            tags.no_of_times_used = uses + 1
            await tags.save()

    @tag.subcommand(sub_cmd_name='create', sub_cmd_description="allow's me to store tags")
    @slash_option(name='tagname', description='Type a name of a tag', opt_type=OptionType.STRING, required=True, autocomplete=False)
    @content()
    @attachment()
    async def tag_create(self, ctx:InteractionContext, tagname:str=None, content:str=None, attachment:OptionType.ATTACHMENT=None):
        """/tag create
        Description:
            Create tags.

        Args:
            tagname: The tag's name
            content: The content of the tag
            attachment: The attachment from the message
        """
        await ctx.defer()
        if tagname is None:
            embed = Embed(description=f":x: You must include tag's name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        elif (content is None) and (attachment is None):
            embed = Embed(description=f":x: You must include tag's content",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        elif (tagname is None) and (content is None):
            embed = Embed(description=f":x: You must include tag's name and content",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        tagname_regx = {'$regex':f'^{re.escape(tagname)}$', '$options':'i'}
        check = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx})
        if check==None:
            if attachment is not None:
                for at in ['exe', 'scr', 'cpl', 'doc', 'jar']:
                    if at in attachment.content_type:
                        return await ctx.send(f'`{at}` attachment file type is not allowed to be uploaded to our host site')
                if content is None:
                    if (attachment.content_type == 'image/png') or (attachment.content_type == 'image/jpg') or (attachment.content_type == 'image/jpeg') or (attachment.content_type == 'image/gif'):
                        image_url = catbox.url_upload(attachment.url)
                        await db.tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, attachment_url=image_url, creation_date=datetime.utcnow()).insert()
                        embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname}",
                                color=0xffcc50)
                        embed.set_image(url=image_url)
                        return await ctx.send(embed=embed)
                    else:
                        await db.tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, attachment_url=catbox.url_upload(attachment.url), creation_date=datetime.utcnow()).insert()
                        embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname}\n**Attachment:** {catbox.url_upload(attachment.url)}",
                                color=0xffcc50)
                        return await ctx.send(embed=embed)
                else:
                    if (attachment.content_type == 'image/png') or (attachment.content_type == 'image/jpg') or (attachment.content_type == 'image/jpeg') or (attachment.content_type == 'image/gif'):
                        image_url = catbox.url_upload(attachment.url)
                        await db.tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, attachment_url=image_url, creation_date=datetime.utcnow()).insert()
                        embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname}\n**Content:** {content}",
                                color=0xffcc50)
                        embed.set_image(url=image_url)
                        return await ctx.send(embed=embed)
                    else:
                        await db.tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, attachment_url=catbox.url_upload(attachment.url), creation_date=datetime.utcnow()).insert()
                        embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname}\n**Content:** {content}\n**Attachment:** {catbox.url_upload(attachment.url)}",
                                color=0xffcc50)
                        return await ctx.send(embed=embed)
            else:
                if content is not None:
                    url = geturl(content)
                    for url in url:
                        url = url
                    if url:
                        for at in ['.exe', '.scr', '.cpl', '.doc', '.jar']:
                            if url.endswith(at):
                                return await ctx.send(f'`{at}` url file type is not allowed to be stored in my database')
                        if url.endswith('.png') or url.endswith('.apng') or url.endswith('.jpg') or url.endswith('.jpeg') or url.endswith('.gif'):
                            await db.tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, attachment_url=url, creation_date=datetime.utcnow()).insert()
                            embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:**{content}",
                                        color=0xffcc50)
                            embed.set_image(url=url)
                            return await ctx.send(embed=embed)
                        else:
                            await db.tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, attachment_url=url, creation_date=datetime.utcnow()).insert()
                            embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:** \n{content}",
                                        color=0xffcc50)
                            return await ctx.send(embed=embed)
                    else:
                        await db.tag(guild_id=ctx.guild_id, author_id=ctx.author.id, owner_id=ctx.author.id, names=tagname, content=content, attachment_url=None, creation_date=datetime.utcnow()).insert()
                        embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:** \n{content}",
                                    color=0xffcc50)
                        return await ctx.send(embed=embed)
        else:
            embed = Embed(description=f":x: The tag `{tagname}` already exists",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
    
    @tag.subcommand(sub_cmd_name='delete', sub_cmd_description="allow's me to delete tags that you own")
    @tagname()
    async def tag_delete(self, ctx:InteractionContext, tagname:str=None):
        """/tag delete
        Description:
            Delete tags.

        Args:
            tagname: The tag's name
        """
        await ctx.defer()
        if tagname is None:
            embed = Embed(description=f":x: You must include tag's name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        tagname_regx = {'$regex':f'^{re.escape(tagname)}$', '$options':'i'}
        tag_to_delete = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx, 'author_id':ctx.author.id})
        if tag_to_delete is None:
            tag_to_delete = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx, 'owner_id':ctx.author.id})
            if tag_to_delete is None:
                embed = Embed(description=f":x: You don't own a tag called  `{tagname}`",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return
        content = ''
        if tag_to_delete.content is None:
            if tag_to_delete.attachment_url is not None:
                content = content + f'{tag_to_delete.attachment_url}'
        elif tag_to_delete.content is not None:
            content = content + f'{tag_to_delete.content}'
            if tag_to_delete.attachment_url is not None:
                content = content + f'\n{tag_to_delete.attachment_url}'
        embed = Embed(description=f"__**Tag deleted!**__ \n\n**Tag's name:** {tag_to_delete.names} \n**Tag's content:**{content}",
                    color=0xffcc50)
        await ctx.send(embed=embed)
        await tag_to_delete.delete()
    
    @tag.subcommand(sub_cmd_name='admindelete', sub_cmd_description="[ADMIN ONLY]allow's me to delete any tag")
    @tagname()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def tag_admin_delete(self, ctx:InteractionContext, tagname:str=None):
        """/tag admindelete
        Description:
            Delete any tags. Requires admin permission.

        Args:
            tagname: The tag's name
        """
        await ctx.defer()
        if tagname is None:
            embed = Embed(description=f":x: You must include tag's name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        tagname_regx = {'$regex':f'^{re.escape(tagname)}$', '$options':'i'}
        tag_to_delete = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx})
        if tag_to_delete is None:
            embed = Embed(description=f":x: There's not a tag with the name `{tagname}`",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        content = ''
        if tag_to_delete.content is None:
            if tag_to_delete.attachment_url is not None:
                content = content + f'{tag_to_delete.attachment_url}'
        elif tag_to_delete.content is not None:
            content = content + f'{tag_to_delete.content}'
            if tag_to_delete.attachment_url is not None:
                content = content + f'\n{tag_to_delete.attachment_url}'
        embed = Embed(description=f"__**Tag deleted!**__ \n\n**Tag's name:** {tag_to_delete.names} \n**Tag's content:**{content}",
                    color=0xffcc50)
        await ctx.send(embed=embed)
        await tag_to_delete.delete()

    @tag.subcommand(sub_cmd_name='edit', sub_cmd_description="allow's me to delete tags that you own")
    @tagname()
    @content()
    @attachment()
    async def tag_edit(self, ctx:InteractionContext, tagname:str=None, content:str=None, attachment:OptionType.ATTACHMENT=None):
        """/tag edit
        Description:
            Edit tags.

        Args:
            tagname: The tag's name
            content: The content of the tag
            attachment: The attachment from the message
        """
        await ctx.defer()
        if tagname is None:
            embed = Embed(description=f":x: You must include tag's name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        elif (content is None) and (attachment is None):
            embed = Embed(description=f":x: You must include tag's content",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        elif (tagname is None) and (content is None):
            embed = Embed(description=f":x: You must include tag's name and content",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        tagname_regx = {'$regex':f'^{re.escape(tagname)}$', '$options':'i'}
        tag_to_edit = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx, 'author_id':ctx.author.id})
        if tag_to_edit is None:
            tag_to_edit = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx, 'owner_id':ctx.author.id})
            if tag_to_edit is None:
                embed = Embed(description=f":x: You don't own a tag called  `{tagname}`",
                            color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
                return

        if attachment is not None:
            for at in ['exe', 'scr', 'cpl', 'doc', 'jar']:
                if at in attachment.content_type:
                    return await ctx.send(f'`{at}` attachment file type is not allowed to be uploaded to our host site')
            if content is None:
                if (attachment.content_type == 'image/png') or (attachment.content_type == 'image/jpg') or (attachment.content_type == 'image/jpeg') or (attachment.content_type == 'image/gif'):
                    image_url = catbox.url_upload(attachment.url)
                    tag_to_edit.attachment_url = catbox.url_upload(attachment.url)
                    tag_to_edit.content = content
                    await tag_to_edit.save()
                    embed = Embed(description=f"__**Tag edited!**__ \n\n**Tag's name:** {tagname}",
                            color=0xffcc50)
                    embed.set_image(url=image_url)
                    return await ctx.send(embed=embed)
                else:
                    tag_to_edit.attachment_url = catbox.url_upload(attachment.url)
                    tag_to_edit.content = content
                    await tag_to_edit.save()
                    embed = Embed(description=f"__**Tag edited!**__ \n\n**Tag's name:** {tagname}\n**Attachment:** {catbox.url_upload(attachment.url)}",
                            color=0xffcc50)
                    return await ctx.send(embed=embed)
            else:
                if (attachment.content_type == 'image/png') or (attachment.content_type == 'image/jpg') or (attachment.content_type == 'image/jpeg') or (attachment.content_type == 'image/gif'):
                    image_url = catbox.url_upload(attachment.url)
                    tag_to_edit.attachment_url = catbox.url_upload(attachment.url)
                    tag_to_edit.content = content
                    await tag_to_edit.save()
                    embed = Embed(description=f"__**Tag edited!**__ \n\n**Tag's name:** {tagname}\n**Content:** {content}",
                            color=0xffcc50)
                    embed.set_image(url=image_url)
                    return await ctx.send(embed=embed)
                else:
                    tag_to_edit.attachment_url = catbox.url_upload(attachment.url)
                    tag_to_edit.content = content
                    await tag_to_edit.save()
                    embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname}\n**Content:** {content}\n**Attachment:** {catbox.url_upload(attachment.url)}",
                            color=0xffcc50)
                    return await ctx.send(embed=embed)
        else:
            if content is not None:
                url = geturl(content)
                for url in url:
                    url = url
                if url:
                    for at in ['.exe', '.scr', '.cpl', '.doc', '.jar']:
                            if url.endswith(at):
                                return await ctx.send(f'`{at}` url file type is not allowed to be stored in my database')
                    if url.endswith('.png') or url.endswith('.apng') or url.endswith('.jpg') or url.endswith('.jpeg') or url.endswith('.gif'):
                        tag_to_edit.attachment_url = None
                        tag_to_edit.content = content
                        await tag_to_edit.save()
                        embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:**{content}",
                                    color=0xffcc50)
                        embed.set_image(url=url)
                        return await ctx.send(embed=embed)
                    else:
                        tag_to_edit.attachment_url = None
                        tag_to_edit.content = content
                        await tag_to_edit.save()
                        embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:** \n{content}",
                                    color=0xffcc50)
                        return await ctx.send(embed=embed)
                else:
                    tag_to_edit.attachment_url = None
                    tag_to_edit.content = content
                    await tag_to_edit.save()
                    embed = Embed(description=f"__**Tag created!**__ \n\n**Tag's name:** {tagname} \n**Tag's content:** \n{content}",
                                color=0xffcc50)
                    return await ctx.send(embed=embed)
    
    @tag.subcommand(sub_cmd_name='info', sub_cmd_description="allow's me to see information about a tag")
    @tagname()
    async def tag_info(self, ctx:InteractionContext, tagname:str=None):
        """/tag info
        Description:
            See info about tags

        Args:
            tagname: The tag's name
        """
        await ctx.defer()
        if tagname is None:
            embed = Embed(description=f":x: You must include tag's name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
 
        tagname_regx = {'$regex':f'^{re.escape(tagname)}$', '$options':'i'}
        tag_to_view = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx})
        if tag_to_view is None:
            embed = Embed(description=f":x: I couldn't find a tag called `{tagname}`",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        if tag_to_view.owner_id is None:
            owner_id = tag_to_view.author_id
        else:
            owner_id = tag_to_view.owner_id

        tag_owner = ctx.guild.get_member(owner_id)         
        if tag_owner is None:
            tag_owner = tag_to_view.owner_id
            current_owner = 'Currently Orphaned'
            last_owner = f'Last owner: {tag_owner}'
        else:
            current_owner = 'Current owner'
            last_owner = tag_owner
        
        
        total_uses = tag_to_view.no_of_times_used
        if total_uses is None:
            uses = 'UNKNOWN'
        else:
            uses = total_uses

        creation_date = tag_to_view.creation_date
        if creation_date is None:
            date = 'UNKNOWN'
        else:
            date = f'<t:{math.ceil(tag_to_view.creation_date.replace(tzinfo=timezone.utc).timestamp())}:R>'
        
        if tag_to_view.attachment_url is not None:
            if tag_to_view.content is not None:
                content = f'{tag_to_view.content}\n{tag_to_view.attachment_url}'
            else:
                content = f'{tag_to_view.attachment_url}'
        else:
            content = f'{tag_to_view.content}'

        embed = Embed(title=f"Info about [{tag_to_view.names}] tag",
                    color=0xffcc50)
        embed.add_field(name=current_owner, value=last_owner)
        embed.add_field(name="Total uses", value=uses)
        embed.add_field(name="Created", value=date)
        embed.add_field(name="Content", value=content)
        await ctx.send(embed=embed)
    
    @tag.subcommand(sub_cmd_name='list', sub_cmd_description="allow's me to see all tags for this server")
    async def tag_list(self, ctx:InteractionContext):
        """/tag list
        Description:
            Lists all tags
        """
        await ctx.defer()
        from interactions.ext.paginators import Paginator
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
            color=0xffcc50)
            embed.add_field(name='Tag Names', value=names, inline=True)
            return embed

        
        tag_names = db.tag.find({"guild_id":ctx.guild_id})
        names = []
        async for t in tag_names:
            names.append(f"{t.names}\n")
        if names == []:
            embed = Embed(description=f"There are no tags for {ctx.guild.name}.",
                        color=0xffcc50)
            await ctx.send(embed=embed)
            return

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
                
    
    @tag.subcommand(sub_cmd_name='claim', sub_cmd_description="claim orphaned tags")
    @tagname()
    async def tag_claim(self, ctx:InteractionContext, tagname:str=None):
        """/tag claim
        Description:
            Claim orphaned tags

        Args:
            tagname: The tag's name
        """
        await ctx.defer()
        if tagname is None:
            embed = Embed(description=f":x: You must include tag's name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        tagname_regx = {'$regex':f'^{re.escape(tagname)}$', '$options':'i'}
        tag_to_claim = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx})
        if tag_to_claim is None:
            embed = Embed(description=f":x: I couldn't find a tag called `{tagname}`",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        if tag_to_claim.owner_id is None:
            current_owner = tag_to_claim.author_id
        else:
            current_owner = tag_to_claim.owner_id
        if (current_owner == ctx.author.id):
            embed = Embed(description=f":x: You can't claim a tag you already own",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        if (tag_to_claim.author_id == ctx.author.id) and (current_owner != ctx.author.id):
            mf = ctx.guild.get_member(current_owner)
            if mf is None:
                thief = current_owner
            else:
                thief = mf.mention

            embed = Embed(description=f"{ctx.author.mention} You took back your tag {tag_to_claim.names} from {thief}",
                        color=0xffcc50)
            await ctx.send(embed=embed)
            current_owner = ctx.author.id
            await tag_to_claim.save()
            return

        if ctx.guild.get_member(current_owner) is None:
            tag_to_claim.owner_id = ctx.author.id
            await tag_to_claim.save()
            embed = Embed(description=f"{ctx.author.mention} You are now owner of {tag_to_claim.names}",
                        color=0xffcc50)
            await ctx.send(embed=embed)
        else:
            embed = Embed(description=f":x: You can't claim a tag that's not orphaned",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

    @tag.subcommand(sub_cmd_name='gift', sub_cmd_description="gift your tags")
    @tagname()
    @member()
    async def tag_gift(self, ctx:InteractionContext, tagname:str=None, member:OptionType.USER=None):
        """/tag gift
        Description:
            Gidt tags you own

        Args:
            tagname: The tag's name
            member: Member to gift to
        """
        await ctx.defer()
        if tagname is None:
            embed = Embed(description=f":x: You must include tag's name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        if member is None:
            embed = Embed(description=f":x: You must include a member",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        if member == ctx.author:
            embed = Embed(description=f":x: You can't gift to yourself, egomaniac...",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        tagname_regx = {'$regex':f'^{re.escape(tagname)}$', '$options':'i'}
        tag_to_claim = await db.tag.find_one({'guild_id':ctx.guild_id, 'names':tagname_regx, 'owner_id':ctx.author.id})
        if tag_to_claim is None:
            embed = Embed(description=f":x: You don't own a tag with that name",
                        color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            return
        aceept_button_id = f'{member.id}_accept_tag_gift_button'
        cancel_button_id = f'{ctx.author.id}_accept_tag_gift_button'
        accept_button: list[ActionRow] = spread_to_rows(
            Button(
                style=ButtonStyle.GREEN,
                label="GIMME!",
                custom_id=aceept_button_id
            ),
            Button(
                style=ButtonStyle.RED,
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
                await tag_to_claim.save()
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

    @tag.autocomplete('tagname')
    async def tag_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        regx = {'$regex':f'{re.escape(tagname)}', '$options':'igm'}
        tags = db.tag.find({"guild_id":ctx.guild_id, 'names': regx}).limit(25)
        async for tag in tags:
            tag_name = tag.names
            choices.append({'name':f'{tag_name}', 'value':f'{tag.names}'})
        await ctx.send(choices=choices)
    
    @tag_admin_delete.autocomplete('tagname')
    async def tag_admin_delete_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        regx = {'$regex':f'{re.escape(tagname)}', '$options':'igm'}
        tags = db.tag.find({"guild_id":ctx.guild_id, 'names': regx}).limit(25)
        async for tag in tags:
            tag_name = tag.names
            choices.append({'name':f'{tag_name}', 'value':f'{tag.names}'})
        await ctx.send(choices=choices)
    
    @tag_claim.autocomplete('tagname')
    async def tag_claim_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        regx = {'$regex':f'{re.escape(tagname)}', '$options':'igm'}
        tags = db.tag.find({"guild_id":ctx.guild_id, 'names': regx}).limit(25)
        async for tag in tags:
            tag_name = tag.names
            choices.append({'name':f'{tag_name}', 'value':f'{tag.names}'})
        await ctx.send(choices=choices)
    
    @tag_gift.autocomplete('tagname')
    async def tag_gift_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        regx = {'$regex':f'{re.escape(tagname)}', '$options':'igm'}
        tags = db.tag.find({"guild_id":ctx.guild_id, 'names': regx}).limit(25)
        async for tag in tags:
            tag_name = tag.names
            choices.append({'name':f'{tag_name}', 'value':f'{tag.names}'})
        await ctx.send(choices=choices)
    
    @tag_info.autocomplete('tagname')
    async def tag_info_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        regx = {'$regex':f'{re.escape(tagname)}', '$options':'igm'}
        tags = db.tag.find({"guild_id":ctx.guild_id, 'names': regx}).limit(25)
        async for tag in tags:
            tag_name = tag.names
            choices.append({'name':f'{tag_name}', 'value':f'{tag.names}'})
        await ctx.send(choices=choices)
    
    @tag_edit.autocomplete('tagname')
    async def tag_edit_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        regx = {'$regex':f'{re.escape(tagname)}', '$options':'igm'}
        tags = db.tag.find({"guild_id":ctx.guild_id, 'names': regx}).limit(25)
        async for tag in tags:
            tag_name = tag.names
            choices.append({'name':f'{tag_name}', 'value':f'{tag.names}'})
        await ctx.send(choices=choices)
    
    @tag_delete.autocomplete('tagname')
    async def tag_delete_autocomplete(self, ctx: AutocompleteContext):
        tagname = ctx.input_text
        choices = []
        regx = {'$regex':f'{re.escape(tagname)}', '$options':'igm'}
        tags = db.tag.find({"guild_id":ctx.guild_id, 'names': regx}).limit(25)
        async for tag in tags:
            tag_name = tag.names
            choices.append({'name':f'{tag_name}', 'value':f'{tag.names}'})
        await ctx.send(choices=choices)
        
def setup(bot):
    Tags(bot)