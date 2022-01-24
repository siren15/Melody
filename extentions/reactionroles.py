import random
import asyncio

from dis_snek.api.events.discord import *
from dis_snek import Snake, Scale, Permissions, listen, Message, Embed, slash_command, InteractionContext
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *

def random_string_generator():
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    result=''
    for i in range(0, 8):
        result += random.choice(characters)
    return result

class ReactionRoles(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot

    @slash_command(name='reactionrole', sub_cmd_name='create' , sub_cmd_description='[admin]Create a reactionrole', description="[admin]Create and edit reactionroles")
    async def reaction_role_create(self, ctx:InteractionContext):
        await ctx.defer()
        perms = await has_perms(ctx.author, Permissions.ADMINISTRATOR)
        if (perms == True):
            def check(event:Message) -> bool:
                return (event.message.channel == ctx.channel) and (event.message.author == ctx.author)

            choose_emoji_m = await ctx.send('Choose a reaction role emoji:')

            rr_emoji = False
            while rr_emoji == False:
                try:
                    emoji = await self.bot.wait_for('message_create', timeout=120, checks=check)

                except asyncio.TimeoutError:
                    await ctx.send(f":x: Uh oh, {ctx.author.mention}! You took longer than 2 minutes to respond, creation cancelled.", ephemeral=True)

                if emoji.message.content.lower() == "abort":
                    embed = Embed(
                        description=":x: Creation process aborted",
                        color=0xDD2222)
                    await ctx.send(embed=embed)
                    return
                else:
                    await ctx.send(emoji.message.content)

    #modes: 1 = react to get a role - unreact to remove the role, 2 = react to get a role - not possible to remove the role, 3 = only one role allowed from the message

    @listen()
    async def on_message_reaction_add(self, event:MessageReactionAdd):
        #modes 1 and 2
        guild = event.message.guild
        message = event.message
        emoji = event.emoji
        member = event.message.author

        db = await odm.connect()
        rr = await db.find_one(reactionroles, {'guildid': guild.id, 'channelid': message.channel.id, 'reactionmessageid': message.id, 'reactionemoji': emoji.name})

        if rr == None:
            return
        else:
            if rr.mode != 3:
                rrid = rr.reactionroleid
                reqrid = rr.requirementroleid
                igrid = rr.ignoredroleid
                member_roles = [role.id for role in member.roles]
                role = await guild.get_role(rrid)
                if role != None:
                    if igrid == None:
                        if reqrid == None:
                            if rrid not in member_roles:
                                await member.add_role(role, 'reaction role add')
                        else:
                            if (reqrid in member_roles) and (rrid not in member_roles):
                                await member.add_role(role, 'reaction role add')
                    else:
                        if igrid in member_roles:
                            return
                        elif igrid not in member_roles:
                            if reqrid == None:
                                if rrid not in member_roles:
                                    await member.add_role(role, 'reaction role add')
                            else:
                                if (reqrid in member_roles) and (rrid not in member_roles):
                                    await member.add_role(role, 'reaction role add')
                else:
                    raise RoleNotFound()
    
    @listen()
    async def on_message_reaction_add(self, event:MessageReactionAdd):
        #mode 3
        guild = event.message.guild
        message = event.message
        emoji = event.emoji
        member = event.message.author

        db = await odm.connect()
        rr = await db.find_one(reactionroles, {'guildid': guild.id, 'channelid': message.channel.id, 'reactionmessageid': message.id, 'reactionemoji': emoji.name, 'mode': 3})

        if rr == None:
            return
        else:
            all_roles = await db.find(reactionroles, {'guildid': guild.id, 'channelid': message.channel.id, 'reactionmessageid': message.id, 'mode': 3})
            all_roles = [roles.reactionroleid for roles in all_roles]
            rrid = rr.reactionroleid
            reqrid = rr.requirementroleid
            igrid = rr.ignoredroleid
            member_roles = [role.id for role in member.roles]
            role = await guild.get_role(rrid)
            if role != None:
                if igrid in member_roles:
                    return
                if (reqrid == None) or (reqrid in member_roles):
                    if rrid not in member_roles:
                        old_role = [role for role in member.roles if role.id in all_roles]
                        for old_role in old_role:
                            old_role = old_role
                        if old_role in member.roles:
                            await member.remove_roles(old_role)
                        await member.add_roles(role)
            else:
                raise RoleNotFound()
    
    @listen()
    async def on_message_reaction_remove(self, event:MessageReactionRemove):
        #modes 1 and 3
        guild = event.message.guild
        message = event.message
        emoji = event.emoji
        member = event.message.author

        db = await odm.connect()
        rr = await db.find_one(reactionroles, {'guildid': guild.id, 'channelid': message.channel.id, 'reactionmessageid': message.id, 'reactionemoji': emoji.name})

        if rr == None:
            return
        else:
            if rr.mode != 2:
                rrid = rr.reactionroleid
                reqrid = rr.requirementroleid
                igrid = rr.ignoredroleid
                member_roles = [role.id for role in member.roles]
                role = await guild.get_role(rrid)
                if role != None:
                    if igrid == None:
                        if reqrid == None:
                            if rrid in member_roles:
                                await member.remove_role(role, 'reaction role remove')
                        else:
                            if (reqrid in member_roles) and (rrid in member_roles):
                                await member.remove_role(role, 'reaction role remove')
                    else:
                        if igrid in member_roles:
                            return
                        elif igrid not in member_roles:
                            if reqrid == None:
                                if rrid in member_roles:
                                    await member.remove_role(role, 'reaction role remove')
                            else:
                                if (reqrid in member_roles) and (rrid in member_roles):
                                    await member.remove_role(role, 'reaction role remove')
                else:
                    raise RoleNotFound()
            else:
                return        

def setup(bot):
    ReactionRoles(bot)