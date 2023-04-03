# props to proxy and his way to connect to database https://github.com/artem30801/SkyboxBot/blob/master/main.py
import os
from typing import Optional
import asyncio
import motor

from beanie import init_beanie
from interactions import Client, Intents, listen, Embed, InteractionContext, AutoDefer, PermissionOverwrite
from interactions.client import utils
from utils.customchecks import *
from extentions.touk import BeanieDocuments as db, violation_settings
from interactions.api.events.discord import GuildLeft, GuildJoin
from dotenv import load_dotenv
load_dotenv()
database_url = os.getenv('database_url')
# database_url = os.getenv('mongodb://localhost:27017')

# import logging
# import interactions
# logging.basicConfig()
# cls_log = logging.getLogger(interactions.const.logger_name)
# cls_log.setLevel(logging.DEBUG)

intents = Intents.ALL
ad = AutoDefer(enabled=True, time_until_defer=1)


class CustomClient(Client):
    def __init__(self):
        super().__init__(
            intents=intents, 
            sync_interactions=True, 
            delete_unused_application_cmds=True, 
            default_prefix='+', 
            fetch_members=True, 
            auto_defer=ad,
            # asyncio_debug=True
        )
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.models = list()
        self.spotify = None

    async def startup(self):
        for filename in os.listdir('./extentions'):
            if filename.endswith('.py') and not filename.startswith('--'):
                self.load_extension(name=f'extentions.{filename[:-3]}')
                print(f'grew {filename[:-3]}')
        self.db = motor.motor_asyncio.AsyncIOMotorClient(database_url)
        await init_beanie(database=self.db.giffany, document_models=self.models)
        if __name__ == "__main__":
            await self.astart(os.getenv('amelody_token'))
        else:
            await self.astart(os.getenv('bot_token'))
    
    @listen()
    async def on_ready(self):
        print(f"[Logged in]: {self.user}")
        guild = self.get_guild(435038183231848449)
        channel = guild.get_channel(932661537729024132)
        await channel.send(f'[Logged in]: {self.user}')

    @listen()
    async def on_guild_join(self, event:GuildJoin):
        # add guild to database
        if await db.prefixes.find_one({'guildid':event.guild.id}) is None:
            await db.prefixes(guildid=event.guild.id, mods=[]).insert()
            guild = self.get_guild(435038183231848449)
            channel = guild.get_channel(932661537729024132)
            await channel.send(f'I was added to {event.guild.name}|{event.guild.id}')
        if await db.automod_config.find_one({'guildid':event.guild.id}) is None:
            violations = violation_settings(violation_count=None, violation_punishment=None)
            await db.automod_config(guildid=event.guild.id, banned_words=violations, phishing=violations).insert()
        if await db.leveling_settings.find_one({'guildid':event.guild.id}) is None:
            await db.leveling_settings(guildid=event.guild.id, min=15, max=25, multiplier=1, ignored_channels=[], ignored_roles=[], ignored_users=[]).insert()
        # if await db.modmail_conf.find_one({'guildid':event.guild.id}) is None:
        #     everyone_role_po = PermissionOverwrite(id=event.guild.id, type=0).for_target(utils.find(lambda r: r.name == '@everyone', event.guild.roles))
        #     everyone_role_po.add_denies(Permissions.VIEW_CHANNEL, Permissions.READ_MESSAGE_HISTORY)
        #     melody_po = PermissionOverwrite(id=event.guild.id, type=0).for_target(self.user)
        #     melody_po.add_allows(Permissions.VIEW_CHANNEL, Permissions.READ_MESSAGE_HISTORY, Permissions.USE_PRIVATE_THREADS, Permissions.MANAGE_THREADS)
            # modmail_channel = utils.find(lambda m: m.name == 'modmail', event.guild.channels)
            # if modmail_channel is None:
            #     modmail_channel = await event.guild.create_text_channel(name='modmail', permission_overwrites=[everyone_role_po, melody_po])
            # modmail_log_channel = utils.find(lambda m: m.name == 'modmail-log', event.guild.channels)
            # if modmail_log_channel is None:
            #     modmail_log_channel = await event.guild.create_text_channel(name='modmail-log', permission_overwrites=[everyone_role_po, melody_po])
            # await db.modmail_conf(guildid=event.guild.id, channelid=modmail_channel.id, logchannel=modmail_log_channel.id).insert()
    
    @listen()
    async def on_guild_leave(self, event:  GuildLeft):
        if event.guild.id == 149167686159564800:
            return
        for document in self.models:
            async for entry in document.find({'guildid': event.guild_id}):
                await entry.delete()
            async for entry in document.find({'guild_id': event.guild_id}):
                await entry.delete()
        print(f'Guild {event.guild_id} was removed.')

    async def on_command_error(self, ctx: InteractionContext, error:Exception):
        if isinstance(error, MissingPermissions):
            embed = Embed(description=f":x: {ctx.author.mention} You don't have permissions to perform that action",
                          color=0xdd2e44)
            await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, MissingRole):
            
            regx = {'$regex':f"^{re.escape(ctx.invoked_name)}$", '$options':'i'}
            roleid = await db.hasrole.find_one({"guildid":ctx.guild.id, "command":regx})
            if roleid is not None:
                role = ctx.guild.get_role(roleid.role)
                embed = Embed(description=f":x: {ctx.author.mention} You don't have role {role.mention} that's required to use this command.",
                              color=0xDD2222)
                return await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, RoleNotFound):
            embed = Embed(description=f":x: Couldn't find that role",
                          color=0xDD2222)
            return await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, UserNotFound):
            embed = Embed(description=f":x: User is not a member of this server ",
                          color=0xDD2222)
            return await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, CommandOnCooldown):
            embed = Embed(
                description=f":x: Command **{ctx.invoked_name}** on cooldown, try again later.",
                color=0xDD2222)
            return await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, ExtensionNotActivatedInGuild):
            embed = Embed(description=f":x: Module for this command is not activated in the server.",
                          color=0xDD2222)
            return await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, CommandNotActivatedInGuild):
            embed = Embed(description=f":x: Command is not activated in the server.",
                          color=0xDD2222)
            return await ctx.send(embed=embed, ephemeral=True)

        if isinstance(error, UserInBlacklist):
            embed = Embed(description=f":x: {ctx.author.mention} You are not allowed to use this command",
                          color=0xDD2222)
            return await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = Embed(description=f":x: An error occured while trying to execute `{ctx.invoked_name}` command: ```{error}```",
                          color=0xDD2222)
            await ctx.send(embed=embed, ephemeral=True)
            # if ctx.guild_id != 435038183231848449:
            #     guild = self.get_guild(435038183231848449)
            #     channel = guild.get_channel(932661537729024132)
            #     invite = await ctx.channel.create_invite(reason=f'[AUTOMOD]invite created due to error occuring')
            #     await channel.send(f"<@400713431423909889> An error occured while {ctx.author}({ctx.author.id}) tried to execute `{ctx.invoked_name}` command in {ctx.channel.name} from `{ctx.guild.name}`: ```{error}```\n{invite}")
        
    def add_model(self, model):
        self.models.append(model)

bot = CustomClient()
if __name__ == "__main__":
    asyncio.run(bot.startup())