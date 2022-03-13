# props to proxy and his way to connect to database https://github.com/artem30801/SkyboxBot/blob/master/main.py
import os
import asyncio
from typing import Optional
import motor

from beanie import Indexed, init_beanie
from dis_snek import Snake, Intents, listen, Embed, InteractionContext, AutoDefer
from utils.customchecks import *
from extentions.touk import BeanieDocuments as db
from dis_snek.client.errors import NotFound

# import logging
# import dis_snek
# logging.basicConfig()
# cls_log = logging.getLogger(dis_snek.const.logger_name)
# cls_log.setLevel(logging.DEBUG)

intents = Intents.ALL
ad = AutoDefer(enabled=True, time_until_defer=1.2)

class CustomSnake(Snake):
    def __init__(self):
        super().__init__(
            intents=intents, 
            sync_interactions=True, 
            delete_unused_application_cmds=True, 
            default_prefix='p.', 
            fetch_members=True, 
            auto_defer=ad
        )
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.models = list()

    async def startup(self):
        for filename in os.listdir('./extentions'):
            if filename.endswith('.py') and not filename.startswith('--'):
                self.load_extension(f'extentions.{filename[:-3]}')
                print(f'grew {filename[:-3]}')
        self.db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['pt_mongo_url'])
        await init_beanie(database=self.db.giffany, document_models=self.models)
        await self.astart(os.environ['tyrone_token'])
    
    @listen()
    async def on_ready(self):
        print(f"[Logged in]: {self.user}")
        guild = self.get_guild(435038183231848449)
        channel = guild.get_channel(932661537729024132)
        await channel.send(f'[Logged in]: {self.user}')

    @listen()
    async def on_guild_join(self, event):
        checkserver = await db.prefixes.find_one({'guildid':event.guild.id})
        if checkserver is None:
            #add server to database
            await db.prefixes(guildid=event.guild.id, prefix='p.').insert()
            guild = self.get_guild(435038183231848449)
            channel = guild.get_channel(932661537729024132)
            await channel.send(f'I was added to {event.guild.name}|{event.guild.id}')

    async def on_command_error(self, ctx: InteractionContext, error:Exception):
        if isinstance(error, MissingPermissions):
            embed = Embed(description=f":x: {ctx.author.mention} You don't have permissions to perform that action",
                          color=0xdd2e44)
            await ctx.send(embed=embed, ephemeral=True)

        elif isinstance(error, MissingRole):
            
            regx = {'$regex':f"^{ctx.invoked_name}$", '$options':'i'}
            roleid = await db.hasrole.find_one({"guildid":ctx.guild.id, "command":regx})
            if roleid is not None:
                role = ctx.guild.get_role(roleid.role)
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
        else:
        #     embed = Embed(description=f":x: An error occured while trying to execute `{ctx.invoked_name}` command: ```{error}```",
        #                   color=0xDD2222)
        #     await ctx.send(embed=embed, ephemeral=True)
            if ctx.guild_id != 435038183231848449:
                guild = self.get_guild(435038183231848449)
                channel = guild.get_channel(932661537729024132)
                await channel.send(f"<@400713431423909889> An error occured while trying to execute `{ctx.invoked_name}` command in `{ctx.guild.name}`: ```{error}```")
        
    def add_model(self, model):
        self.models.append(model)

if __name__ == "__main__":
    bot = CustomSnake()
    asyncio.run(bot.startup())