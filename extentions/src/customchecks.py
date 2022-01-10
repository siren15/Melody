from dis_snek.errors import *
from .mongo import *
import re

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

async def has_role(ctx):
    db = await odm.connect()
    regx = re.compile(f"^{ctx.invoked_name}$", re.IGNORECASE)
    roleid = await db.find_one(hasrole, {"guildid":ctx.guild_id, "command":regx})
    if roleid != None:
        role = await ctx.guild.get_role(roleid.role)
        if role not in ctx.author.roles:
            raise MissingRole(f'{ctx.author} missing role {role.name}')
        else:
            return True
    elif roleid == None:
        return True
    
async def is_extension_active(ctx):    
    db = await odm.connect()
    commands = await db.find_one(prefixes, {"guildid":ctx.guild.id})
    if ctx.invoked_name.lower() not in commands.activecogs.lower():
        raise ExtensionNotActivatedInGuild(f'{ctx.invoked_name} not activated for {ctx.guild}')
    return True

async def is_command_active(ctx):
    db = await odm.connect()
    commands = await db.find_one(prefixes, {"guildid":ctx.guild.id})
    if ctx.invoked_name.lower() not in commands.activecommands.lower():
        raise CommandNotActivatedInGuild(f'{ctx.invoked_name} not activated for {ctx.guild}')
    return True

async def is_event_active(guild, event: str):
    db = await odm.connect()
    commands = await db.find_one(prefixes, {"guildid":guild.id})
    if event.lower() not in commands.activecommands.lower():
        raise EventNotActivatedInGuild(f'{event} not activated for {guild}')
    return True

async def is_user_blacklisted_e(message):
    db = await odm.connect()
    users = await db.find_one(userfilter, {"guild":message.guild.id, "userid":message.author.id})
    if users.userid == message.author.id:
        raise UserInBlacklist(f'{message.author} has been blacklisted from using events')
    elif users.userid == None:
        return True
    return True
