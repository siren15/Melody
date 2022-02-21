import os
import asyncio

from dis_snek import Snake, Intents, listen, Embed, InteractionContext, AutoDefer
from extentions.src.customchecks import *
from extentions.src.mongo import *
from dis_snek.client.errors import NotFound

# import logging
# import dis_snek
# logging.basicConfig()
# cls_log = logging.getLogger(dis_snek.const.logger_name)
# cls_log.setLevel(logging.DEBUG)

intents = Intents.ALL

class CustomSnake(Snake):
    async def on_command_error(self, ctx: InteractionContext, error:Exception):
        if isinstance(error, MissingPermissions):
            embed = Embed(description=f":x: {ctx.author.mention} You don't have permissions to perform that action",
                          color=0xdd2e44)
            await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, MissingRole):
            db = await odm.connect()
            regx = re.compile(f"^{ctx.invoked_name}$", re.IGNORECASE)
            roleid = await db.find_one(hasrole, {"guildid":ctx.guild.id, "command":regx})
            if roleid != None:
                role = await ctx.guild.get_role(roleid.role)
                embed = Embed(description=f":x: {ctx.author.mention} You don't have role {role.mention} that's required to use this command.",
                              color=0xDD2222)
                await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, RoleNotFound):
            embed = Embed(description=f":x: Couldn't find that role",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, UserNotFound):
            embed = Embed(description=f":x: User is not a member of this server ",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, CommandOnCooldown):
            embed = Embed(
                description=f":x: Command **{ctx.invoked_name}** on cooldown, try again later.",
                color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, ExtensionNotActivatedInGuild):
            embed = Embed(description=f":x: Module for this command is not activated in the server.",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, CommandNotActivatedInGuild):
            embed = Embed(description=f":x: Command is not activated in the server.",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, UserInBlacklist):
            embed = Embed(description=f":x: {ctx.author.mention} You are not allowed to use this command",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
        # else:
        #     embed = Embed(description=f":x: An error occured while trying to execute `{ctx.invoked_name}` command: ```{error}```",
        #                   color=0xDD2222)
        #     await ctx.send(embed=embed, ephemeral=True)
        #     if ctx.guild_id != 435038183231848449:
        #         guild = await bot.get_guild(435038183231848449)
        #         channel = guild.get_channel(932661537729024132)
        #         await channel.send(f"<@400713431423909889> An error occured while trying to execute `{ctx.invoked_name}` command in `{ctx.guild.name}`: ```{error}```")


ad = AutoDefer(enabled=True, time_until_defer=0)
bot = CustomSnake(intents=intents, 
                  sync_interactions=True, 
                  delete_unused_application_cmds=True, 
                  default_prefix='p.', 
                  fetch_members=True, 
                  auto_defer=ad,
                # asyncio_debug=True,
                  )

@listen()
async def on_ready():
    print(f"[Logged in]: {bot.user}")
    guild = await bot.get_guild(435038183231848449)
    channel = guild.get_channel(932661537729024132)
    await channel.send(f'[Logged in]: {bot.user}')

@listen()
async def on_guild_join(event):
    db = await odm.connect()
    checkserver = await db.find_one(prefixes, {'guildid':event.guild.id})
    if checkserver == None:
        #add server to database
        await db.save(prefixes(guildid=event.guild.id, prefix='p.'))
        guild = await bot.get_guild(435038183231848449)
        channel = guild.get_channel(932661537729024132)
        await channel.send(f'I was added to {event.guild.name}|{event.guild.id}')

for filename in os.listdir('./extentions'):
    if filename.endswith('.py'):
        bot.load_extension(f'extentions.{filename[:-3]}')

bot.start(os.environ['tyrone_token'])
