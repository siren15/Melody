# inspired by https://github.com/artem30801/SkyboxBot/blob/master/main.py
from bson.int64 import Int64 as int64
from naff import Client, Extension, slash_command, InteractionContext, Embed
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from beanie import TimeSeriesConfig, Granularity
from pydantic import Field
from beanie import Document as BeanieDocument

class Document(BeanieDocument):
    def __hash__(self):
        return hash(self.id)

class violation_settings(BaseModel):
    violation_count: Optional[int64] = None
    violation_punishment: Optional[str] = None
    class Config:
        orm_mode = True

class BeanieDocuments():
    class banned_words(Document):
        guildid: Optional[int64] = None
        exact: Optional[str] = None
        partial: Optional[str] = None

    class giveaways(Document):
        giveawaynum: Optional[str] = None
        guildid: Optional[int64] = None
        authorid: Optional[int64] = None
        endtime: Optional[datetime] = None
        giveawaychannelid: Optional[int64] = None
        giveawaymessageid: Optional[int64] = None
        reqrid:	Optional[str] = None
        winnersnum:	Optional[str] = None
        prize: Optional[str] = None
        starttime: Optional[datetime] = None
        status: Optional[str] = None

    class giveyou(Document):
        guildid: Optional[int64] = None
        name: Optional[str] = None
        roleid:	Optional[int64] = None

    class hasrole(Document):
        guildid: Optional[int64] = None
        command: Optional[str] = None
        role: Optional[int64] = None

    class leveling_settings(Document):
        guildid: Optional[int64] = None
        min: Optional[int64] = None
        max: Optional[int64] = None
        multiplier: Optional[int64] = None
        no_xp_channel: Optional[int64] = None

    class leveling(Document):
        guildid: Optional[int64] = None
        display_name: Optional[str] = None
        memberid: Optional[int64] = None
        level: Optional[int64] = None
        xp_to_next_level: Optional[int64] = None
        total_xp: Optional[int64] = None
        messages: Optional[int64] = None
        decimal: Optional[int64] = None
        lc_background: Optional[str] = None
        
    class leveling_roles(Document):
        guildid: Optional[int64] = None
        roleid: Optional[int64] = None
        level: Optional[int64] = None

    class limbo(Document):
        guildid: Optional[int64] = None
        userid: Optional[int64] = None
        roles: Optional[str] = None
        reason: Optional[str] = None

    class logs(Document):
        guild_id: Optional[int64] = None
        channel_id: Optional[int64] = None

    class mutes(Document):
        guildid: Optional[int64] = None
        user: Optional[int64] = None
        roles: Optional[str] = None
        starttime: Optional[datetime] = None
        endtime: Optional[datetime] = None

    class persistentroles(Document):
        guildid: Optional[int64] = None
        userid: Optional[int64] = None
        roles: Optional[str] = None

    class persistent_roles(Document):
        guildid: Optional[int64] = None
        user: Optional[int64] = None
        roles: Optional[str] = None

    class persistent_roles_settings(Document):
        guildid: Optional[int64] = None
        roleid: Optional[int64] = None

    class prefixes(Document):
        guildid: Optional[int64] = None
        prefix: Optional[str] = None
        activecogs: Optional[str] = None
        activecommands: Optional[str] = None

    class strikes(Document):
        strikeid: Optional[str] = None
        guildid: Optional[int64] = None
        user: Optional[int64] = None
        moderator: Optional[str] = None
        action: Optional[str] = None
        reason: Optional[str] = None
        day: Optional[str] = None
        automod: Optional[bool] = False

    class tag(Document):
        guild_id: Optional[int64] = None
        author_id: Optional[int64] = None
        names: Optional[str] = None
        content: Optional[str] = None
        attachment_url: Optional[str] = None
        no_of_times_used: Optional[int64] = None
        creation_date: Optional[datetime] = None
        owner_id: Optional[int64] = None

    class tempbans(Document):
        guildid: Optional[int64] = None
        user: Optional[int64] = None
        starttime: Optional[datetime] = None
        endtime: Optional[datetime] = None
        banreason: Optional[str] = None

    class userfilter(Document):
        guild: Optional[int64] = None
        userid: Optional[int64] = None

    class welcome_msg(Document):
        guildid: Optional[int64] = None
        channelid: Optional[int64] = None
        message: Optional[str] = None
        role: Optional[int64] = None
        background_url: Optional[str] = None
    
    class special_welcome_msg(Document):
        guildid: Optional[int64] = None
        channelid: Optional[int64] = None
        message: Optional[str] = None
        background_url: Optional[str] = None
    
    class leave_msg(Document):
        guildid: Optional[int64] = None
        channelid: Optional[int64] = None
        message: Optional[str] = None

    class button_roles(Document):
        guildid: Optional[int64] = None
        button_id: Optional[str] = None
        channelid: Optional[int64] = None
        msg_id: Optional[int64] = None
        roleid: Optional[int64] = None
        requirement_role_id: Optional[int64] = None
        ignored_role_id: Optional[int64] = None
        mode: Optional[int64] = None

    class levelingstats(Document):
        lvl: Optional[int64] = None
        xptolevel: Optional[int64] = None
        totalxp: Optional[int64] = None

    class levelwait(Document):
        guildid: Optional[int64] = None
        user: Optional[int64] = None
        starttime: Optional[datetime] = None
        endtime: Optional[datetime] = None
    
    class automod_config(Document):
        guildid: Optional[int64] = None
        ignored_channels: Optional[str] = None
        ignored_roles: Optional[str] = None
        ignored_users: Optional[str] = None
        phishing: violation_settings
        banned_words: violation_settings
        ban_time: Optional[int64] = None
        mute_time: Optional[int64] = None
    
    class levelingStats(Document):
        level: Optional[int64] = None
        xp_to_next_level: Optional[int64] = None
        total_xp: Optional[int64] = None
    
    class dashSession(Document):
        sessionid: str
        user: Dict
        guilds: List
        token: Dict
        csrf: str
        ts: datetime = Field(default_factory=datetime.now)

        class Settings:
            timeseries = TimeSeriesConfig(
                time_field="ts",
                meta_field="sessionid",
                expire_after_seconds=7200
            )

class BeanieDocumentsExtension(Extension):
    def __init__(self, bot: Client):
        self.bot = bot

    @slash_command(name='btest', description='beanie test', scopes=[435038183231848449,149167686159564800])
    async def beanie_test(self, ctx:InteractionContext):
        if ctx.author.id != 400713431423909889:
            return ctx.channel.send(f"{ctx.author.mention} You can't do that! Criminal scum!")
        doc = await BeanieDocuments.prefixes.find_one({'guildid':ctx.guild_id})
        await ctx.send(f'{doc.activecommands}\n{doc.activecogs}')
    
    # @slash_command(name='xpfix', scopes=[149167686159564800])
    # async def xpfix(self, ctx: InteractionContext):
    #     await ctx.defer()
    #     if ctx.author.id != 400713431423909889:
    #         return ctx.channel.send(f"{ctx.author.mention} You can't do that! Criminal scum!")

    #     guild = self.bot.get_guild(149167686159564800)
    #     users = [user for user in guild.members if user.has_role(569285116321595403)]
    #     for user in users:
    #         levels = await BeanieDocuments.leveling.find_one({'guildid':guild.id, 'memberid':user.id})
    #         if levels is not None:
    #             user_roles = [role.id for role in user.roles]
    #             if 569285116321595403 in user_roles:
    #                 lvl = 5
    #                 messages = 58
    #             if 625728559977070632 in user_roles:
    #                 lvl = 10
    #                 messages = 187
    #             if 565761243894251520 in user_roles:
    #                 lvl = 15
    #                 messages = 473
    #             if 280403353098256384 in user_roles:
    #                 lvl = 20
    #                 messages = 954
    #             if 319232041872785408 in user_roles:
    #                 lvl = 30
    #                 messages = 2701
    #             if 427141870490222593 in user_roles:
    #                 lvl = 35
    #                 messages = 4067
    #             if 569286668184584203 in user_roles:
    #                 lvl = 40
    #                 messages = 5828
    #             if 573205670908919817 in user_roles:
    #                 lvl = 50
    #                 messages = 10735
    #             if 573210014223826954 in user_roles:
    #                 lvl = 60
    #                 messages = 17822
    #             if 953358137849708624 in user_roles:
    #                 lvl = 70
    #                 messages = 27489
    #             if 953359337781329961 in user_roles:
    #                 lvl = 80
    #                 messages = 40136
    #             if 953359947683475476 in user_roles:
    #                 lvl = 90
    #                 messages = 56163
    #             if 953360704403042384 in user_roles:
    #                 lvl = 100
    #                 messages = 75970
    #             if 953361613002522664 in user_roles:
    #                 lvl = 110
    #                 messages = 99957
    #             if 953362463477362768 in user_roles:
    #                 lvl = 120
    #                 messages = 128524
    #             if levels.messages is not None:
    #                 if levels.messages > messages:
    #                     messages = levels.messages
    #             if levels.level > lvl:
    #                 lvl = levels.level
    #             level_stats = await BeanieDocuments.levelingStats.find_one({'level':lvl})
    #             levels.level = lvl
    #             if levels.xp_to_next_level is None:
    #                 xptnl = 0
    #             elif levels.xp_to_next_level > 0:
    #                 xptnl = levels.xp_to_next_level
    #             else:
    #                 xptnl = 0
    #             levels.xp_to_next_level = xptnl
    #             levels.total_xp = level_stats.total_xp + xptnl
    #             await levels.save()
    #             print(f"guildid={guild.id}, memberid={user.id}, level={lvl}, xp_to_next_level={xptnl}, total_xp={level_stats.total_xp + xptnl}, messages={messages}")
    #     await ctx.send('done')

def setup(bot):
    BeanieDocumentsExtension(bot)
    bot.add_model(BeanieDocuments.dashSession)
    bot.add_model(BeanieDocuments.automod_config)
    bot.add_model(BeanieDocuments.levelingStats)
    bot.add_model(BeanieDocuments.banned_words)
    bot.add_model(BeanieDocuments.giveaways)
    bot.add_model(BeanieDocuments.giveyou)
    bot.add_model(BeanieDocuments.hasrole)
    bot.add_model(BeanieDocuments.leveling)
    bot.add_model(BeanieDocuments.leveling_roles)
    bot.add_model(BeanieDocuments.leveling_settings)
    bot.add_model(BeanieDocuments.levelingstats)
    bot.add_model(BeanieDocuments.levelwait)
    bot.add_model(BeanieDocuments.limbo)
    bot.add_model(BeanieDocuments.logs)
    bot.add_model(BeanieDocuments.mutes)
    bot.add_model(BeanieDocuments.persistent_roles_settings)
    bot.add_model(BeanieDocuments.persistent_roles)
    bot.add_model(BeanieDocuments.prefixes)
    bot.add_model(BeanieDocuments.mutes)
    bot.add_model(BeanieDocuments.tag)
    bot.add_model(BeanieDocuments.tempbans)
    bot.add_model(BeanieDocuments.button_roles)
    bot.add_model(BeanieDocuments.persistentroles)
    bot.add_model(BeanieDocuments.userfilter)
    bot.add_model(BeanieDocuments.welcome_msg)
    bot.add_model(BeanieDocuments.special_welcome_msg)
    bot.add_model(BeanieDocuments.leave_msg)
    bot.add_model(BeanieDocuments.strikes)