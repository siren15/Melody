import asyncio
import math
import re
import random
from time import time

from dateutil.relativedelta import *
from datetime import datetime, timedelta
from naff import Client, Extension, listen, Embed, Permissions, slash_command, InteractionContext,  OptionTypes, check, Select, SelectOption,  Button, ButtonStyles, ActionRow, spread_to_rows
from naff.models.discord.base import DiscordObject
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *
from naff.client.errors import NotFound
from naff.api.events.internal import Component

class BotConfiguration(Extension):
    def __init__(self, bot: Client):
        self.bot = bot

    @slash_command(name='config', sub_cmd_name='logging', sub_cmd_description="[ADMIN]Configure what the bot logs")
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def logging_settings(self, ctx:InteractionContext):
        # events_selects = Select(
        # options=[
        #     SelectOption(
        #         label="Message Deleted",
        #         value=f"{ctx.author.id}_msg_del_sel"
        #     ),
        #     SelectOption(
        #         label="Message Edited",
        #         value=f"{ctx.author.id}_msg_edit_sel"
        #     ),
        #     SelectOption(
        #         label="User Joined",
        #         value=f"{ctx.author.id}_usr_join_sel"
        #     ),
        #     SelectOption(
        #         label="User Left",
        #         value=f"{ctx.author.id}_usr_left_sel"
        #     ),
        #     SelectOption(
        #         label="User Kicked",
        #         value=f"{ctx.author.id}_usr_kick_sel"
        #     ),
        #     SelectOption(
        #         label="User Banned",
        #         value=f"{ctx.author.id}_usr_ban_sel"
        #     ),
        #     SelectOption(
        #         label="User Unbanned",
        #         value=f"{ctx.author.id}_usr_unb_sel"
        #     )
        # ],
        # placeholder="Choose an event to configure",
        # min_values=1,
        # max_values=1,
        # )
        # await ctx.send("Choose an event to configure:", components=events_selects)
        deleted_messages_buttons: list[ActionRow] = spread_to_rows(
            #deleted messages
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_deleted_messages_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_deleted_messages_off'
            )
        )
        edited_messages_buttons: list[ActionRow] = spread_to_rows(
            #deleted messages
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_edited_messages_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_edited_messages_off'
            )
        )
        user_joined_buttons: list[ActionRow] = spread_to_rows(
            #user joined
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_join_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_join_off'
            )
        )
        user_left_buttons: list[ActionRow] = spread_to_rows(
            #user left
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_left_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_left_off'
            )
        )
        user_kicked_buttons: list[ActionRow] = spread_to_rows(
            #kicked
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_kicked_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_kicked_off'
            ),
        )
        user_banned_buttons: list[ActionRow] = spread_to_rows(
            #banned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_ban_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_ban_off'
            )
        )
        user_unbanned_buttons: list[ActionRow] = spread_to_rows(
            #unbaned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_unban_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_unban_off'
            )
        )
        mem_timeout_buttons: list[ActionRow] = spread_to_rows(
            #unbaned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_timeout_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_timeout_off'
            )
        )
        mem_roles_buttons: list[ActionRow] = spread_to_rows(
            #unbaned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_roles_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_roles_off'
            )
        )
        mem_nick_buttons: list[ActionRow] = spread_to_rows(
            #unbaned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_nick_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_nick_off'
            )
        )
        welcome_msg_buttons: list[ActionRow] = spread_to_rows(
            #unbaned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_welcome_msg_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_welcome_msg_off'
            )
        )
        welcome_msg_card_buttons: list[ActionRow] = spread_to_rows(
            #unbaned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_welcome_msg_card_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_welcome_msg_card_off'
            )
        )
        leave_msg_buttons: list[ActionRow] = spread_to_rows(
            #unbaned
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_leave_msg_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_leave_msg_off'
            )
        )
        automod_buttons: list[ActionRow] = spread_to_rows(
            Button(
                style=ButtonStyles.GREEN,
                label="On",
                custom_id=f'{ctx.author.id}_automod_on'
            ),
            Button(
                style=ButtonStyles.RED,
                label="Off",
                custom_id=f'{ctx.author.id}_automodg_off'
            )
        )
        
        buttons = [
            deleted_messages_buttons,
            edited_messages_buttons,
            user_joined_buttons,
            user_left_buttons,
            user_kicked_buttons,
            user_banned_buttons,
            user_unbanned_buttons,
            mem_timeout_buttons,
            mem_roles_buttons,
            mem_nick_buttons,
            welcome_msg_buttons,
            welcome_msg_card_buttons,
            leave_msg_buttons,
            automod_buttons
        ]

        
        events_logging = await db.prefixes.find_one({'guildid':ctx.guild_id})
        events_log_list = events_logging.activecommands.lower()

        if 'message_deleted' in events_log_list:
            msg_del_status = 'On'
        else:
            msg_del_status = 'Off'
        msg_de_msg = await ctx.send(embed=Embed(color=0xfc5f62, description=f'Log deleted messages: `{msg_del_status}`'), components=deleted_messages_buttons)

        if 'message_edited' in events_log_list:
            msg_edit_status = 'On'
        else:
            msg_edit_status = 'Off'
        msg_ed_msg = await ctx.send(embed=Embed(color=0xfcab5f, description=f'Log edited messages: `{msg_edit_status}`'), components=edited_messages_buttons)

        if 'member_join' in events_log_list:
            mem_join_status = 'On'
        else:
            mem_join_status = 'Off'
        mem_jo_msg = await ctx.send(embed=Embed(color=0x4d9d54, description=f'Log members joining: `{mem_join_status}`'), components=user_joined_buttons)

        if 'member_leave' in events_log_list:
            mem_leave_status = 'On'
        else:
            mem_leave_status = 'Off'
        mem_le_msg = await ctx.send(embed=Embed(color=0xcb4c4c, description=f'Log members leaving: `{mem_leave_status}`'), components=user_left_buttons)

        if 'member_kick' in events_log_list:
            mem_kick_status = 'On'
        else:
            mem_kick_status = 'Off'
        mem_kck_msg = await ctx.send(embed=Embed(color=0x5c7fb0, description=f'Log kicking members: `{mem_kick_status}`'), components=user_kicked_buttons)

        if 'member_ban' in events_log_list:
            mem_ban_status = 'On'
        else:
            mem_ban_status = 'Off'
        mem_bn_msg = await ctx.send(embed=Embed(color=0x62285e, description=f'Log banning users: `{mem_ban_status}`'), components=user_banned_buttons)
        
        if 'member_unban' in events_log_list:
            mem_unban_status = 'On'
        else:
            mem_unban_status = 'Off'
        mem_un_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Log unbanning users: `{mem_unban_status}`'), components=user_unbanned_buttons)

        if 'member_timeout' in events_log_list:
            mem_timeout_status = 'On'
        else:
            mem_timeout_status = 'Off'
        mem_ti_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Log muting members: `{mem_timeout_status}`'), components=mem_timeout_buttons)

        if 'member_roles' in events_log_list:
            mem_roles_status = 'On'
        else:
            mem_roles_status = 'Off'
        mem_ro_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Log members roles add/remove: `{mem_roles_status}`'), components=mem_roles_buttons)

        if 'member_nick' in events_log_list:
            mem_nick_status = 'On'
        else:
            mem_nick_status = 'Off'
        mem_ni_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Log members nickname change: `{mem_nick_status}`'), components=mem_nick_buttons)

        if 'welcome_msg' in events_log_list:
            welcome_msg_status = 'On'
        else:
            welcome_msg_status = 'Off'
        wel_m_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Welcome message: `{welcome_msg_status}`'), components=welcome_msg_buttons)

        if 'welcome_msg_card' in events_log_list:
            welcome_msg_card_status = 'On'
        else:
            welcome_msg_card_status = 'Off'
        wel_m_c_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Welcome message card: `{welcome_msg_card_status}`'), components=welcome_msg_card_buttons)

        if 'leave_msg' in events_log_list:
            leave_msg_status = 'On'
        else:
            leave_msg_status = 'Off'
        lea_m_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Leave message: `{leave_msg_status}`'), components=leave_msg_buttons)

        if 'automod' in events_log_list:
            automod_status = 'On'
        else:
            automod_status = 'Off'
        automod_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Automod: `{automod_status}`'), components=automod_buttons)

        button_messages = [
            msg_de_msg,
            msg_ed_msg,
            mem_jo_msg,
            mem_le_msg,
            mem_kck_msg,
            mem_bn_msg,
            mem_un_msg,
            mem_ti_msg,
            mem_ro_msg,
            mem_ni_msg,
            wel_m_msg,
            wel_m_c_msg,
            lea_m_msg,
            automod_msg
        ]

        if ctx.guild_id in [149167686159564800, 435038183231848449]:
            special_welcome_msg_buttons: list[ActionRow] = spread_to_rows(
                #unbaned
                Button(
                    style=ButtonStyles.GREEN,
                    label="On",
                    custom_id=f'{ctx.author.id}_special_welcome_msg_on'
                ),
                Button(
                    style=ButtonStyles.RED,
                    label="Off",
                    custom_id=f'{ctx.author.id}_special_welcome_msg_off'
                )
            )
            buttons = buttons + [special_welcome_msg_buttons]
            if 'special_welcome_msg' in events_log_list:
                s_welcome_msg_status = 'On'
            else:
                s_welcome_msg_status = 'Off'
            s_wel_m_msg = await ctx.send(embed=Embed(color=0x9275b2, description=f'Special welcome message: `{s_welcome_msg_status}`'), components=special_welcome_msg_buttons)
            button_messages = button_messages + [s_wel_m_msg]

        def buttons_check(component: Button) -> bool:
            return (component.context.author == ctx.author)

        timed_out = False
        while timed_out == False:
            try:
                button_used = await self.bot.wait_for_component(components=buttons, check=buttons_check, timeout=120)
            except asyncio.TimeoutError:
                await ctx.channel.delete_messages(button_messages)
                return await ctx.send(f'{ctx.author.mention} Events config closed due to 2 minutes of inactivity')
            else:
                bctx = button_used.context
                events_logging = await db.prefixes.find_one({'guildid':ctx.guild_id})
                events_log_list = events_logging.activecommands.lower()
                if bctx.custom_id == f'{bctx.author.id}_deleted_messages_on':
                    if 'message_deleted' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Logging of deleted messages already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' message_deleted,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0xfc5f62, description=f'Log deleted messages: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_deleted_messages_off':
                    if 'message_deleted' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Logging of deleted messages already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' message_deleted,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0xfc5f62, description=f'Log deleted messages: `Off`'))

                elif bctx.custom_id == f'{bctx.author.id}_edited_messages_on':
                    if 'message_edited' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Logging of edited messages already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' message_edited,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0xfcab5f, description=f'Log edited messages: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_edited_messages_off':
                    if 'message_edited' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Logging of edited messages already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' message_edited,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0xfcab5f, description=f'Log edited messages: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_join_on':
                    if 'member_join' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member join logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_join,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x4d9d54, description=f'Log members joining: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_join_off':
                    if 'member_join' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member join logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_join,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x4d9d54, description=f'Log members joining: `Off`'))

                elif bctx.custom_id == f'{bctx.author.id}_left_on':
                    if 'member_leave' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member leave logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_leave,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0xcb4c4c, description=f'Log users leaving: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_left_off':
                    if 'member_leave' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member leave logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_leave,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0xcb4c4c, description=f'Log users leaving: `On`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_kicked_on':
                    if 'member_kick' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member kick logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_kick,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x5c7fb0, description=f'Log kicking users: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_kicked_off':
                    if 'member_kick' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member kick logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_kick,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x5c7fb0, description=f'Log kicking users: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_ban_on':
                    if 'member_ban' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member ban logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_ban,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x62285e, description=f'Log banning users: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_ban_off':
                    if 'member_ban' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member ban logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_ban,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x62285e, description=f'Log banning users: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_unban_on':
                    if 'member_unban' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member unban logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_unban,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log unbanning users: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_unban_off':
                    if 'member_unban' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member unban logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_unban,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log unbanning users: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_timeout_on':
                    if 'member_timout' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member muting logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_timeout,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log muting users: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_timeout_off':
                    if 'member_timeout' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member muting logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_timeout,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log muting users: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_roles_on':
                    if 'member_roles' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member roles add/remove logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_roles,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log members roles add/remove: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_roles_off':
                    if 'member_roles' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member roles add/remove logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_roles,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log members roles add/remove: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_nick_on':
                    if 'member_nick' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member nickname change logs already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' member_nick,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log members nickname change: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_nick_off':
                    if 'member_nick' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Member nickname change logs already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' member_nick,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Log members nickname change: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_welcome_msg_on':
                    if 'welcome_msg' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Welcome message already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' welcome_msg,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Welcome message: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_welcome_msg_off':
                    if 'welcome_msg' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Welcome message already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' welcome_msg,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Welcome message: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_welcome_msg_card_on':
                    if 'welcome_msg_card' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Welcome message card already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' welcome_msg_card,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Welcome message card: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_welcome_msg_card_off':
                    if 'welcome_msg_card' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Welcome message card already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' welcome_msg_card,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Welcome message card: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_special_welcome_msg_on':
                    if 'special_welcome_msg' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Special welcome message already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' special_welcome_msg,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Special welcome message: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_special_welcome_msg_off':
                    if 'special_welcome_msg' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Special welcome message already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' special_welcome_msg,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Special welcome message: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_leave_msg_on':
                    if 'leave_msg' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Leave message already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' leave_msg,'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Leave message: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_leave_msg_off':
                    if 'leave_msg' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Leave message already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' leave_msg,', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Leave message: `Off`'))
                
                elif bctx.custom_id == f'{bctx.author.id}_automod_on':
                    if 'automod' in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Automod already turned on.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands+' automod, banned_words, phishing_filter'
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Automod: `On`'))

                elif bctx.custom_id == f'{bctx.author.id}_automod_off':
                    if 'automod' not in events_log_list:
                        await bctx.send(f'{bctx.author.mention} Automod already turned off.', ephemeral=True)
                    else:
                        events_logging.activecommands = events_logging.activecommands.replace(' automod, banned_words, phishing_filter', '')
                        await events_logging.save()
                        await bctx.edit_origin(embed=Embed(color=0x9275b2, description=f'Automod: `Off`'))

def setup(bot):
    BotConfiguration(bot)