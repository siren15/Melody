import asyncio
import re
from PIL import Image, ImageOps, ImageDraw, ImageFont
import os
import requests
import math
import dataset

from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.discord_objects.channel import ChannelHistory
from dis_snek.models.discord import DiscordObject
from dis_snek.models.scale import Scale
from dis_snek.models.enums import Permissions
from dis_snek.models.listener import listen
from dis_snek import Snake, slash_command, InteractionContext, slash_option, OptionTypes
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *
from dis_snek.models.discord_objects.components import ActionRow, Button, spread_to_rows
from dis_snek.models.enums import ButtonStyles

wait_mem = []

class Levels(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @listen()
    async def on_message_create(self, event):
        message = event.message
        if message.author.bot:
            return
        #if (iscogactive(message.guild, 'leveling') == True) and (is_event_active(message.guild, 'leveling')):
        db = await odm.connect()
        lvls = await db.find_one(leveling_settings, {'guildid':message.guild.id})
        if lvls != None:
            if message.channel.id in lvls.no_xp_channel:
                return

        #check if enough time has passed since last message
        if message.author.id in wait_mem:
            return

        #check what xp the user has
        levels = await db.find_one(leveling, {'guildid':message.guild.id, 'memberid':message.author.id})
        if levels == None:
            await db.save(leveling(guildid=message.guild.id, memberid=message.author.id, total_xp=0, level=0, xp_to_next_level=0))
            return

        total_xp = levels.total_xp #total xp the user has
        lvl = levels.level #the level the user has
        if levels.xp_to_next_level == None:
            xp = 0
        else:
            xp = levels.xp_to_next_level #xp that the user has towards next level, this counter resets every time a new level is acquired

        min = 15
        max = 25
        multiplier = 1 #boost multiplier
        stats_db = dataset.connect('sqlite:///leveling_stats.db3')
        stats_db.begin()
        level_stats = stats_db['leveling'].find_one(level=lvl)
        decimal = level_stats['decimal']
        tot_xp_for_level = level_stats['totalxp']

        #xp_to_next_level = math.ceil(((4*((lvl*max) + (min+lvl)) - xp)/multiplier)*decimal)
        xp_to_next_level = level_stats['xptonextlevel']

        import random
        xp_to_give = random.randint(15, 25)
        new_total_xp = total_xp+xp_to_give
        if levels.messages == None:  
            number_of_messages = 1
        else:
            number_of_messages = levels.messages + 1
        
        if new_total_xp >= tot_xp_for_level:
            levels.level = lvl+1
            levels.xp_to_next_level = 0
            levels.total_xp = new_total_xp
            levels.messages = number_of_messages
            await db.save(levels)
            
            roles = await db.find_one(leveling_roles, {'guildid':message.guild.id, 'level':lvl+1})
            if roles != None:
                role = await message.guild.get_role(roles.roleid)
                if (role != None) and (role not in message.author.roles):
                    await message.author.add_role(role, '[bot]leveling role add')

        if (xp_to_next_level+xp) <= (xp+xp_to_give):
            levels.level = lvl+1
            levels.xp_to_next_level = 0
            levels.total_xp = new_total_xp
            levels.messages = number_of_messages
            await db.save(levels)
            
            roles = await db.find_one(leveling_roles, {'guildid':message.guild.id, 'level':lvl+1})
            if roles != None:
                role = await message.guild.get_role(roles.roleid)
                if (role != None) and (role not in message.author.roles):
                    await message.author.add_role(role, '[bot]leveling role add')

        else:
            levels.xp_to_next_level = xp+xp_to_give
            levels.total_xp = new_total_xp
            levels.messages = number_of_messages
            await db.save(levels)

        wait_mem.append(message.author.id)
        await asyncio.sleep(60)
        wait_mem.remove(message.author.id)
    
    @slash_command(name='leveling', sub_cmd_name='addrole', sub_cmd_description="[admin]allow's me to create leveling roles", scopes=[435038183231848449, 149167686159564800])
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
    
    @slash_command(name='leveling', sub_cmd_name='removerole', sub_cmd_description="[admin]allow's me to remove leveling roles", scopes=[435038183231848449, 149167686159564800])
    @role()
    async def leveling_add_role(self, ctx:InteractionContext, role: OptionTypes.ROLE=None):
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

    @slash_command(name='rank', description='check your levelling statistics', scopes=[435038183231848449, 149167686159564800])
    @member()
    async def rank(self, ctx: InteractionContext, member:OptionTypes.USER=None):
        await ctx.defer()
        if member == None:
            member = ctx.author
        db = await odm.connect()
        levels = await db.find_one(leveling, {'guildid':ctx.guild.id, 'memberid':member.id})
        if levels == None:
            await ctx.send("You don't have any xp yet. You can start having conversations with people to gain xp.", ephemeral=True)
            return

        min = 15
        max = 25
        multiplier = 1
        lvl = levels.level
        stats_db = dataset.connect('sqlite:///leveling_stats.db3')
        stats_db.begin()
        level_stats = stats_db['leveling'].find_one(level=lvl)
        decimal = level_stats['decimal']

        if levels.xp_to_next_level == None:
            xp = 0
        else:
            xp = levels.xp_to_next_level
        #xp_to_next_level = math.ceil(((4*((lvl*max) + (min+lvl)) - xp)/multiplier)*decimal)
        xp_to_next_level = level_stats['xptonextlevel']
        if member.top_role.color.value == 0:
            color = 0x0c73d3
        else:
            color = member.top_role.color
        embed = Embed(color=color,
        description=f"__**Leveling stats for {member.mention}**__\n\n**Level:** {levels.level}\n**XP:** {levels.xp_to_next_level}**/**{xp_to_next_level+xp}\n**Total XP:** {levels.total_xp}\n**Messages sent:** {levels.messages}")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

def setup(bot):
    Levels(bot)