import asyncio
import math
import re
import random

from dateutil.relativedelta import *
from datetime import datetime, timedelta
from dis_snek import Snake, Scale, listen, Embed, Permissions, slash_command, InteractionContext,  OptionTypes, check, Select, SelectOption, Button, ButtonStyles
from dis_snek.models.discord.base import DiscordObject
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *
from dis_snek.client.errors import NotFound

class BotConfiguration(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot

    @slash_command(name='pinetree', sub_cmd_name='settings', sub_cmd_description="[ADMIN]Configure how should pinetree behave", scopes=[435038183231848449,149167686159564800])
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def bot_configuration(self, ctx:InteractionContext):
        selects = Select(
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
        def check(component: Select) -> bool:
            return (component.context.author == ctx.author)
        settings_message = await ctx.send("Bot settings:", components=selects)
        while True:
            try:
                select_option = await self.bot.wait_for_component(components=selects, timeout=600, check=check)
            except asyncio.TimeoutError:
                selects.disabled=True
                await settings_message.edit('Config closed after 10 minutes of inactivity.', components=selects)
                return
            print(select_option.context)
                

def setup(bot):
    BotConfiguration(bot)