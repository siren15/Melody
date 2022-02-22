import asyncio
import math
import re
import random

from dateutil.relativedelta import *
from datetime import datetime, timedelta
from dis_snek import Snake, Scale, listen, Embed, Permissions, slash_command, InteractionContext,  OptionTypes, check, Select, SelectOption,  Button, ButtonStyles, ActionRow, spread_to_rows
from dis_snek.models.discord.base import DiscordObject
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *
from dis_snek.client.errors import NotFound

class BotConfiguration(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot

    @slash_command(name='bot', sub_cmd_name='settings', sub_cmd_description="[ADMIN]Configure how should pinetree behave", scopes=[435038183231848449,149167686159564800])
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def bot_configuration(self, ctx:InteractionContext):
        db = await odm.connect()
        events_logging = await db.find_one(prefixes, {'guildid':ctx.guild_id})
        events_log_list = events_logging.activecommands.lower()
        settings_selects = Select(
        options=[
            SelectOption(
                label="Event Logging",
                value="event_logging"
            )
        ],
        placeholder="Choose a module to configure",
        min_values=1,
        max_values=1,
        )
        def select_check(component: Select) -> bool:
            return (component.context.author == ctx.author)
        settings_sel_message = await ctx.send("Choose Which module you want to configure:", components=settings_selects)
        try:
            select_option = await self.bot.wait_for_component(components=settings_selects, timeout=600, check=select_check)
        except asyncio.TimeoutError:
            settings_selects.disabled=True
            await settings_sel_message.edit('Config closed after 10 minutes of inactivity.', components=settings_selects)
            return
        values = select_option.context.values
        if 'event_logging' in values:
            events_selects = Select(
            options=[
                SelectOption(
                    label="Message Deleted",
                    value="msg_del_sel"
                ),
                SelectOption(
                    label="Message Edited",
                    value="msg_edit_sel"
                ),
                SelectOption(
                    label="User Joined",
                    value="usr_join_sel"
                ),
                SelectOption(
                    label="User Left",
                    value="usr_left_sel"
                ),
                SelectOption(
                    label="User Kicked",
                    value="usr_kick_sel"
                ),
                SelectOption(
                    label="User Banned",
                    value="usr_ban_sel"
                ),
                SelectOption(
                    label="User Unbanned",
                    value="usr_unb_sel"
                )
            ],
            placeholder="Choose an event to configure",
            min_values=1,
            max_values=1,
            )
            events_sel_message = await select_option.context.send("Choose an event to configure:", components=events_selects)
            try:
                events_sel_option = await self.bot.wait_for_component(components=events_selects, timeout=600, check=select_check)
            except asyncio.TimeoutError:
                events_selects.disabled=True
                await events_sel_message.edit('Config closed after 10 minutes of inactivity.', components=events_selects)
                return
            events_btn_message = await events_sel_option.context.send(embed=Embed('buttons innit'))
            values = events_sel_option.context.values
            if 'msg_del_sel' in values:
                if 'message_deleted' in events_log_list:
                    msg_del_status = 'On'
                else:
                    msg_del_status = 'Off'
                deleted_messages_buttons: list[ActionRow] = spread_to_rows(
                    #deleted messages
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='deleted_messages_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='deleted_messages_off'
                    )
                )
                log_button = deleted_messages_buttons
                await events_btn_message.edit(embed=Embed(color=0xfc5f62, description=f'Log deleted messages: `{msg_del_status}`'), components=deleted_messages_buttons)
                await events_sel_option.context.send('You chose settings for Deleted Messages', ephemeral=True)
            
            if 'msg_edit_sel' in values:
                if 'message_edited' in events_log_list:
                    msg_edit_status = 'On'
                else:
                    msg_edit_status = 'Off'
                edited_messages_buttons: list[ActionRow] = spread_to_rows(
                    #deleted messages
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='edited_messages_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='edited_messages_off'
                    )
                )
                log_button = edited_messages_buttons
                await events_btn_message.edit(embed=Embed(color=0xfcab5f, description=f'Log edited messages: `{msg_edit_status}`'), components=edited_messages_buttons)
                await events_sel_option.context.send('You chose settings for Edited Messages', ephemeral=True)
            
            if 'usr_join_sel' in values:
                if 'member_join' in events_log_list:
                    mem_join_status = 'On'
                else:
                    mem_join_status = 'Off'
                user_joined_buttons: list[ActionRow] = spread_to_rows(
                    #user joined
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='join_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='join_off'
                    )
                )
                log_button = user_joined_buttons
                await events_btn_message.edit(embed=Embed(color=0x4d9d54, description=f'Log users joining: `{mem_join_status}`'), components=user_joined_buttons)
                await events_sel_option.context.send('You chose settings for User Join', ephemeral=True)
            
            if 'usr_left_sel' in values:
                if 'member_leave' in events_log_list:
                    mem_leave_status = 'On'
                else:
                    mem_leave_status = 'Off'
                user_left_buttons: list[ActionRow] = spread_to_rows(
                    #user left
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='left_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='left_off'
                    )
                )
                log_button = user_left_buttons
                await events_btn_message.edit(embed=Embed(color=0xcb4c4c, description=f'Log users leaving: `{mem_leave_status}`'), components=user_left_buttons)
                await events_sel_option.context.send('You chose settings for User Leave', ephemeral=True)
            
            if 'usr_left_sel' in values:
                if 'member_leave' in events_log_list:
                    mem_leave_status = 'On'
                else:
                    mem_leave_status = 'Off'
                user_left_buttons: list[ActionRow] = spread_to_rows(
                    #user left
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='left_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='left_off'
                    )
                )
                log_button = user_left_buttons
                await events_btn_message.edit(embed=Embed(color=0xcb4c4c, description=f'Log users leaving: `{mem_leave_status}`'), components=user_left_buttons)
                await events_sel_option.context.send('You chose settings for User Leave', ephemeral=True)
            
            if 'usr_kick_sel' in values:
                if 'member_kick' in events_log_list:
                    mem_kick_status = 'On'
                else:
                    mem_kick_status = 'Off'
                user_kicked_buttons: list[ActionRow] = spread_to_rows(
                    #kicked
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='kicked_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='kicked_off'
                    ),
                )
                log_button = user_kicked_buttons
                await events_btn_message.edit(embed=Embed(color=0x5c7fb0, description=f'Log kicking users: `{mem_kick_status}`'), components=user_kicked_buttons)
                await events_sel_option.context.send('You chose settings for User Kick', ephemeral=True)
            
            if 'usr_ban_sel' in values:
                if 'member_ban' in events_log_list:
                    mem_ban_status = 'On'
                else:
                    mem_ban_status = 'Off'
                user_banned_buttons: list[ActionRow] = spread_to_rows(
                    #banned
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='ban_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='ban_off'
                    )
                )
                log_button = user_banned_buttons
                await events_btn_message.edit(embed=Embed(color=0x473657, description=f'Log banning users: `{mem_ban_status}`'), components=user_banned_buttons)
                await events_sel_option.context.send('You chose settings for User Ban', ephemeral=True)
            
            if 'usr_unban_sel' in values:
                if 'member_unban' in events_log_list:
                    mem_unban_status = 'On'
                else:
                    mem_unban_status = 'Off'
                user_unbanned_buttons: list[ActionRow] = spread_to_rows(
                    #unbaned
                    Button(
                        style=ButtonStyles.GREEN,
                        label="On",
                        custom_id='unban_on'
                    ),
                    Button(
                        style=ButtonStyles.RED,
                        label="Off",
                        custom_id='unban_off'
                    )
                )
                log_button = user_unbanned_buttons
                await events_btn_message.edit(embed=Embed(color=0x9275b2, description=f'Log unbanning users: `{mem_unban_status}`'), components=user_unbanned_buttons)
                await events_sel_option.context.send('You chose settings for User Unban', ephemeral=True)
            
            def buttons_check(component: Button) -> bool:
                return (component.context.author == ctx.author)
            while True:
                events_logging = await db.find_one(prefixes, {'guildid':ctx.guild_id})
                events_log_list = events_logging.activecommands.lower()
                try:
                    log_buttons = await self.bot.wait_for_component(components=log_button, timeout=600, check=buttons_check)
                except asyncio.TimeoutError:
                    settings_selects.disabled=True
                    events_selects.disabled=True
                    await events_sel_message.delete()
                    await events_btn_message.delete()
                    await settings_sel_message.edit('Config closed after 10 minutes of inactivity.', components=settings_selects)
                    return
                if log_buttons.context.custom_id == 'deleted_messages_on':
                    if 'message_deleted' in events_log_list:
                        await log_buttons.context.send('Logging of deleted messages already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace('message_deleted,', '')
                        await db.save(events_logging)
                        deleted_messages_buttons: list[ActionRow] = spread_to_rows(
                            #deleted messages
                            Button(
                                style=ButtonStyles.GREEN,
                                label="On",
                                custom_id='deleted_messages_on'
                            ),
                            Button(
                                style=ButtonStyles.RED,
                                label="Off",
                                custom_id='deleted_messages_off'
                            )
                        )
                        await events_btn_message.edit(embed=Embed(color=0xfc5f62, description=f'Log deleted messages: `On`'), components=deleted_messages_buttons)
                        await log_buttons.context.send('You turned on logging of deleted messages.', ephemeral=True)
                elif log_buttons.context.custom_id == 'deleted_messages_off':
                    if 'message_deleted' not in events_log_list:
                        await log_buttons.context.send('Logging of deleted messages already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' message_deleted,'
                        await db.save(events_logging)
                        deleted_messages_buttons: list[ActionRow] = spread_to_rows(
                            #deleted messages
                            Button(
                                style=ButtonStyles.GREEN,
                                label="On",
                                custom_id='deleted_messages_on'
                            ),
                            Button(
                                style=ButtonStyles.RED,
                                label="Off",
                                custom_id='deleted_messages_off'
                            )
                        )
                        await events_btn_message.edit(embed=Embed(color=0xfc5f62, description=f'Log deleted messages: `Off`'), components=deleted_messages_buttons)
                        await log_buttons.context.send('You turned off logging of deleted messages.', ephemeral=True)

def setup(bot):
    BotConfiguration(bot)