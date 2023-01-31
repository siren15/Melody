# inspired by https://github.com/artem30801/SkyboxBot/blob/master/main.py
from bson.int64 import Int64 as int64
from naff import Client, Extension
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from beanie import Document as BeanieDocument, Indexed, TimeSeriesConfig
import pymongo
import uuid

class Document(BeanieDocument):
    def __hash__(self):
        return hash(self.id)

class violation_settings(BaseModel):
    violation_count: Optional[int64] = 0
    violation_punishment: Optional[str] = 0
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
        guildid: int64
        name: str
        roleid:	int64
        giveyou_id: str

    class hasrole(Document):
        guildid: Optional[int64] = None
        command: Optional[str] = None
        role: Optional[int64] = None
    
    class levelingStats(Document):
        level: Optional[int64] = None
        xp_to_next_level: Optional[int64] = None
        total_xp: Optional[int64] = None

    class leveling_settings(Document):
        guildid: int64
        min: int64 = 15
        max: int64 = 25
        multiplier: int64 = 1
        ignored_channels: List|int = []
        ignored_roles: List|int = []
        ignored_users: List|int = []

    class leveling(Document):
        guildid: Optional[int64] = None
        display_name: Optional[str] = None
        memberid: Optional[int64] = None
        level: Optional[int64] = 0
        xp_to_next_level: Optional[int64] = 0
        total_xp: Optional[int64] = 0
        messages: Optional[int64] = 0
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
        mods: List = []
        activecogs: str = ""
        activecommands: str = ""

    class strikes(Document):
        type: Optional[str] = None
        strikeid: str = uuid.uuid4
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
        names: Indexed(str, pymongo.TEXT)
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
        requirement_roles: List = []
        ignored_roles: List = []
        ignored_users: List = []
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
    
    class bannedNames(Document):
        guild: int64
        names: List|str = []
        default_name:str = 'Default Name'
        violation_count: int64 = 0
        violation_punishment: List|str = []
    
    class amConfig(Document):
        guild: int64
        ignored_channels: List|int = list()
        ignored_roles: List|int = list()
        ignored_users: List|int = list()
        phishing: violation_settings
        banned_words: violation_settings
        banned_names: violation_settings
        ban_time: int64 = 0
        mute_time: int64 = 0
    
    class modmail(Document):
        guild: int64
        user: int64
        report_id: str
        contents: str
        images: List|str = []
        anon: bool = False
        messages:List|str = []
        active: bool = True
    
    class modmail_conf(Document):
        guild: int64
        category_id: int64 = None
        active_modmail_channels: List|int64 = []
    
    class dashSession(Document):
        sessionid: str
        user: dict
        guilds: list
        token: dict
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

def setup(bot):
    BeanieDocumentsExtension(bot)
    bot.add_model(BeanieDocuments.dashSession)
    bot.add_model(BeanieDocuments.modmail)
    bot.add_model(BeanieDocuments.modmail_conf)
    bot.add_model(BeanieDocuments.amConfig)
    bot.add_model(BeanieDocuments.bannedNames)
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