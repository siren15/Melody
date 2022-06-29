import asyncio
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import requests

from datetime import datetime, timedelta
from naff import Client, Extension, listen, Permissions, Embed, slash_command, InteractionContext, OptionTypes, check, SlashCommandChoice, Button, ButtonStyles
from naff.models.naff.tasks import Task
from naff.models.naff.tasks.triggers import IntervalTrigger
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *

cooldown_task_ongoing = list()

def find_member(ctx, userid):
    members = [m for m in ctx.guild.members if m.id == userid]
    if members != []:
        for m in members:
            return m
    return None

def find_role(ctx, roleid):
    roles = [r for r in ctx.guild.roles if r.id == roleid]
    if roles != []:
        for r in roles:
            return r
    return None

class Levels(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
    
    @listen()
    async def on_ready(self):
        self.lvl_cooldown_task.start()
    
    @listen()
    async def on_message_create(self, event):
        message = event.message
        if message.author.bot:
            return
        
        cooldown = await db.leveling_cooldown.find_one({'guildid':message.guild.id, 'user':message.author.id})
        if cooldown:
            return
        await db.levelwait(guildid=message.guild.id, user=message.author.id, starttime=datetime.utcnow(), endtime=(datetime.utcnow() + timedelta(seconds=60))).insert()
        
        member = await db.leveling.find_one({'guildid':message.guild.id, 'memberid':message.author.id})
        if not member:
            await db.leveling(guildid=message.guild.id, memberid=message.author.id, total_xp=0, level=0, xp_to_next_level=0, messages=1).insert()
            return
        
        level_stats = await db.levelingstats.find_one( {'lvl':member.level})

        if member.xp_to_next_level is None:
            xp = random.randint(15, 25)
        else:
            xp = member.xp_to_next_level + random.randint(15, 25)

        member.total_xp = member.total_xp+xp
        member.messages = member.messages+1

        if xp >= level_stats.xptolevel:
            member.level = member.level+1
            member.xp_to_next_level = 0
            roles = await db.leveling_roles.find_one({'guildid':message.guild.id, 'level':member.level})
            if roles:
                role = message.guild.get_role(roles.roleid)
                if (role is not None) and (role not in message.author.roles):
                    await message.author.add_role(role, f'[Melody][LEVELUP]Added a role assoiciated with level {member.level}')
        else:
            member.xp_to_next_level = xp
        await member.save()

        level_roles = db.leveling_roles.find({"guildid":message.guild.id, 'level':{'$lte':member.level}})
        roles = []
        async for role in level_roles:
            roles.append(role.roleid)
        if level_roles != []:
            for role_id in roles:
                role = message.guild.get_role(role_id)
                if role not in message.author.roles:
                    await message.author.add_role(role)
        
        if (member.display_name is None) or (member.display_name != message.author.display_name):
            member.display_name = message.author.display_name
            await member.save()
    
    @Task.create(IntervalTrigger(seconds=5))
    async def lvl_cooldown_task(self):
        level_wait = db.levelwait.find({'endtime':{'$lte':datetime.utcnow()}})
        async for instance in level_wait:
            mem = int(f'{instance.guildid}{instance.user}')
            if mem not in cooldown_task_ongoing:
                cooldown_task_ongoing.append(mem)
                await instance.delete()
                cooldown_task_ongoing.remove(mem)

    @slash_command(name='leveling', sub_cmd_name='addrole', sub_cmd_description="[admin]allow's me to create leveling roles",
        default_member_permissions=Permissions.MANAGE_ROLES
    )
    @role()
    @role_level()
    async def leveling_add_role(self, ctx:InteractionContext, role: OptionTypes.ROLE, role_level:str): 
        if (int(role_level) < 1) or (int(role_level) > 300):
            await ctx.send('role level has to be more than 0 and less than 300')
            return

        check = await db.leveling_roles.find_one({'guildid':ctx.guild_id, 'roleid':role.id})
        if check is None:
            await db.leveling_roles(guildid=ctx.guild_id, roleid=role.id, level=int(role_level)).insert()
            await ctx.send(embed=Embed(color=0x0c73d3, description=f'Leveling role {role.mention} assigned to level {role_level}'))
        else:
            await ctx.send(embed=Embed(color=0xDD2222, description=f':x: Leveling role {role.mention} is already assigned to level {check.level}'))
        
        for member in ctx.guild.members:
            mem = await db.leveling.find_one({'guildid':ctx.guild.id, 'memberid':member.id})
            level_roles = db.leveling_roles.find({"guildid":ctx.guild_id, 'level':{'$lte':mem.level}})
            roles = []
            async for role in level_roles:
                roles.append(role.roleid)
            if level_roles != []:
                for role_id in roles:
                    role = ctx.guild.get_role(role_id)
                    if role not in member.roles:
                        await member.add_role(role)
    
    @slash_command(name='ranklist', description="leveling roles list")
    async def ranks_list(self, ctx:InteractionContext):
        from naff.ext.paginators import Paginator
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

        def newpage(title, level, role):
            embed = Embed(title=title,
            color=0x0c73d3)
            embed.add_field(name='Level', value=level, inline=True)
            embed.add_field(name='Role', value=role, inline=True)
            return embed

        
        levels = db.leveling_roles.find({"guildid":ctx.guild_id})
        level = []
        roles = []
        async for l in levels:
            level.append(f'{l.level}\n')
            lvlrole = find_role(ctx, l.roleid)
            if lvlrole is None:
                roles.append('[ROLE NOT FOUND]\n')
            else:
                roles.append(f"{lvlrole.mention}\n")

        if (level or roles) == []:
            embed = Embed(description=f"There are no ranks for {ctx.guild.name}.",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
            return

        s = -1
        e = 0
        embedcount = 1
        nc = list(chunks(level, 20))
        
        embeds = []
        while embedcount <= len(nc):
            s = s+1
            e = e+1
            embeds.append(newpage(f'List of ranks for {ctx.guild.name}', mlis(level, s, e), mlis(roles, s, e)))
            embedcount = embedcount+1
        print(embeds)    
        paginator = Paginator(
            client=self.bot, 
            pages=embeds,
            timeout_interval=80,
            show_select_menu=False)
        await paginator.send(ctx)
    
    @slash_command(name='leveling', sub_cmd_name='removerole', sub_cmd_description="[admin]allow's me to remove leveling roles",
        default_member_permissions=Permissions.MANAGE_ROLES
    )
    @role()
    async def leveling_remove_role(self, ctx:InteractionContext, role: OptionTypes.ROLE=None):
        if role is None:
            await ctx.send('you have to include a role')
            return
        
        check = await db.leveling_roles.find_one({'guildid':ctx.guild.id, 'roleid':role.id})
        if check is None:
            await ctx.send(embed=Embed(color=0xDD2222, description=f':x: Leveling role {role.mention} is not assigned to a level'))
        else:
            await ctx.send(embed=Embed(color=0x0c73d3, description=f'Leveling role {role.mention} removed from level {check.level}'))
            await check.delete()
        
        for member in ctx.guild.members:
            if role in member.roles:
                await member.remove_role(role)
    
    @slash_command(name='rank', description='check your leveling statistics')
    @member()
    async def newrank(self, ctx: InteractionContext, member:OptionTypes.USER=None):
        await ctx.defer()
        # assets: https://imgur.com/a/3Y6W7lZ
        if member is None:
            member = ctx.author
        
        levels = await db.leveling.find_one({'guildid':ctx.guild_id, 'memberid':member.id}) 
        if levels is None:
            await ctx.send("You don't have any xp yet. You can start having conversations with people to gain xp.", ephemeral=True)
            return

        level_stats = await db.levelingstats.find_one({'lvl':levels.level})
        if (levels.display_name is None) or (levels.display_name != member.display_name):
            levels.display_name = member.display_name
            await levels.save()

        #lvl_set = await db.find_one(leveling_settings, {'guildid':ctx.guild.id})
        #if lvl_set is None:
            #await db.save(leveling_settings(guildid=ctx.guild.id))

        #if lvl_set.multiplier is None:
            #multiplier = 1
        #else:
            #multiplier = lvl_set.multiplier
        
        def getPercent(first, second):
            return first / second * 100
        percent = getPercent(levels.xp_to_next_level,level_stats.xptolevel)
        def findx(percentage):
            if percentage == 0:
                return 1
            return 550/(100/percentage)

        if member.guild_avatar is not None:
            avatarurl = f'{member.guild_avatar.url}.png'
        else:
            avatarurl = f'{member.avatar.url}.png'
        
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
        aspect_ratio = IW/IH

        if levels.lc_background is not None:
            try:
                background = Image.open(requests.get(f'{levels.lc_background}', stream=True).raw).crop((0,0,IW,IH)).convert("RGBA")
            except:
                background = Image.open(requests.get('https://i.imgur.com/ExfggOL.png', stream=True).raw).convert("RGBA")
        else:
            background = Image.open(requests.get('https://i.imgur.com/ExfggOL.png', stream=True).raw).convert("RGBA")

        overlay = Image.open(requests.get('https://i.imgur.com/fsuIzSv.png', stream=True).raw).convert("RGBA")
        background.paste(overlay, (0, 0), overlay)

        pfp = Image.open(requests.get(avatarurl, stream=True).raw).resize((230,230)).convert("RGBA")
        pfp = round(pfp)
        background.paste(pfp, (78, 115), pfp)

        # progress_bar = Image.open(requests.get('https://i.imgur.com/YZIuHJV.png', stream=True).raw).resize((int(findx(int(percent))), 23), resample=Image.ANTIALIAS).convert("RGBA")
        # background.paste(progress_bar, (277, 288), progress_bar)
        
        def draw_progress_bar(fx):
            rad = 115
            im = Image.open(requests.get('https://i.imgur.com/sRseF8Y.png', stream=True).raw).convert('RGBA')
            im = im.resize((fx*16,30*16), resample=Image.ANTIALIAS)
            circle = Image.new('L', (rad * 2, rad * 2), 0)
            draw = ImageDraw.Draw(circle)
            draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
            alpha = Image.new('L', im.size, 255)
            w, h = im.size
            alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
            alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
            alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
            alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
            im.putalpha(alpha)
            im = im.resize((fx,30), resample=Image.ANTIALIAS)
            return im

        fx = findx(int(percent))
        progress_bar = draw_progress_bar(int(fx))
        background.paste(progress_bar, (330, 370), progress_bar)

        def rectangle_fill(im):
            mask = Image.new("L", im.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rectangle((0,0)+im.size, fill=255)
            out = ImageOps.fit(im, mask.size, centering=(0,0))
            out.putalpha(mask)
            return out

        background = rectangle_fill(background)

        font = ImageFont.truetype('Everson-Mono-Bold.ttf', 45)
        
        I1 = ImageDraw.Draw(background)

        lvlfont = ImageFont.truetype('Everson-Mono-Bold.ttf', 45)
        I1.text((73,352), f'LVL:{levels.level}', font=lvlfont, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255))
        # lvlfont_2 = ImageFont.truetype('Everson-Mono-Bold.ttf', 25)
        # I1.text((52,360), 'Lvl', font=lvlfont_2, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255))

        lvlmsg = f'XP: {levels.xp_to_next_level}/{level_stats.xptolevel}\nTotal XP: {levels.total_xp}\nMessages: {levels.messages}'
        I1.text((341,110), lvlmsg, font=font, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255))

        namefont = ImageFont.truetype('Everson-Mono-Bold.ttf', 50)
        name = f'{member.display_name}'
        if len(name) > 27:
            name = name[:-4]
        # tw, th = I1.textsize(name, font)
        # position = ((IW-tw)/2,(IH-th)/14)
        I1.text((73,28), name, font=namefont, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255))
        background.save(f'levelcard_{member.id}.png')
        await ctx.send(file=f'levelcard_{member.id}.png')
        os.remove(f'levelcard_{member.id}.png')
    
    @slash_command(name='level', sub_cmd_name='background', sub_cmd_description='change the background of your level stats card(resolution should be min: 956x435)', scopes=[435038183231848449,149167686159564800])
    @attachment()
    @reset_to_default()
    @check(role_lock())
    async def level_bg(self, ctx: InteractionContext, attachment: OptionTypes.ATTACHMENT, reset_to_default:OptionTypes.BOOLEAN=False):
        from utils.catbox import CatBox as cb
        if reset_to_default == True:
            levels = await db.leveling.find_one({'guildid':ctx.guild_id, 'memberid':ctx.author.id})
            if levels.lc_background is not None:
                levels.lc_background = None
                await levels.save()
                return await ctx.send(f"{ctx.author.mention} Background is now set back to default")
            elif levels.lc_background is None:
                return await ctx.send(f"{ctx.author.mention} You don't have a custom background set")

        if str(attachment.content_type) not in ['image/jpeg', 'image/jpg', 'image/png']:
            return await ctx.send('The background has to be an image, .png or .jpg/.jpeg are allowed')

        bg_url = cb.url_upload(attachment.url)
        levels = await db.leveling.find_one({'guildid':ctx.guild_id, 'memberid':ctx.author.id})
        levels.lc_background = bg_url
        await levels.save()
        embed = Embed(description=f"Leveling card background set to {bg_url}", color=0x0c73d3)
        embed.set_image(bg_url)
        await ctx.send(embed=embed)
    
    @slash_command(name='reset_lvl_bg', description='[ADMIN]Reset members level card background)', scopes=[435038183231848449,149167686159564800],
        default_member_permissions=Permissions.ADMINISTRATOR
    )
    @user()
    async def level_bg_reset(self, ctx: InteractionContext, user: OptionTypes.USER):
        levels = await db.leveling.find_one({'guildid':ctx.guild_id, 'memberid':user.id})
        if levels.lc_background is not None:
            levels.lc_background = None
            await levels.save()
            return await ctx.send(f"Background is now set back to default")
        elif levels.lc_background is None:
            return await ctx.send(f"Member {user.mention} doeasn't have a custom background set")

    @slash_command(name='leaderboard', description='check the servers leveling leaderboard')
    @slash_option(name="web_or_local", description="Choose which type do you want, within discord or link to website.", opt_type=OptionTypes.STRING, required=False,
    choices=[
            SlashCommandChoice(name="website", value='web'),
            SlashCommandChoice(name="discord_paginator", value='local')
        ]
    )
    async def leaderboard(self, ctx: InteractionContext, web_or_local:OptionTypes.STRING='web'):
        if web_or_local == 'web':
            components = Button(
                style=ButtonStyles.URL,
                label="Click Me!",
                url=f"https://beni2am.herokuapp.com/melody/leaderboard/{ctx.guild_id}/",
            )
            await ctx.send("A button to the web leaderboard!", components=components)
        elif web_or_local == 'local':
            from naff.ext.paginators import Paginator
            from tabulate import tabulate as tb
            def chunks(l, n):
                n = max(1, n)
                return (l[i:i+n] for i in range(0, len(l), n))
            
            def page_list(lst, s, e):
                nc = list(chunks(lst, 20))
                for page in nc[s:e]:
                    return page

            def newpage(title, stats):
                embed = Embed(
                    title=title,
                    description=f'```\n{stats}\n```',
                    color=0x0c73d3)
                return embed
            
            lvl_order = db.leveling.find({'guildid':ctx.guild_id, 'level':{'$gt':0}}).sort(-db.leveling.total_xp)
            
            rank = 1
            stats = []
            async for lvl in lvl_order:
                if rank == 1:
                    ranks = '🏆1'
                elif rank == 2:
                    ranks = '🥈2'
                elif rank == 3:
                    ranks = '🥉3'
                else:
                    ranks = rank
                member = find_member(ctx, lvl.memberid)
                if member is not None:
                    # stats.append([f'[1;37m{ranks}.', f'[0;34m{member.display_name}', f'[0;31m{lvl.level}', f'[0;36m{lvl.total_xp}']) this will be used when mobile ansi support will be available
                    # if (lvl.display_name is None) or (lvl.display_name != member.display_name):
                    #     lvl.display_name = member.display_name
                    #     await lvl.save()
                    stats.append([f'{ranks}.', f'{member.display_name}', f'{lvl.level}', f'{lvl.total_xp}'])
                else:
                    stats.append([f'{ranks}.', f'{lvl.memberid}', f'{lvl.level}', f'{lvl.total_xp}'])
                rank = rank+1
            
            if stats == []:
                await ctx.send('Nobody has levels in this server yet')
                return            

            s = -1
            e = 0
            embedcount = 1
            nc = list(chunks(stats, 20))
            
            embeds = []
            while embedcount <= len(nc):
                s = s+1
                e = e+1

                embeds.append(newpage(f'Leveling leaderboard for {ctx.guild.name}', tb(page_list(stats, s, e), headers=['Rank', "Member", "Level", "Total XP"], colalign=("left","left","left","left"))))
                embedcount = embedcount+1
                
            paginator = Paginator(
                client=self.bot, 
                pages=embeds,
                timeout_interval=80,
                show_select_menu=False,
                wrong_user_message='Stop finding yourself! ...Since this leaderboard was not generated for you')
            await paginator.send(ctx)
        
def setup(bot):
    Levels(bot)