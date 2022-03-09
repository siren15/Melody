from bson.int64 import Int64 as int64
from dis_snek import Snake, Scale, slash_command, InteractionContext, Embed
from typing import Optional
from datetime import datetime
from beanie import Document as BeanieDocument

class Document(BeanieDocument):
    def __hash__(self):
        return hash(self.id)

class BeanieDocuments():
    class banned_words(Document):
        guildid: Optional[int64] = None
        words_exact: Optional[str] = None
        words_wildcard: Optional[str] = None
        links_blacklist: Optional[str] = None
        links_whitelist: Optional[str] = None

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

    class welcomer(Document):
        guildid: Optional[int64] = None
        channelid: Optional[int64] = None
        msg: Optional[str] = None
        achannelid: Optional[int64] = None
        amsg: Optional[str] = None
        leavechannelid: Optional[int64] = None
        leavemsg: Optional[str] = None

    class reactionroles(Document):
        reactionid: Optional[str] = None
        guildid: Optional[int64] = None
        channelid: Optional[int64] = None
        reactionmsgid: Optional[str] = None
        reactionemoji: Optional[str] = None
        reactionroleid: Optional[int64] = None
        requirementroleid: Optional[int64] = None
        ignoredroleid: Optional[int64] = None
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

class BeanieDocumentsScale(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot

    @slash_command(name='btest', description='beanie test', scopes=[435038183231848449,149167686159564800])
    async def beanie_test(self, ctx:InteractionContext):
        doc = await BeanieDocuments.prefixes.find_one({'guildid':ctx.guild_id})
        await ctx.send(f'{doc.activecommands}\n{doc.activecogs}')

def setup(bot):
    BeanieDocumentsScale(bot)
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
    bot.add_model(BeanieDocuments.reactionroles)
    bot.add_model(BeanieDocuments.persistentroles)
    bot.add_model(BeanieDocuments.userfilter)
    bot.add_model(BeanieDocuments.welcomer)
    bot.add_model(BeanieDocuments.strikes)