import random
from interactions import Client, SlashCommand, slash_command, InteractionContext, Message, OptionType, Permissions, Extension, Embed, check, listen, Button, spread_to_rows, SlashCommandChoice, SlashContext, ChannelType
from interactions.models.discord.components import ActionRow
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *
from interactions.api.events.internal import Component, ButtonPressed
from interactions.models.discord.enums import ButtonStyle, ComponentType

async def button_id_generator(ctx, channel, message):
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    while True:
        result = ''.join(random.choice(characters) for i in range(8))
        rb = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':channel.id, 'msg_id':message.id, 'button_id':result})
        if rb is None:
            return result
        else:
            continue

class ButtonRoles(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
    
    role_buttons = SlashCommand(name='rolebuttons', description='Manage role buttons.', default_member_permissions=Permissions.ADMINISTRATOR)
    
    @role_buttons.subcommand(sub_cmd_name='create', sub_cmd_description="Add role buttons to a message")
    @slash_option(name='roles', description='Roles, seperated by a comma(,)', opt_type=OptionType.STRING, required=True)
    @slash_option(name='message_id', description='Paste in a message ID', opt_type=OptionType.STRING, required=True)
    @slash_option(name='channel', description='Select a channel', opt_type=OptionType.CHANNEL, channel_types=[ChannelType.GUILD_TEXT], required=False)
    @slash_option(name="button_colours", description="Choose what colour the button will be. Default: Blurple", required=False, opt_type=OptionType.INTEGER,
    choices=[SlashCommandChoice(name="Blurple", value=1), SlashCommandChoice(name="Green", value=3), SlashCommandChoice(name="Red", value=4), SlashCommandChoice(name="Gray", value=2)])
    @slash_option(name="mode", description="Choose the mode this set of buttons will be in. Default: Click to get/remove a role", required=False, opt_type=OptionType.INTEGER,
    choices=[SlashCommandChoice(name="Get or remove a role", value=1),SlashCommandChoice(name="Get a role, no removing", value=2),SlashCommandChoice(name="Only one role allowed", value=3)])
    async def role_buttons_add(self, ctx: SlashContext, roles: str, message_id: OptionType.STRING, channel: ChannelType.GUILD_TEXT=None, button_colours: OptionType.INTEGER = 1, mode: OptionType.INTEGER=1):
        """/rolebuttons create
        Description:
            Add role buttons to a message.

        Args:
            roles (str): Role IDs or @roles, sperated by comma `,` | the roles you want to create role buttons from. There can't be more than 25 roles/buttons on one message.
            message_id (OptionType.STRING): Message ID you want the role buttons on, it has to be a message sent by Melody.
            channel (ChannelType.GUILD_TEXT, optional): Channel the message is in. Defaults to channel command is executed in.
            button_colours (OptionType.INTEGER, optional): The colour you want the buttons to be. Defaults to Blurple.
            mode (OptionType.INTEGER, optional): Mode you want buttons to be in. Defaults to 1. Modes: 1 = get or remove the role, 2 = get a role - not possible to remove the role, 3 = only one role allowed from the message
        """
        await ctx.defer()
        # modes: 1 = get or remove the role, 2 = get a role - not possible to remove the role, 3 = only one role allowed from the message
        if channel is None:
            channel = ctx.channel
        message: Message = await channel.fetch_message(message_id)
        if message is not None:
            components = []
            if message.components != []:
                for ob in message.components:
                    components = components + ob.components
            documents = []
            messages = []

            if button_colours == 1:
                button_colour = ButtonStyle.BLURPLE
            elif button_colours == 3:
                button_colour = ButtonStyle.GREEN
            elif button_colours == 4:
                button_colour = ButtonStyle.RED
            elif button_colours == 2:
                button_colour = ButtonStyle.GRAY
            
            raw_roles_list = roles.split(',')
            roles_ids = []
            for r in raw_roles_list:
                r = r.replace('<', '')
                r = r.replace('@', '')
                r = r.replace('!', '')
                r = r.replace('&', '')
                r = r.replace('>', '')
                roles_ids.append(r)
            for role_id in roles_ids:
                role = ctx.guild.get_role(role_id)
                if role is not None:
                    button_id = await button_id_generator(ctx, channel, message)
                    components.append(Button(style=button_colour,label=f"{role.name}",custom_id=button_id))
                    messages.append(f"Button for role {role.mention} was added.\nButton ID: `{button_id}`\nMode: {mode}")
                    documents.append(db.button_roles(guildid=ctx.guild_id, button_id=button_id, channelid=channel.id, msg_id=message.id, roleid=role.id, mode=mode))
                    
            if len(components) > 25:
                return await ctx.send("There can't be more than 25 components on one message")

            rows = spread_to_rows(*components)

            await db.button_roles.insert_many(documents)
            await message.edit(components=rows)
            for m in messages:
                await ctx.send(embed=Embed(color=0xffcc50, description=m))
        else:
            return await ctx.send("Message not found.")
    
    @role_buttons.subcommand(sub_cmd_name='edit', sub_cmd_description="Edit the behaviour of a role button")
    @message_id()
    @button_id()
    @channel()
    @slash_option(name="mode",description="Choose the mode this set of buttons will be in. Default: Click to get/remove a role",required=False,opt_type=OptionType.INTEGER,
    choices=[SlashCommandChoice(name="Get or remove a role", value=1),SlashCommandChoice(name="Get a role, no removing", value=2),SlashCommandChoice(name="Only one role allowed", value=3)])
    @new_role()
    @slash_option(name="button_colours",description="Choose what colour the button will be. Default: Blurple",required=False,opt_type=OptionType.INTEGER,
    choices=[SlashCommandChoice(name="Blurple", value=1),SlashCommandChoice(name="Green", value=3),SlashCommandChoice(name="Red", value=4),SlashCommandChoice(name="Gray", value=2)])
    @slash_option(name="requirement_role",description="Choose a role. Members will be required to have this role to use the button.",required=False,opt_type=OptionType.ROLE)
    @slash_option(name="ignore_role",description="Choose a role. Members with this role will be ignored.",required=False,opt_type=OptionType.ROLE)
    @slash_option(name='name', description='Give the button a custom name', opt_type=OptionType.STRING, required=False)
    async def role_buttons_edit(self, ctx: InteractionContext, message_id:OptionType.STRING, button_id:OptionType.STRING, channel:OptionType.CHANNEL=None, mode:OptionType.INTEGER=None,
    button_colours:OptionType.INTEGER=None, new_role: OptionType.ROLE = None, requirement_role: OptionType.ROLE = None, ignore_role: OptionType.ROLE = None, name: OptionType.STRING=None):
        """/rolebuttons edit
        Description:
            Edit the behaviour of a role button. `Name`, `Button colour` and `New Role` can't be edited together.

        Args:
            message_id (OptionType.STRING): Message ID the role button is on.
            button_id (OptionType.STRING): Button ID of the button you want to modify.
            channel (OptionType.CHANNEL, optional): Channel the message is in. Defaults to channel command is executed in.
            mode (OptionType.INTEGER, optional): Mode you want buttons to be in. Modes: 1 = get or remove the role, 2 = get a role - not possible to remove the role, 3 = only one role allowed from the message
            button_colours (OptionType.INTEGER, optional): _description_. The colour you want the buttons to be.
            new_role (OptionType.ROLE, optional): The new role you want on the button.
            requirement_role (OptionType.ROLE, optional): Choose a role. Members will be required to have this role to use the button.
            ignore_role (OptionType.ROLE, optional): Choose a role. Members with this role will be ignored.
            name (OptionType.STRING, optional): Change the button name.
        """
        await ctx.defer()
        if button_colours == 1:
            button_colour = ButtonStyle.BLURPLE
            colour = 'Blurple'
        elif button_colours == 3:
            button_colour = ButtonStyle.GREEN
            colour = 'Green'
        elif button_colours == 4:
            button_colour = ButtonStyle.RED
            colour = 'Red'
        elif button_colours == 2:
            button_colour = ButtonStyle.GRAY
            colour = 'Gray'
        if (mode is None) and (button_colours is None) and (new_role is None) and (requirement_role is None) and (ignore_role is None) and (name is None):
            return await ctx.send('You have to change at least one option to change')
        if channel is None:
            channel = ctx.channel
        edits = ''
        message = await channel.fetch_message(message_id)
        if message is not None:
            if (button_colours is not None) and (new_role is not None) and (name is not None):
                return await ctx.send("`Name`, `Button colour` and `New Role` can't be edited together")
            if button_colours is not None:
                    if message.components != []:
                        components = []
                        for ob in message.components:
                            components.append(ob.components)
                            
                        for l in components:
                            for b in l:
                                if b.custom_id == button_id:
                                    for p in [(i, l.index(b)) for i, l in enumerate(components) if b in l]:
                                        p1, p2 = p
                        
                        message.components[p1].components[p2].style = button_colour
                        await message.edit(components=message.components)    
                        edits = edits + f"New colour: {colour}\n"
            button = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':channel.id, 'msg_id':message.id, 'button_id':button_id})
            if mode is not None:
                button.mode = mode
                await button.save()
                if mode == 1:
                    button_mode = 'Get or remove a role'
                elif mode == 2:
                    button_mode = 'Get a role, no removing'
                elif mode == 3:
                    button_mode = 'Only one role allowed'
                edits = edits + f"New Mode: {button_mode}\n"
            if name is not None:
                if message.components != []:
                    components = []
                    for ob in message.components:
                        components.append(ob.components)
                        
                    for l in components:
                        for b in l:
                            if b.custom_id == button_id:
                                for p in [(i, l.index(b)) for i, l in enumerate(components) if b in l]:
                                    p1, p2 = p
                    message.components[p1].components[p2].label = name
                    await message.edit(components=message.components)
                edits = edits + f"New Name: {name}\n"
            if new_role is not None:
                button.roleid = new_role.id
                await button.save()
                if message.components != []:
                    components = []
                    for ob in message.components:
                        components.append(ob.components)
                        
                    for l in components:
                        for b in l:
                            if b.custom_id == button_id:
                                for p in [(i, l.index(b)) for i, l in enumerate(components) if b in l]:
                                    p1, p2 = p
                    if name is not None:
                        bname = name
                    elif name is None:
                        bname = new_role.name
                    message.components[p1].components[p2].label = bname
                    await message.edit(components=message.components)
                edits = edits + f"New Role: {new_role.mention}\n"
            if requirement_role is not None:
                if button.requirement_roles is not None:
                    button.requirement_roles.append(requirement_role.id)
                    await button.save()
                else:
                    button.requirement_roles = [requirement_role.id]
                    await button.save()
                edits = edits + f"Requirement Role: {requirement_role.mention}\n"
            if ignore_role is not None:
                if button.ignored_roles is not None:
                    button.ignored_roles.append(ignore_role.id)
                    await button.save()
                else:
                    button.ignored_roles = [ignore_role.id]
                    button.save()
                edits = edits + f"Ignore Role: {ignore_role.mention}\n"
            await ctx.send(embed=Embed(color=0xffcc50,description=f"Button `{button_id}` succesfully edited\n{edits}"))
        else:
            await ctx.send('Message not found')

    @role_buttons.subcommand(sub_cmd_name='remove', sub_cmd_description="Remove a role button")
    @button_id()
    @message_id()
    @channel()
    async def role_buttons_remove(self, ctx: InteractionContext, message_id:OptionType.STRING, button_id:OptionType.STRING, channel:OptionType.CHANNEL=None):
        """/rolebuttons remove
        Description:
            Delete a role button from a message.

        Args:
            message_id (OptionType.STRING): Message ID the button is on.
            button_id (OptionType.STRING): The button ID, of the button you want to delete.
            channel (OptionType.CHANNEL, optional): Channel the message is in. Defaults to channel command is executed in.
        """
        await ctx.defer()
        if channel is None:
            channel = ctx.channel
        message: Message = await channel.fetch_message(message_id)
        if message is None:
            return await ctx.send(f"Can't find a message with that id", ephemeral=True)
        components = []
        if message.components != []:
            for ob in message.components:
                components = components + ob.components
        
        for b in components:
            if b.custom_id == button_id:
                components.remove(b)
        
        rows = spread_to_rows(*components)

        await message.edit(components=rows)

        button = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':channel.id, 'msg_id':message.id, 'button_id':button_id})
        await button.delete()
        await ctx.send(f"Button `{button_id}` successfully deleted")

    @role_buttons.subcommand(sub_cmd_name='list', sub_cmd_description="List all role buttons on this server")
    async def role_buttons_list(self, ctx: InteractionContext):
        """/rolebuttons list

        Description:
            List all the role buttons, and their info.
        """
        await ctx.defer()
        from interactions.ext.paginators import Paginator
        def chunks(l, n):
            n = max(1, n)
            return (l[i:i+n] for i in range(0, len(l), n))
        
        def mlis(lst, s, e):
            nc = list(chunks(lst, 10))
            mc = ''
            for testlist in nc[s:e]:
                for m in testlist:
                    mc = mc + m
            return mc

        def newpage(title, buttoninfo):
            embed = Embed(title=title,
            description=buttoninfo,
            color=0xffcc50)
            return embed
        
        role_buttons = db.button_roles.find({'guildid':ctx.guild_id})
        
        buttons = []
        async for button in role_buttons:
            role = ctx.guild.get_role(button.roleid)
            if role is None:
                role = 'Role missing'
            elif role is not None:
                role = role.mention
            if button.requirement_roles is not None:
                req_role = ' '.join([ctx.guild.get_role(id).mention for id in button.requirement_roles])
                if req_role == '':
                    reqrole = 'Req. role missing'
            else:
                reqrole = 'No req. role'
            if button.ignored_roles is not None:
                ign_role = ' '.join([ctx.guild.get_role(id).mention for id in button.ignored_roles])
                if ign_role == '':
                    ignrole = 'Ign. role missing'
            else:
                ignrole = 'No ign. role'
            channel = ctx.guild.get_channel(button.channelid)
            if channel is None:
                chnl = 'Channel missing'
            elif channel is not None:
                chnl = channel.mention
            msg = await channel.fetch_message(button.msg_id)
            if msg is None:
                msg = 'Message missing'
            elif msg is not None:
                msg = f'[[Jump to message]]({msg.jump_url})'
            buttons.append(f"**Button ID:** {button.button_id} | **Role:** {role} | **Req. role:** {reqrole} | **Ign. role:** {ignrole} |** Channel:** {chnl} | **Message:** {msg}\n\n")
        
        if buttons == []:
            await ctx.send('There are no role buttons for this server yet')
            return            
        
        s = -1
        e = 0
        embedcount = 1
        nc = list(chunks(buttons, 10))
        
        embeds = []
        while embedcount <= len(nc):
            s = s+1
            e = e+1
            embeds.append(newpage(f'Role buttons for {ctx.guild.name}', mlis(buttons, s, e)))
            embedcount = embedcount+1
            
        paginator = Paginator(
            client=self.bot, 
            pages=embeds,
            timeout_interval=80,
            show_select_menu=False)
        await paginator.send(ctx)

    @listen()
    async def on_button_press_role_add_mode_1(self, event: ButtonPressed):
        ctx = event.ctx
        user = ctx.author
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':1})
        if rolebutton is not None:
            role_to_add = ctx.guild.get_role(rolebutton.roleid)
            if role_to_add is not None:
                if not user.has_permission(Permissions.ADMINISTRATOR):
                    if (rolebutton.ignored_users is not None) and (rolebutton.ignored_users != []):
                        if user.id in rolebutton.ignored_users:
                            return await ctx.author.send('You are not allowed to use that role button.')

                    if (rolebutton.ignored_roles is not None) and (rolebutton.ignored_roles != []):
                        ign_roles = [role.name for role in user.roles if role.id in rolebutton.ignored_roles]
                        if ign_roles != []:
                            ign_roles_str = ','.join(ign_roles)
                            return await ctx.author.send(f"I can't give members with **`{ign_roles_str}`** role the **`{role_to_add.name}`** role in `{ctx.guild.name}`", ephemeral=True)

                    if (rolebutton.requirement_roles is not None) and (rolebutton.requirement_roles != []):
                        usr_roles = [role.id for role in user.roles]
                        req_roles = [ctx.guild.get_role(roleid).name for roleid in rolebutton.requirement_roles if roleid not in usr_roles]
                        if req_roles != []:
                            req_roles_str = ','.join(ign_roles)
                            return await ctx.author.send(f"You don't have **`{req_roles_str}`**, which you need to have for me to give you **`{role_to_add.name}`** in `{ctx.guild.name}`", ephemeral=True)           
                
                if role_to_add not in ctx.author.roles:
                    await ctx.author.add_role(role_to_add)
                    await ctx.author.send(embed=Embed(color=0xffcc50, description=f"I gave you role `{role_to_add.name}` in `{ctx.guild.name}`"), ephemeral=True)
    
    @listen()
    async def on_button_press_role_add_mode_2(self, event: Component):
        ctx = event.ctx
        user = ctx.author
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':2})
        if rolebutton is not None:
            role_to_add = ctx.guild.get_role(rolebutton.roleid)
            if role_to_add is not None:
                if not user.has_permission(Permissions.ADMINISTRATOR):
                    if (rolebutton.ignored_users is not None) and (rolebutton.ignored_users != []):
                        if user.id in rolebutton.ignored_users:
                            return await ctx.author.send('You are not allowed to use that role button.')

                    if (rolebutton.ignored_roles is not None) and (rolebutton.ignored_roles != []):
                        ign_roles = [role.name for role in user.roles if role.id in rolebutton.ignored_roles]
                        if ign_roles != []:
                            ign_roles_str = ','.join(ign_roles)
                            return await ctx.author.send(f"I can't give members with **`{ign_roles_str}`** role the **`{role_to_add.name}`** role in `{ctx.guild.name}`", ephemeral=True)

                    if (rolebutton.requirement_roles is not None) and (rolebutton.requirement_roles != []):
                        usr_roles = [role.id for role in user.roles]
                        req_roles = [ctx.guild.get_role(roleid).name for roleid in rolebutton.requirement_roles if roleid not in usr_roles]
                        if req_roles != []:
                            req_roles_str = ','.join(ign_roles)
                            return await ctx.author.send(f"You don't have **`{req_roles_str}`**, which you need to have for me to give you **`{role_to_add.name}`** in `{ctx.guild.name}`", ephemeral=True)

                if role_to_add not in ctx.author.roles:
                    await ctx.author.add_role(role_to_add)
                    await ctx.author.send(embed=Embed(color=0xffcc50, description=f"I gave you role `{role_to_add.name}`"), ephemeral=True)
                elif role_to_add in ctx.author.roles:
                    await ctx.author.send(embed=Embed(color=0xffcc50, description=f"This role `{role_to_add.name}` can't be taken away from you in `{ctx.guild.name}` in `{ctx.guild.name}`"), ephemeral=True)
    
    @listen()
    async def on_button_press_role_add_mode_3(self, event: Component):
        ctx = event.ctx
        user = ctx.author
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':3})
        if rolebutton is not None:
            role_to_add = ctx.guild.get_role(rolebutton.roleid)                 
            if role_to_add is not None:
                if not user.has_permission(Permissions.ADMINISTRATOR):
                    if (rolebutton.ignored_users is not None) and (rolebutton.ignored_users != []):
                        if user.id in rolebutton.ignored_users:
                            return await ctx.author.send('You are not allowed to use that role button.')

                    if (rolebutton.ignored_roles is not None) and (rolebutton.ignored_roles != []):
                        ign_roles = [role.name for role in user.roles if role.id in rolebutton.ignored_roles]
                        if ign_roles != []:
                            ign_roles_str = ','.join(ign_roles)
                            return await ctx.author.send(f"I can't give members with **`{ign_roles_str}`** role the **`{role_to_add.name}`** role in `{ctx.guild.name}`", ephemeral=True)

                    if (rolebutton.requirement_roles is not None) and (rolebutton.requirement_roles != []):
                        usr_roles = [role.id for role in user.roles]
                        req_roles = [ctx.guild.get_role(roleid).name for roleid in rolebutton.requirement_roles if roleid not in usr_roles]
                        if req_roles != []:
                            req_roles_str = ','.join(ign_roles)
                            return await ctx.author.send(f"You don't have **`{req_roles_str}`**, which you need to have for me to give you **`{role_to_add.name}`** in `{ctx.guild.name}`", ephemeral=True)

                old_roles = 'and took away '
                buttons = []
                async for b in db.button_roles.find({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'mode':3}):
                    buttons.append(b.roleid)
                if buttons != []:
                    for button_role_id in buttons:
                        if button_role_id != rolebutton.roleid:
                            old_role = ctx.guild.get_role(button_role_id)
                            if old_role is not None:
                                if old_role in ctx.author.roles:
                                    await ctx.author.remove_role(old_role)
                                    old_roles = old_roles + f'`{old_role.name}` '
                
                if old_roles == 'and took away ':
                    old_roles = ''
            
                if role_to_add not in ctx.author.roles:
                    await ctx.author.add_role(role_to_add)
                    await ctx.author.send(embed=Embed(color=0xffcc50, description=f"I gave you role `{role_to_add.name}` {old_roles} in `{ctx.guild.name}`"), ephemeral=True)

    @listen()
    async def on_button_press_role_remove_mode_1(self, event: Component):
        ctx = event.ctx
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':1})
        if rolebutton is not None:
            role_to_remove = ctx.guild.get_role(rolebutton.roleid)
            if role_to_remove is not None:
                if role_to_remove in ctx.author.roles:
                    await ctx.author.remove_role(role_to_remove)
                    await ctx.author.send(embed=Embed(color=0xffcc50, description=f"I took away a role `{role_to_remove.name}` from you in `{ctx.guild.name}`"), ephemeral=True)

    @listen()
    async def on_button_press_role_remove_mode_3(self, event: Component):
        ctx = event.ctx
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':3})
        if rolebutton is not None:
            old_roles = ''
            buttons = []
            async for b in db.button_roles.find({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'mode':3}):
                buttons.append(b.roleid)
            if buttons != []:
                for button_role_id in buttons:
                    if button_role_id != rolebutton.roleid:
                        old_role = ctx.guild.get_role(button_role_id)
                        if old_role is not None:
                            if old_role in ctx.author.roles:
                                await ctx.author.remove_role(old_role)
                                old_roles = old_roles + f'`{old_role.name}` '

            role_to_remove = ctx.guild.get_role(rolebutton.roleid)                 
            if role_to_remove is not None:
                if role_to_remove in ctx.author.roles:
                    await ctx.author.remove_role(role_to_remove)
                    old_roles = old_roles + f'`{role_to_remove.name}` '
                    await ctx.author.send(embed=Embed(color=0xffcc50, description=f"I took away {old_roles} in `{ctx.guild.name}`"), ephemeral=True)

def setup(bot):
    ButtonRoles(bot)