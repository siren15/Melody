import asyncio
from PIL import Image, ImageDraw, ImageFont
import os
import requests

from datetime import datetime, timedelta
from dis_snek import Snake, Scale, listen, Permissions, Embed, slash_command, InteractionContext, OptionTypes
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *

class Levels(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @listen()
    async def on_message_create(self, event):
        message = event.message
        if message.author.bot:
            return
        #if (iscogactive(message.guild, 'leveling') == True) and (is_event_active(message.guild, 'leveling')):
        
        #level_settings = await db.find_one(leveling_settings, {'guildid':message.guild.id})
        #if level_settings != None:
            #if message.channel.id in level_settings.no_xp_channel:
                #return
        db = await odm.connect() #connect to database
        #check if enough time has passed since last message
        wait_mem = await db.find_one(levelwait, {'guildid':message.guild.id, 'user':message.author.id, 'endtime':{'$gt':datetime.utcnow()}})
        if wait_mem == None:
            #check what xp the user has
            levels = await db.find_one(leveling, {'guildid':message.guild.id, 'memberid':message.author.id}) #find the member in the db
            
            if levels == None: #if the member is not logged in db
                await db.save(leveling(guildid=message.guild.id, memberid=message.author.id, total_xp=0, level=0, xp_to_next_level=0)) #member get's logged to db with level and xp set to 0
                return

            level_stats = await db.find_one(levelingstats, {'lvl':levels.level}) #get level stats from db

            total_xp = levels.total_xp #total xp the user has
            lvl = levels.level #the level the user has
            if levels.xp_to_next_level == None:#if the xp to next level is not logged, due to migration from mee6
                xp = 0 #xp is set to 0
            else:
                xp = levels.xp_to_next_level #xp that the user has towards next level, this counter resets every time a new level is acquired

            #level multiplier, it's gonna divide the xp needed towards the next level
            #if level_settings.multiplier == None:#if the server doesn't have multiplier set up
                #multiplier = 1#the default multiplier is set to 1
            #else:
                #multiplier = level_settings.multiplier#otherwise get the multiplier from db

            #xp_to_next_level = math.ceil(((4*((lvl*max) + (min+lvl)) - xp)/multiplier)*decimal) #count the xp to next level, now unused since it's better to have it all already calculated and ready to check in db
            xp_to_next_level = level_stats.xptolevel#/multiplier #the xp expected for next level

            import random
            xp_to_give = random.randint(15, 25) #xp that's given to member, a random number between 15-25
            new_total_xp = total_xp+xp_to_give #the new total xp, old total xp + xp to give
            if levels.messages == None:  #if no messages logged in db
                number_of_messages = 1 #number of xp messages is 1 for the current message
            else:
                number_of_messages = levels.messages + 1 #otherwise the number of xp messages is logged no. of messages + 1 for the current message

            if xp_to_next_level <= (xp+xp_to_give): # if the members xp towards the next level equals or is higher than xp expected for next level, member levels up
                levels.level = lvl+1 #members level gets updated
                levels.xp_to_next_level = 0 #members xp towards next level gets reset to 0
                levels.total_xp = new_total_xp #total xp gets updated
                levels.messages = number_of_messages #no. of messages that made xp get updated
                await db.save(levels)
                
                roles = await db.find_one(leveling_roles, {'guildid':message.guild.id, 'level':lvl+1})#get the role reward for the level if it exists
                if roles != None:#if it's not none
                    role = await message.guild.get_role(roles.roleid)#find the role in the guild by the id stored in the db
                    if (role != None) and (role not in message.author.roles):#if it exists and the member doesn't have it
                        await message.author.add_role(role, '[bot]leveling role add')#give it to member
            else:                                       # if the members xp towards the next level equals or is not higher than xp expected for next level
                levels.xp_to_next_level = xp+xp_to_give #members xp towards the next level gets updated
                levels.total_xp = new_total_xp          #with total xp
                levels.messages = number_of_messages    #and number of messages
                await db.save(levels)

            await db.save(levelwait(guildid=message.guild.id, user=message.author.id, starttime=datetime.utcnow(), endtime=(datetime.utcnow() + timedelta(seconds=60)))) #member gets put into the wait list
            await asyncio.sleep(60) #the commands gonna wait for 60 seconds
            level_wait = await db.find(levelwait, {'guildid':message.guild.id, 'user':message.author.id, 'endtime':{'$lte':datetime.utcnow()}}) #find member in the wait list
            for instance in level_wait:
                await db.delete(instance) #member gets removed from wait list
    
    @slash_command(name='leveling', sub_cmd_name='addrole', sub_cmd_description="[admin]allow's me to create leveling roles")
    @role()
    @role_level()
    async def leveling_add_role(self, ctx:InteractionContext, role: OptionTypes.ROLE=None, role_level:str=None):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.ADMINISTRATOR)
        if (perms == True):
            if role == None:
                await ctx.send('you have to include a role')
                return
            if role_level == None:
                await ctx.send('you have to include a role level')
                return
            if (int(role_level) < 1) or (int(role_level) > 500):
                await ctx.send('role level has to be more than 0 and less than 300')
                return

            db = await odm.connect()
            check = await db.find_one(leveling_roles, {'guildid':ctx.guild.id, 'roleid':role.id})
            if check == None:
                await db.save(leveling_roles(guildid=ctx.guild.id, roleid=role.id, level=int(role_level)))
                await ctx.send(embed=Embed(color=0x0c73d3, description=f'Leveling role {role.mention} assigned to level {role_level}'))
            else:
                await ctx.send(embed=Embed(color=0xDD2222, description=f':x: Leveling role {role.mention} is already assigned to level {check.level}'))
    
    @slash_command(name='ranklist', description="leveling roles list")
    async def ranks_list(self, ctx:InteractionContext):
        await ctx.defer()
        hasrole = await has_role(ctx)
        if hasrole == True:
            from .src.paginators import Paginator
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

            db = await odm.connect()
            levels = await db.find(leveling_roles, {"guildid":ctx.guild_id})

            level = [str(l.level)+"\n" for l in levels]

            if level == []:
                embed = Embed(description=f"There are no ranks for {ctx.guild.name}.",
                            color=0x0c73d3)
                await ctx.send(embed=embed)
                return
            
            roles = []
            for lvl in levels:
                lvlrole = await ctx.guild.get_role(lvl.roleid)
                if lvlrole == None:
                    roles.append('[ROLE NOT FOUND]\n')
                else:
                    roles.append(f"{lvlrole.mention}\n")

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
                
            paginator = Paginator(
                client=self.bot, 
                pages=embeds,
                timeout_interval=80,
                show_select_menu=False)
            await paginator.send(ctx)
    
    @slash_command(name='leveling', sub_cmd_name='removerole', sub_cmd_description="[admin]allow's me to remove leveling roles")
    @role()
    async def leveling_remove_role(self, ctx:InteractionContext, role: OptionTypes.ROLE=None):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.ADMINISTRATOR)
        if (perms == True):
            if role == None:
                await ctx.send('you have to include a role')
                return

            db = await odm.connect()
            check = await db.find_one(leveling_roles, {'guildid':ctx.guild.id, 'roleid':role.id})
            if check == None:
                await ctx.send(embed=Embed(color=0xDD2222, description=f':x: Leveling role {role.mention} is not assigned to a level'))
            else:
                await ctx.send(embed=Embed(color=0x0c73d3, description=f'Leveling role {role.mention} removed from level {check.level}'))
                await db.delete(check)

    @slash_command(name='oldrank', description='check your leveling statistics')
    @member()
    async def oldrank(self, ctx: InteractionContext, member:OptionTypes.USER=None):
        await ctx.defer()
        if member == None:
            member = ctx.author
        db = await odm.connect()
        levels = await db.find_one(leveling, {'guildid':ctx.guild_id, 'memberid':member.id}) 
        if levels == None:
            await ctx.send("You don't have any xp yet. You can start having conversations with people to gain xp.", ephemeral=True)
            return

        level_stats = await db.find_one(levelingstats, {'lvl':levels.level})

        #lvl_set = await db.find_one(leveling_settings, {'guildid':ctx.guild.id})
        #if lvl_set == None:
            #await db.save(leveling_settings(guildid=ctx.guild.id))

        #if lvl_set.multiplier == None:
            #multiplier = 1
        #else:
            #multiplier = lvl_set.multiplier
        
        def getPercent(first, second, integer = False):
            percent = first / second * 100
            if integer:
                return int(percent)
            return percent

        percent = getPercent(levels.xp_to_next_level,level_stats.xptolevel)
        if percent <= 5:
            boxes = '□□□□□□□□□□'
        elif percent <= 10:
            boxes = '■□□□□□□□□□'
        elif percent <= 20:
            boxes = '■■□□□□□□□□'
        elif percent <= 30:
            boxes = '■■■□□□□□□□'
        elif percent <= 40:
            boxes = '■■■■□□□□□□'
        elif percent <= 50:
            boxes = '■■■■■□□□□□'
        elif percent <= 60:
            boxes = '■■■■■■□□□□'
        elif percent <= 70:
            boxes = '■■■■■■■□□□'
        elif percent <= 80:
            boxes = '■■■■■■■■□□'
        elif percent <= 90:
            boxes = '■■■■■■■■■□'
        elif percent <= 95:
            boxes = '■■■■■■■■■□'
        elif percent <= 100:
            boxes = '■■■■■■■■■■'

        if member.top_role.color.value == 0:
            color = 0x0c73d3
        else:
            color = member.top_role.color

        embed = Embed(color=color,
        description=f"__**Leveling stats for {member.mention}**__\n\n**Level:** {levels.level}\n**XP:** {levels.xp_to_next_level}**/**{level_stats.xptolevel}\n{boxes}\n**Total XP:** {levels.total_xp}\n**Messages sent:** {levels.messages}")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)
    
    @slash_command(name='rank', description='check your leveling statistics')
    @member()
    async def newrank(self, ctx: InteractionContext, member:OptionTypes.USER=None):
        await ctx.defer()
        if member == None:
            member = ctx.author
        db = await odm.connect()
        levels = await db.find_one(leveling, {'guildid':ctx.guild_id, 'memberid':member.id}) 
        if levels == None:
            await ctx.send("You don't have any xp yet. You can start having conversations with people to gain xp.", ephemeral=True)
            return

        level_stats = await db.find_one(levelingstats, {'lvl':levels.level})

        #lvl_set = await db.find_one(leveling_settings, {'guildid':ctx.guild.id})
        #if lvl_set == None:
            #await db.save(leveling_settings(guildid=ctx.guild.id))

        #if lvl_set.multiplier == None:
            #multiplier = 1
        #else:
            #multiplier = lvl_set.multiplier
        
        def getPercent(first, second):
            return first / second * 100
        percent = getPercent(levels.xp_to_next_level,level_stats.xptolevel)
        def findx(percentage):
            return 715/(100/percentage)

        if member.guild_avatar != None:
            avatarurl = f'{member.guild_avatar.url}.png'
        else:
            avatarurl = f'{member.avatar.url}.png'
        pfp = Image.open(requests.get(avatarurl, stream=True).raw).resize((230,230)).convert("RGBA")

        IW, IH = (1100, 500)

        background = Image.open(requests.get('https://i.imgur.com/wQsqg2H.png', stream=True).raw).convert("RGBA")
        shade = Image.open(requests.get('https://i.imgur.com/8sGr8So.png', stream=True).raw).convert("RGBA")
        background.paste(shade, (0, 0), shade)
        background.paste(pfp, (68, 143), pfp)

        progressbar_fill = Image.open(requests.get('https://i.imgur.com/HE0XtlF.png', stream=True).raw).resize((int(findx(int(percent))), 47)).convert("RGBA")
        background.paste(progressbar_fill, (323, 146), progressbar_fill)

        avatar_frame = Image.open(requests.get('https://i.imgur.com/6iKS56q.png', stream=True).raw).convert("RGBA")
        background.paste(avatar_frame, (0, 75), avatar_frame)

        font = ImageFont.truetype('Everson-Mono-Bold.ttf', 56)
        
        I1 = ImageDraw.Draw(background)
        lvlmsg = f'LVL:{levels.level}|XP: {levels.xp_to_next_level}/{level_stats.xptolevel}\nTotal XP: {levels.total_xp}\nMessages: {levels.messages}'
        I1.text((312,201), lvlmsg, font=font, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255))

        namefont = ImageFont.truetype('Everson-Mono-Bold.ttf', 80)
        name = f'{member.display_name}'
        tw, th = I1.textsize(name, namefont)
        position = ((IW-tw)/2,(IH-th)/12)
        if len(member.display_name) >= 15:
            namefont = ImageFont.truetype('Everson-Mono-Bold.ttf', 70)
            tw, th = I1.textsize(name, namefont)
            position = ((IW-tw)/2,(IH-th)/11.5)
        elif len(member.display_name) >= 25:
            namefont = ImageFont.truetype('Everson-Mono-Bold.ttf', 60)
            tw, th = I1.textsize(name, namefont)
            position = ((IW-tw)/2,(IH-th)/10)

        I1.text(position, name, font=namefont, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255))
        background.save(f'levelcard_{member.id}.png')
        await ctx.send(file=f'levelcard_{member.id}.png')
        os.remove(f'levelcard_{member.id}.png')
    
    @slash_command(name='leaderboard', description='check the servers leveling leaderboard')
    async def leaderboard(self, ctx: InteractionContext):
        from .src.paginators import Paginator
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

        def newpage(title, member, lvl, xp):
            embed = Embed(title=title,
            color=0x0c73d3)
            embed.add_field(name='Member', value=member, inline=True)
            embed.add_field(name='Level', value=lvl, inline=True)
            embed.add_field(name='Total XP', value=xp, inline=True)
            return embed

        await ctx.defer()
        
        db = await odm.connect()
        lvl_order = await db.find(leveling, {'guildid':ctx.guild_id}, sort=(leveling.level.desc(), leveling.total_xp.desc()))
        if lvl_order == None:
            await ctx.send('Nobody has levels in this server yet')
            return
        rank = 1
        members = []
        for lvl in lvl_order:
            if rank == 1:
                ranks = '🏆 1'
            elif rank == 2:
                ranks = '🥈 2'
            elif rank == 3:
                ranks = '🥉 3'
            else:
                ranks = rank
            members.append(f'**{ranks}.** <@{lvl.memberid}>\n')
            rank = rank+1
        lvls = [f'{lvl.level}\n' for lvl in lvl_order]
        tot_xp = [f'{xp.total_xp}\n' for xp in lvl_order]
        
        s = -1
        e = 0
        embedcount = 1
        nc = list(chunks(members, 20))
        
        embeds = []
        while embedcount <= len(nc):
            s = s+1
            e = e+1
            embeds.append(newpage(f'Leveling leaderboard for {ctx.guild.name}', mlis(members, s, e), mlis(lvls, s, e), mlis(tot_xp, s, e)))
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