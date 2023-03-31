from interactions.client.errors import *
import re
from typing import Awaitable, Callable, Union
from interactions import Permissions
from interactions.models.discord.snowflake import Snowflake_Type, to_snowflake
from interactions.models.internal.context import BaseContext
from extentions.touk import BeanieDocuments as db

TYPE_CHECK_FUNCTION = Callable[[BaseContext], Awaitable[bool]]

class MissingPermissions(CommandException):
    """User is missing permissions"""

class RoleNotFound(CommandException):
    """Role was not found in the guild"""

class UserNotFound(CommandException):
    """User was not found in the guild"""

#class CommandOnCooldown(CommandException):
#    """Command is on cooldown"""

class MissingRole(CommandException):
    """Member is missing a role"""

class CommandNotFound(CommandException):
    """Command was not found"""

class UserInBlacklist(CommandException):
    """User is blacklisted from using this feature"""

class CommandNotActivatedInGuild(CommandException):
    """Command is not activated in a guild"""

class ExtensionNotActivatedInGuild(CommandException):
    """Extension is not activated in a guild"""

class EventNotActivatedInGuild(CommandException):
    """Event is not activated in a guild"""

async def has_perms(author, perm):
    adminrole = [role for role in author.roles if perm in role.permissions]
    if adminrole != []:
        return True
    
    raise MissingPermissions(f'{author}|{author.id} is missing permission {perm}')

def member_permissions(*permissions: Permissions) -> TYPE_CHECK_FUNCTION:
    """
    Check if member has any of the given permissions.
    
    Args:
        *permissions: The Permission(s) to check for
    """
    async def check(ctx: BaseContext) -> bool:
        if ctx.guild is None:
            return False
        if any(ctx.author.has_permission(p) for p in permissions):
            return True
        raise MissingPermissions(f'{ctx.author.display_name}|{ctx.author.id} is missing permissions')
    return check

def role_lock() -> TYPE_CHECK_FUNCTION:
    """
    Check if member has a role assigned to the command in the DB

    """
    async def check(ctx: BaseContext) -> bool:
        # await ctx.defer()
        if ctx.author.has_permission(Permissions.ADMINISTRATOR) == True:
            return True
        
        regx = {'$regex':f"^{re.escape(ctx.invoked_name)}$", '$options':'i'}
        roleid = await db.hasrole.find_one({"guildid":ctx.guild_id, "command":regx})
        if roleid is not None:
            role = ctx.guild.get_role(roleid.role)
            if role not in ctx.author.roles:
                raise MissingRole(f'{ctx.author} missing role {role.name}')
            else:
                return True
        elif roleid is None:
            return True
    return check


async def has_role(ctx):
    # await ctx.defer()
    
    regx = {'$regex':f"^{re.escape(ctx.invoked_name)}$", '$options':'i'}
    roleid = await db.hasrole.find_one({"guildid":ctx.guild_id, "command":regx})
    if roleid is not None:
        role = ctx.guild.get_role(roleid.role)
        if role not in ctx.author.roles:
            raise MissingRole(f'{ctx.author} missing role {role.name}')
        else:
            return True
    elif roleid is None:
        return True
    
async def is_extension_active(ctx):    
    
    commands = await db.prefixes.find_one({"guildid":ctx.guild.id})
    if ctx.invoked_name.lower() not in commands.activecogs.lower():
        raise ExtensionNotActivatedInGuild(f'{ctx.invoked_name} not activated for {ctx.guild}')
    return True

async def is_command_active(ctx):
    
    commands = await db.prefixes.find_one({"guildid":ctx.guild.id})
    if ctx.invoked_name.lower() not in commands.activecommands.lower():
        raise CommandNotActivatedInGuild(f'{ctx.invoked_name} not activated for {ctx.guild}')
    return True

async def is_event_active(guild, event: str):
    if guild is not None:
        commands = await db.prefixes.find_one({"guildid":guild.id})
        if event.lower() not in commands.activecommands.lower():
            return False#raise EventNotActivatedInGuild(f'{event} not activated for {guild}')
        return True

async def is_automod_event_active(guild, event: str):
    if guild is not None:
        events = await db.amConfig.find_one({"guild":guild.id})
        if events.active_events is None:
            return False
        if event not in events.active_events:
            return False
        return True

async def is_user_blacklisted_e(message):
    
    users = await db.userfilter.find_one({"guild":message.guild.id, "userid":message.author.id})
    if users.userid == message.author.id:
        raise UserInBlacklist(f'{message.author} has been blacklisted from using events')
    elif users.userid is None:
        return True
    return True

