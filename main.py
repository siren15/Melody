import os
import asyncio

from dis_snek import slash_command, InteractionContext, slash_option, OptionTypes
from dis_snek.client import Snake
from dis_snek.models.enums import Intents
from dis_snek.models.listener import listen
from extentions.src.customchecks import *
from dis_snek.models.discord_objects.embed import Embed

intents = Intents.DEFAULT
intents.GUILD_MEMBERS

async def unban_task():
    print('unban task working')
    db = await odm.connect()
    endtimes = await db.find(tempbans, {'endtime':{'$lte':datetime.now()}})
    for m in endtimes:
        try:
            guild = await bot.get_guild(m.guildid)
        except NotFound:
            print(f"[automod]|[unban_task]{m.guildid} not found in the guild list")
            await db.delete(m)
            return
        try:
            await guild.get_ban(m.user)
        except NotFound:
            print(f"[automod]|[unban_task]{m.user} not found in the ban list")
            await db.delete(m)
            return
        await guild.unban(m.user, '[automod]|[unban_task] ban time expired')
        await db.delete(m)

class CustomSnake(Snake):
    async def on_command_error(self, ctx: InteractionContext, error:Exception):
        if isinstance(error, MissingPermissions):
            embed = Embed(description=f":x: {ctx.author.mention} You don't have permissions to perform that action",
                          color=0xdd2e44)
            await ctx.send(embed=embed, ephemeral=True)
        
        if isinstance(error, MissingRole):
            db = await odm.connect()
            regx = re.compile(f"^{ctx.invoked_name}$", re.IGNORECASE)
            roleid = await db.find_one(hasrole, {"guildid":ctx.guild.id, "command":regx})
            if roleid != None:
                role = await ctx.guild.get_role(roleid.role)
                embed = Embed(description=f":x: {ctx.author.mention} You don't have role {role.mention} that's required to use this command.",
                              color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)
        
        if isinstance(error, RoleNotFound):
            embed = Embed(description=f":x: Couldn't find that role",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, UserNotFound):
            embed = Embed(description=f":x: User not found",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, CommandOnCooldown):
            embed = Embed(
                description=f":x: Command **{ctx.command.name}** on cooldown, try again later.",
                color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, ExtensionNotActivatedInGuild):
            embed = Embed(description=f":x: Module for this command is not activated in the guild.",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, CommandNotActivatedInGuild):
            embed = Embed(description=f":x: Command is not activated in the guild.",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
        
        if isinstance(error, UserInBlacklist):
            embed = Embed(description=f":x: {ctx.author.mention} You are blacklisted from using some commands",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

bot = CustomSnake(intents=intents, sync_interactions=True, delete_unused_application_cmds=True, default_prefix='p.')

@listen()
async def on_ready():
    print(f"[Logged in]: {bot.user}")
    while True:
        await unban_task()
        asyncio.sleep(60)
        continue

for filename in os.listdir('./extentions'):
    if filename.endswith('.py'):
        if (filename != 'mongo.py') and (filename != 'slash_options.py'):
            bot.load_extension(f'extentions.{filename[:-3]}')

bot.start(os.environ['pinetree_token'])
