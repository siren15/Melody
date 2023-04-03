import random
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import requests

import interactions
from datetime import datetime, timedelta
from interactions import Client, Extension, SlashContext, listen, Permissions, Embed, SlashCommand, slash_command, InteractionContext, OptionType, Button, ButtonStyle
from interactions.api.events.discord import MessageCreate
from interactions.models.internal.tasks import Task
from interactions.models.internal.tasks.triggers import IntervalTrigger
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *

cooldown_task_ongoing = list()

def find_member(ctx, userid):
    return ctx.guild.get_member(userid)

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
    
    LevelSettings = SlashCommand(name='leveling_config', default_member_permissions=Permissions.ADMINISTRATOR, description='Manage leveling settings.')

    @LevelSettings.subcommand('ignored_channel', 'add', 'Add a channel to ignored channels.')
    @channel()
    async def LevelingAddIgnoredChannels(self, ctx:InteractionContext, channel: OptionType.CHANNEL=None):
        """/leveling_config ignored_channel add
        Description:
            Add a channel to ignored channels by leveling
        Args:
            channel (OptionType.CHANNEL, optional): Channel to add, defaults to channel command is executed in
        """
        await ctx.defer(ephemeral=True)
        if channel is None:
            channel = ctx.channel
        settings = await db.leveling_settings.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.leveling_settings(guildid=ctx.guild.id).insert()
        ignored_channels = settings.ignored_channels
        if ignored_channels is None:
            ignored_channels = list()
        if channel.id in ignored_channels:
            await ctx.send(f'{channel.mention} is already ignored.', ephemeral=True)
        ignored_channels.append(channel.id)
        await settings.save()
        channel_mentions = [ctx.guild.get_channel(id) for id in ignored_channels]
        channel_mentions = [ch.mention for ch in channel_mentions if ch is not None]
        channel_mentions = ' '.join(channel_mentions)
        embed = Embed(description=f"Channel {channel.mention} set to be ignored.")
        embed.add_field('Ignored Channels', channel_mentions)
        await ctx.send(embed=embed, ephemeral=True)

    @LevelSettings.subcommand('ignored_channel', 'remove', 'Remove a channel from ignored channels.')
    @channel()
    async def LevelingRemoveIgnoredChannels(self, ctx:InteractionContext, channel: OptionType.CHANNEL=None):
        """/leveling_config ignored_channel remove
        Description:
            Remove a channel from ignored channels by leveling
        Args:
            channel (OptionType.CHANNEL, optional): Channel to remove, defaults to channel command is executed in
        """
        await ctx.defer(ephemeral=True)
        if channel is None:
            channel = ctx.channel
        settings = await db.leveling_settings.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.leveling_settings(guildid=ctx.guild.id).insert()
        ignored_channels = settings.ignored_channels
        if ignored_channels is None:
            ignored_channels = list()
        if channel.id not in ignored_channels:
            await ctx.send(f'{channel.mention} is not being ignored by leveling.', ephemeral=True)
        ignored_channels.remove(channel.id)
        await settings.save()
        channel_mentions = [ctx.guild.get_channel(id) for id in ignored_channels]
        channel_mentions = [ch.mention for ch in channel_mentions if ch is not None]
        channel_mentions = ' '.join(channel_mentions)
        embed = Embed(description=f"Channel {channel.mention} removed from ignored channels.")
        embed.add_field('Ignored Channels', channel_mentions)
        await ctx.send(embed=embed, ephemeral=True)
    
    @LevelSettings.subcommand('ignored_role', 'add', 'Make a role to be ignored by leveling.')
    @role()
    async def LevelingAddIgnoredRoles(self, ctx:InteractionContext, role: OptionType.ROLE):
        """/leveling_config ignored_role add
        Description:
            Add a role to be ignored by leveling
        Args:
            role (OptionType.ROLE): Role to add
        """
        await ctx.defer(ephemeral=True)
        settings = await db.leveling_settings.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.leveling_settings(guildid=ctx.guild.id).insert()
        ignored_roles = settings.ignored_roles
        if ignored_roles is None:
            ignored_roles = list()
        if role.id in ignored_roles:
            await ctx.send(f'{role.mention} is already ignored.', ephemeral=True)
        ignored_roles.append(role.id)
        await settings.save()
        role_mentions = [ctx.guild.get_role(id) for id in ignored_roles]
        role_mentions = [r.mention for r in role_mentions if r is not None]
        role_mentions = ' '.join(role_mentions)
        embed = Embed(description=f"Role {role.mention} was added to roles ignored by leveling.")
        embed.add_field('Ignored Roles', role_mentions)
        await ctx.send(embed=embed, ephemeral=True)

    @LevelSettings.subcommand('ignored_role', 'remove', 'Remove a role from ignored roles.')
    @role()
    async def LevelingRemoveIgnoredRoles(self, ctx:InteractionContext, role: OptionType.ROLE):
        """/leveling_config ignored_role remove
        Description:
            Remove a role from ignored by leveling
        Args:
            role (OptionType.ROLE): Role to remove
        """
        await ctx.defer(ephemeral=True)
        settings = await db.leveling_settings.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.leveling_settings(guildid=ctx.guild.id).insert()
        ignored_roles = settings.ignored_roles
        if ignored_roles is None:
            ignored_roles = list()
        if role.id not in ignored_roles:
            await ctx.send(f'{role.mention} is not being ignored by leveling.', ephemeral=True)
        ignored_roles.remove(role.id)
        await settings.save()
        role_mentions = [ctx.guild.get_role(id) for id in ignored_roles]
        role_mentions = [r.mention for r in role_mentions if r is not None]
        role_mentions = ' '.join(role_mentions)
        embed = Embed(description=f"Role {role.mention} was removed from roles ignored by leveling.")
        embed.add_field('Ignored Roles', role_mentions)
        await ctx.send(embed=embed, ephemeral=True)
    
    @LevelSettings.subcommand('ignored_member', 'add', 'Make a member to be ignored by leveling.')
    @user()
    async def LevelingAddIgnoredMember(self, ctx:InteractionContext, user: OptionType.USER):
        """/leveling_config ignored_member add
        Description:
            Make a member to be ignored by leveling.
        Args:
            user (OptionType.USER): User to add
        """
        await ctx.defer(ephemeral=True)
        settings = await db.leveling_settings.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.leveling_settings(guildid=ctx.guild.id).insert()
        ignored_users = settings.ignored_users
        if ignored_users is None:
            ignored_users = list()
        if user.id in ignored_users:
            await ctx.send(f'{user}|{user.id} is already ignored.', ephemeral=True)
        ignored_users.append(user.id)
        await settings.save()
        users = [ctx.guild.get_member(id) for id in ignored_users]
        users = [f'{r}({r.id})' for r in users if r is not None]
        users = ' '.join(users)
        embed = Embed(description=f"Member {user}({user.id}) was added to members ignored by leveling.")
        embed.add_field('Ignored Members', users)
        await ctx.send(embed=embed, ephemeral=True)

    @LevelSettings.subcommand('ignored_member', 'remove', 'Remove a member from ignored members.')
    @user()
    async def LevelingRemoveIgnoredMember(self, ctx:InteractionContext, user: OptionType.USER):
        """/leveling_config ignored_member remove
        Description:
            Remove a member from ignored members for leveling

        Args:
            user (OptionType.USER): User to ignore
        """
        await ctx.defer(ephemeral=True)
        settings = await db.leveling_settings.find_one({"guildid":ctx.guild.id})
        if settings is None:
           await db.leveling_settings(guildid=ctx.guild.id).insert()
        ignored_users = settings.ignored_users
        if ignored_users is None:
            ignored_users = list()
        if user.id not in ignored_users:
            await ctx.send(f'{user}|{user.id} is not being ignored by leveling.', ephemeral=True)
        ignored_users.remove(user.id)
        await settings.save()
        users = [ctx.guild.get_member(id) for id in ignored_users]
        users = [f'{r}({r.id})' for r in users if r is not None]
        users = ' '.join(users)
        embed = Embed(description=f"Member {user}({user.id}) was removed from members ignored by leveling.")
        embed.add_field('Ignored Members', users)
        await ctx.send(embed=embed, ephemeral=True)
    
    @listen()
    async def on_xp_gain(self, event: MessageCreate):
        message = event.message # get message object from event
        user = message.author # get user object from message
        if user.bot: # if user is a bot, return
            return
        
        settings = await db.leveling_settings.find_one({'guildid':message.guild.id}) # get leveling settings for guild
        if not user.has_permission(Permissions.ADMINISTRATOR): # if user is not an admin
            if settings.ignored_users is not None: # if ignored users list is not empty
                if user.id in settings.ignored_users: # if user is in ignored users list, return
                    return
            if settings.ignored_roles is not None: # if ignored roles list is not empty
                if any(role for role in user.roles if role.id in settings.ignored_roles): # if user has an ignored role, return
                    return
        if settings.ignored_channels is not None: # if ignored channels list is not empty
            if message.channel.id in settings.ignored_channels: # if message is in ignored channel, return
                return
        
        cooldown = await db.levelwait.find_one({'guildid':message.guild.id, 'user':message.author.id}) # check if user is on cooldown
        if cooldown: # if user is on cooldown, return
            return
        await db.levelwait(guildid=message.guild.id, user=message.author.id, starttime=datetime.utcnow(), endtime=(datetime.utcnow() + timedelta(seconds=60))).insert() # add user to cooldown list
        
        member = await db.leveling.find_one({'guildid':message.guild.id, 'memberid':message.author.id}) # get leveling data for user
        if not member: # if user has no leveling data, create new data and return
            await db.leveling(guildid=message.guild.id, memberid=message.author.id, total_xp=0, level=0, xp_to_next_level=0, messages=1).insert()
            return
        
        level_stats = await db.levelingStats.find_one( {'level':member.level}) # get leveling stats for user's current level

        if member.xp_to_next_level is None: # if user has no xp to next level, set to 0
            xptnl = 0
        else:
            xptnl = member.xp_to_next_level
        xp_to_give = random.randint(15, 25) # generate random xp to give
        member.total_xp = member.total_xp+xp_to_give # add xp to user's total xp
        if member.messages is None: # if user has no message count, set to 0
            member.messages = 0
        member.messages = member.messages+1 # increment user's message count
        xp = xptnl + xp_to_give # calculate total xp
        
        if xp >= level_stats.xp_to_next_level: # if user has enough xp to level up
            member.level = member.level+1 # increment user's level
            member.xp_to_next_level = 0 # reset user's xp to next level
            roles = await db.leveling_roles.find_one({'guildid':message.guild.id, 'level':member.level}) # get roles associated with user's new level
            if roles: # if roles exist for user's new level
                role = message.guild.get_role(roles.roleid) # get role object
                if (role is not None) and (role not in message.author.roles): # if role exists and user does not already have role
                    await message.author.add_role(role, f'[Melody][LEVELUP]Added a role assoiciated with level {member.level}') # add role to user and send message
        else:
            member.xp_to_next_level = xp # set user's xp to next level to calculated value
        await member.save() # save user's leveling data

        # Find all leveling roles for the current guild that have a level requirement less than or equal to the member's level
        level_roles = db.leveling_roles.find({"guildid":message.guild.id, 'level':{'$lte':member.level}})
        
        # Create an empty list to store the role IDs of the leveling roles the member is eligible for
        roles = []
        
        # Loop through the leveling roles the member is eligible for and append their role IDs to the roles list
        async for role in level_roles:
            roles.append(role.roleid)
        
        # If the member is eligible for any leveling roles, loop through the role IDs and add the corresponding roles to the member's roles if they don't already have them
        if level_roles != []:
            for role_id in roles:
                role = message.guild.get_role(role_id)
                if role not in message.author.roles:
                    await message.author.add_role(role)
        
        # If the member's display name is None or different from their current display name, update their display name and save the changes
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

    leveling = SlashCommand(name='leveling', description='add/remove leveling roles', default_member_permissions=Permissions.MANAGE_ROLES)

    @leveling.subcommand(sub_cmd_name='addrole', sub_cmd_description="allow's me to create leveling roles")
    @role()
    @role_level()
    async def leveling_add_role(self, ctx:InteractionContext, role: OptionType.ROLE, role_level:str):
        """/leveling addrole
        Description:
            Create level roles

        Args:
            role (OptionType.ROLE): Role
            role_level (str): Role level number, has to be more than 0 and less than 1000
        """
        await ctx.defer()
        if (int(role_level) < 1) or (int(role_level) > 1000):
            await ctx.send('role level has to be more than 0 and less than 1000')
            return

        check = await db.leveling_roles.find_one({'guildid':ctx.guild_id, 'roleid':role.id})
        if check is None:
            await db.leveling_roles(guildid=ctx.guild_id, roleid=role.id, level=int(role_level)).insert()
            await ctx.send(embed=Embed(color=0xffcc50, description=f'Leveling role {role.mention} assigned to level {role_level}'))
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
        """/ranklist
        Description:
            List leveling roles
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

        def newpage(title, level, role):
            embed = Embed(title=title,
            color=0xffcc50)
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
                        color=0xffcc50)
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
            
        paginator = Paginator(
            client=self.bot, 
            pages=embeds,
            timeout_interval=80,
            show_select_menu=False)
        await paginator.send(ctx)
    
    @leveling.subcommand(sub_cmd_name='removerole', sub_cmd_description="allow's me to remove leveling roles")
    @role()
    async def leveling_remove_role(self, ctx:InteractionContext, role: OptionType.ROLE=None):
        """/leveling removerole

        Args:
            role (OptionType.ROLE, optional): Role to remove from leveling.
        """
        await ctx.defer()
        if role is None:
            await ctx.send('you have to include a role')
            return
        
        check = await db.leveling_roles.find_one({'guildid':ctx.guild.id, 'roleid':role.id})
        if check is None:
            await ctx.send(embed=Embed(color=0xDD2222, description=f':x: Leveling role {role.mention} is not assigned to a level'))
        else:
            await ctx.send(embed=Embed(color=0xffcc50, description=f'Leveling role {role.mention} removed from level {check.level}'))
            await check.delete()
        
        for member in ctx.guild.members:
            if role in member.roles:
                await member.remove_role(role)

    @slash_command(name='rank', description='check your leveling statistics')
    @member()
    async def newrank(self, ctx: SlashContext, member:OptionType.USER=None):
        """/rank
        Description:
            Generates leveling info card

        Args:
            member (OptionType.USER, optional): Member, defaults to member executing the command
        """
        await ctx.defer() # defer the response to avoid timeout
        if member is None: # if no member parameter is provided, use the author of the command
            member = ctx.author
        
        levels = await db.leveling.find_one({'guildid':ctx.guild_id, 'memberid':member.id}) # get the leveling data for the member
        if levels is None: # if no leveling data is found, send a message and return
            await ctx.send("You don't have any xp yet. You can start having conversations with people to gain xp.", ephemeral=True)
            return

        level_stats = await db.levelingStats.find_one({'level':levels.level}) # get the leveling stats for the member's current level
        if (levels.display_name is None) or (levels.display_name != member.display_name): # if the member's display name has changed, update it in the database
            levels.display_name = member.display_name
            await levels.save()
        
        def getPercent(first, second): # helper function to calculate percentage
            return first / second * 100
        percent = getPercent(levels.xp_to_next_level,level_stats.xp_to_next_level) # calculate the percentage of xp towards the next level
        def findx(percentage): # helper function to calculate the progress bar width
            if percentage == 0:
                return 1
            return 550/(100/percentage)

        if member.guild_avatar is not None: # get the member's avatar url
            avatarurl = f'{member.guild_avatar.url}.png'
        else:
            avatarurl = f'{member.avatar.url}.png'
        
        def round(im): # helper function to round the member's avatar
            im = im.resize((210*16,210*16), resample=Image.ANTIALIAS)
            mask = Image.new("L", im.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0,0)+im.size, fill=255)
            out = ImageOps.fit(im, mask.size, centering=(0,0))
            out.putalpha(mask)
            image = out.resize((210,210), resample=Image.ANTIALIAS).convert("RGBA")
            return image

        IW, IH = (956, 435) # set the image width and height
        aspect_ratio = IW/IH

        if levels.lc_background is not None: # get the background image for the level card
            try:
                background = Image.open(requests.get(f'{levels.lc_background}', stream=True).raw).crop((0,0,IW,IH)).convert("RGBA")
            except:
                background = Image.open(requests.get('https://i.imgur.com/4yzKbQo.png', stream=True).raw).convert("RGBA")
        else:
            background = Image.open(requests.get('https://i.imgur.com/4yzKbQo.png', stream=True).raw).convert("RGBA")

        overlay = Image.open(requests.get('https://i.imgur.com/fsuIzSv.png', stream=True).raw).convert("RGBA") # add an overlay to the background
        background.paste(overlay, (0, 0), overlay)

        try:
            pfp = Image.open(requests.get(avatarurl, stream=True).raw).resize((230,230)).convert("RGBA") # get the member's avatar image
        except:
            pfp = Image.open(requests.get('https://cdn.discordapp.com/embed/avatars/1.png', stream=True).raw).resize((230,230)).convert("RGBA")
        pfp = round(pfp) # round the member's avatar
        background.paste(pfp, (78, 115), pfp) # paste the avatar onto the background

        def draw_progress_bar(fx): # helper function to draw the progress bar
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

        fx = findx(int(percent)) # calculate the progress bar width
        progress_bar = draw_progress_bar(int(fx)) # draw the progress bar
        background.paste(progress_bar, (330, 370), progress_bar) # paste the progress bar onto the background

        def rectangle_fill(im): # helper function to fill the background with a rectangle
            mask = Image.new("L", im.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rectangle((0,0)+im.size, fill=255)
            out = ImageOps.fit(im, mask.size, centering=(0,0))
            out.putalpha(mask)
            return out

        background = rectangle_fill(background) # fill the background with a rectangle

        font = ImageFont.truetype('Everson-Mono-Bold.ttf', 45) # set the font for the text

        I1 = ImageDraw.Draw(background)

        lvlfont = ImageFont.truetype('Everson-Mono-Bold.ttf', 45)
        I1.text((73,352), f'LVL:{levels.level}', font=lvlfont, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255)) # add the member's level to the level card

        lvlmsg = f'XP: {levels.xp_to_next_level}/{level_stats.xp_to_next_level}\nTotal XP: {levels.total_xp}\nMessages: {levels.messages}' # create the level message
        I1.text((341,110), lvlmsg, font=font, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255)) # add the level message to the level card

        namefont = ImageFont.truetype('Everson-Mono-Bold.ttf', 50)
        name = f'{member.display_name}'
        if len(name) > 27: # shorten the member's name if it is too long
            name = name[:-4]

        I1.text((73,28), name, font=namefont, stroke_width=2, stroke_fill=(30, 27, 26), fill=(255, 255, 255)) # add the member's name to the level card
        background.save(f'levelcard_{member.id}.png') # save the level card as a file
        await ctx.send(file=f"levelcard_{member.id}.png") # send the level card as a file
        os.remove(f'levelcard_{member.id}.png') # remove the level card file

    @slash_command(name='leaderboard', description='check the servers leveling leaderboard')
    async def leaderboard(self, ctx: InteractionContext):
        """/leaderboard
        Description:
            Sends a button to the leaderboard for the server the command is executed in.
        """
        components = Button(
            style=ButtonStyle.URL,
            label="Click Me!",
            url=f"https://www.beni2am.space/melody/leaderboard/{ctx.guild_id}/",
        )
        await ctx.send("A button to the web leaderboard!", components=components)
        
def setup(bot):
    Levels(bot)