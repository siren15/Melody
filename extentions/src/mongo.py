import pymongo
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from odmantic.bson import Int64 as int64
from typing import Optional
from odmantic import Field, Model
from datetime import datetime
import os
import certifi

from extentions.src.slash_options import attachment
ca = certifi.where()

mongodb_url = os.environ["pt_mongo_url"]

class Mongo(object):
    @staticmethod
    def connect():
        return MongoClient(mongodb_url, tlsCAFile=ca)

class odm(object):
    @staticmethod
    async def connect():
        return AIOEngine(motor_client=AsyncIOMotorClient(mongodb_url, tlsCAFile=ca), database="giffany")

class dat(Model):
	guildid:Optional[int64] = None
	authorid:Optional[int64] = None
	prompts:Optional[str] = None
	content:Optional[str] = None
	resubmitted: Optional[bool] = None

class banned(Model):
    guildid: Optional[int64] = None
    userid: Optional[int64] = None

class banned_words(Model):
	guildid: Optional[int64] = None
	words_exact: Optional[str] = None
	words_wildcard: Optional[str] = None
	links_blacklist: Optional[str] = None
	links_whitelist: Optional[str] = None

class colourme(Model):
	guildid: Optional[int64] = None
	colourme_name: Optional[str] = None
	colourme_role_id: Optional[int64] = None
	requirement_role_id: Optional[str] = None
	ignore_role_id: Optional[str] = None

class giveaways(Model):
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

class giveme(Model):
	guildid: Optional[int64] = None
	reqname: Optional[str] = None
	reqid: Optional[int64] = None
	ignorename: Optional[str] = None
	ignoreid: Optional[int64] = None
	name: Optional[str] = None
	rolename: Optional[str] = None
	roleid: Optional[int64] = None

class giveyou(Model):
	guildid: Optional[int64] = None
	name: Optional[str] = None
	roleid:	Optional[int64] = None

class hasrole(Model):
	guildid: Optional[int64] = None
	command: Optional[str] = None
	role: Optional[int64] = None

class leveling_settings(Model):
	guildid: Optional[int64] = None
	min: Optional[int64] = None
	max: Optional[int64] = None
	multiplier: Optional[int64] = None
	no_xp_channel: Optional[int64] = None

class leveling(Model):
	guildid: Optional[int64] = None
	memberid: Optional[int64] = None
	level: Optional[int64] = None
	xp_to_next_level: Optional[int64] = None
	total_xp: Optional[int64] = None
	messages: Optional[int64] = None
	decimal: Optional[int64] = None
	
class leveling_roles(Model):
	guildid: Optional[int64] = None
	roleid: Optional[int64] = None
	level: Optional[int64] = None

class limbo(Model):
	guildid: Optional[int64] = None
	userid: Optional[int64] = None
	roles: Optional[str] = None
	reason: Optional[str] = None

class logs(Model):
	guild_id: Optional[int64] = None
	channel_id: Optional[int64] = None

class mutes(Model):
	guildid: Optional[int64] = None
	user: Optional[int64] = None
	roles: Optional[str] = None
	starttime: Optional[datetime] = None
	endtime: Optional[datetime] = None

class persistentroles(Model):
	guildid: Optional[int64] = None
	userid: Optional[int64] = None
	roles: Optional[str] = None

class persistent_roles(Model):
	guildid: Optional[int64] = None
	user: Optional[int64] = None
	roles: Optional[str] = None

class persistent_roles_settings(Model):
	guildid: Optional[int64] = None
	roleid: Optional[int64] = None

class prefixes(Model):
	guildid: Optional[int64] = None
	prefix: Optional[str] = None
	activecogs: Optional[str] = None
	activecommands: Optional[str] = None

class reminders(Model):
	guildid: Optional[int64] = None
	userid: Optional[int64] = None
	starttime: Optional[datetime] = None
	endtime: Optional[datetime] = None
	rem: Optional[str] = None

class strikes(Model):
	strikeid: Optional[str] = None
	guildid: Optional[int64] = None
	user: Optional[int64] = None
	moderator: Optional[str] = None
	action: Optional[str] = None
	reason: Optional[str] = None
	day: Optional[str] = None

class tag(Model):
	guild_id: Optional[int64] = None
	author_id: Optional[int64] = None
	names: Optional[str] = None
	content: Optional[str] = None
	attachment_url: Optional[str] = None
	no_of_times_used: Optional[int64] = None
	creation_date: Optional[datetime] = None
	owner_id: Optional[int64] = None

class tempbans(Model):
	guildid: Optional[int64] = None
	user: Optional[int64] = None
	starttime: Optional[datetime] = None
	endtime: Optional[datetime] = None
	banreason: Optional[str] = None

class userfilter(Model):
	guild: Optional[int64] = None
	userid: Optional[int64] = None

class welcomer(Model):
	guildid: Optional[int64] = None
	channelid: Optional[int64] = None
	msg: Optional[str] = None
	achannelid: Optional[int64] = None
	amsg: Optional[str] = None
	leavechannelid: Optional[int64] = None
	leavemsg: Optional[str] = None

class reactionroles(Model):
	reactionid: Optional[str] = None
	guildid: Optional[int64] = None
	channelid: Optional[int64] = None
	reactionmsgid: Optional[str] = None
	reactionemoji: Optional[str] = None
	reactionroleid: Optional[int64] = None
	requirementroleid: Optional[int64] = None
	ignoredroleid: Optional[int64] = None
	mode: Optional[int64] = None

class levelingstats(Model):
	lvl: Optional[int64] = None
	xptolevel: Optional[int64] = None
	totalxp: Optional[int64] = None

class levelwait(Model):
	guildid: Optional[int64] = None
	user: Optional[int64] = None
	starttime: Optional[datetime] = None
	endtime: Optional[datetime] = None

class auditlogs(Model):
	guildid: Optional[int64] = None
	action_type: Optional[int64] = None
	last_entry: Optional[int64] = None
