import asyncio

from dateutil.relativedelta import *
from interactions import Client, Extension, SlashContext, StringSelectMenu, StringSelectOption, listen, Embed, Permissions, slash_command, SlashCommand, InteractionContext,  OptionType, check,  Button, ButtonStyle, ActionRow, spread_to_rows
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *

class BotConfiguration(Extension):
    def __init__(self, bot: Client):
        self.bot = bot

    config_cmd = SlashCommand(name='config', description='Configure the bot', default_member_permissions=Permissions.ADMINISTRATOR)

    @config_cmd.subcommand('logging', sub_cmd_description='Configure what the bot logs')
    async def config_logging(self, ctx: InteractionContext):
        await ctx.defer(ephemeral=True)
        events_logging = await db.prefixes.find_one({'guildid':ctx.guild_id})
        if events_logging.activecommands is None:
            events_log_list = ''
        else:
            events_log_list = events_logging.activecommands.lower()
        if 'message_deleted' in events_log_list:
            msg_del_status = True
        else:
            msg_del_status = False

        if 'message_edited' in events_log_list:
            msg_edit_status = True
        else:
            msg_edit_status = False

        if 'member_join' in events_log_list:
            mem_join_status = True
        else:
            mem_join_status = False

        if 'member_leave' in events_log_list:
            mem_leave_status = True
        else:
            mem_leave_status = False

        if 'member_kick' in events_log_list:
            mem_kick_status = True
        else:
            mem_kick_status = False

        if 'member_ban' in events_log_list:
            mem_ban_status = True
        else:
            mem_ban_status = False
        
        if 'member_unban' in events_log_list:
            mem_unban_status = True
        else:
            mem_unban_status = False

        if 'member_timeout' in events_log_list:
            mem_timeout_status = True
        else:
            mem_timeout_status = False

        if 'member_roles' in events_log_list:
            mem_roles_status = True
        else:
            mem_roles_status = False

        if 'member_nick' in events_log_list:
            mem_nick_status = True
        else:
            mem_nick_status = False

        if 'welcome_msg' in events_log_list:
            welcome_msg_status = True
        else:
            welcome_msg_status = False

        if 'welcome_msg_card' in events_log_list:
            welcome_msg_card_status = True
        else:
            welcome_msg_card_status = False

        if 'leave_msg' in events_log_list:
            leave_msg_status = True
        else:
            leave_msg_status = False

        select_options = [
            StringSelectOption(label="Deleted Messages", value="message_deleted", default=msg_del_status),
            StringSelectOption(label="Edited Messages", value="message_edited", default=msg_edit_status),
            StringSelectOption(label="Member Joined", value="member_join", default=mem_join_status),
            StringSelectOption(label="Member Left", value="member_leave", default=mem_leave_status),
            StringSelectOption(label="Member Kicked", value="member_kick", default=mem_kick_status),
            StringSelectOption(label="Member Banned", value="member_ban", default=mem_ban_status),
            StringSelectOption(label="Member Unbanned", value="member_unban", default=mem_unban_status),
            StringSelectOption(label="Member Timeout", value="member_timeout", default=mem_timeout_status),
            StringSelectOption(label="Member Roles", value="member_roles", default=mem_roles_status),
            StringSelectOption(label="Member Nickname", value="member_nick", default=mem_nick_status),
            StringSelectOption(label="Welcome Message", value="welcome_msg", default=welcome_msg_status),
            StringSelectOption(label="Leave Message", value="leave_msg", default=leave_msg_status),
            StringSelectOption(label="New Member Card", value="welcome_msg_card", default=welcome_msg_card_status),
        ]

        select_menu = StringSelectMenu(select_options, min_values=0, max_values=13)

        message = await ctx.send('Configure logging.', components=select_menu)

        while True:
            try:
                select = await self.bot.wait_for_component(components=select_menu, timeout=120)
            except asyncio.TimeoutError:
                await message.edit('Config closed due to 2 minutes of inactivity.', components=[])
            else:
                values = ",".join(select.ctx.values)
                events_logging.activecommands = values
                await events_logging.save()

def setup(bot):
    BotConfiguration(bot)