from email import message
import random
from dis_snek import Snake, slash_command, InteractionContext, OptionTypes, Permissions, Scale, Embed, check, listen, Button, ButtonStyles, spread_to_rows, SlashCommandChoice
from dis_snek.models.discord.components import ActionRow, spread_to_rows
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *
from dis_snek.api.events.internal import Component
from dis_snek.models.discord.enums import ButtonStyles, ComponentTypes

async def button_id_generator(ctx, channel, message):
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    while True:
        result = ''.join(random.choice(characters) for i in range(8))
        rb = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':channel.id, 'msg_id':message.id, 'button_id':result})
        if rb is None:
            return result
        else:
            continue

class ButtonRoles(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @slash_command(name='rolebuttons', sub_cmd_name='add', sub_cmd_description="Add role buttons to a message", scopes=[435038183231848449,149167686159564800])
    @bt_role_1()
    @message_id()
    @channel()
    @slash_option(name='role_2', description='Select a role for a new button', opt_type=OptionTypes.ROLE, required=False)
    @slash_option(name='role_3', description='Select a role for a new button', opt_type=OptionTypes.ROLE, required=False)
    @slash_option(name='role_4', description='Select a role for a new button', opt_type=OptionTypes.ROLE, required=False)
    @slash_option(name='role_5', description='Select a role for a new button', opt_type=OptionTypes.ROLE, required=False)
    @slash_option(name="button_colour",description="Choose what colour the button will be. Default: Blurple",required=False,opt_type=OptionTypes.INTEGER,
    choices=[SlashCommandChoice(name="Blurple", value=1),SlashCommandChoice(name="Green", value=3),SlashCommandChoice(name="Red", value=4),SlashCommandChoice(name="Gray", value=2)])
    @slash_option(name="mode",description="Choose the mode this set of buttons will be in. Default: Click to get/remove a role",required=False,opt_type=OptionTypes.INTEGER,
    choices=[SlashCommandChoice(name="Get or remove a role", value=1),SlashCommandChoice(name="Get a role, no removing", value=2),SlashCommandChoice(name="Only one role allowed", value=3)])
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def add_role_buttons(self, ctx: InteractionContext, bt_role_1: OptionTypes.ROLE, message_id: OptionTypes.STRING, channel: OptionTypes.CHANNEL=None,
    role_2: OptionTypes.ROLE=None, role_3: OptionTypes.ROLE=None, role_4: OptionTypes.ROLE=None, role_5: OptionTypes.ROLE=None, button_colour: OptionTypes.INTEGER = 1, mode: OptionTypes.INTEGER=1):
        #modes: 1 = react to get a role - unreact to remove the role, 2 = react to get a role - not possible to remove the role, 3 = only one role allowed from the message
        if message_id is None:
            return await ctx.send('You need to include the message buttons will be on.', ephemeral=True)    
        if channel is None:
            channel = ctx.channel
        message = await channel.fetch_message(message_id)
        if message is not None:
            components = []
            if message.components != []:
                for ob in message.components:
                    components = components + ob.components
            documents = []
            messages = []
            button_1_id = await button_id_generator(ctx, channel, message)
            components.append(Button(style=button_colour,label=f"{bt_role_1.name}",custom_id=button_1_id))
            messages.append(f"Button for role {bt_role_1.mention} was added.\nButton ID: `{button_1_id}`\nMode: {mode}")
            documents.append(db.button_roles(guildid=ctx.guild_id, button_id=button_1_id, channelid=channel.id, msg_id=message.id, roleid=bt_role_1.id, mode=mode))
            if role_2 is not None:
                button_2_id = await button_id_generator(ctx, channel, message)
                components.append(Button(style=button_colour, label=f"{role_2.name}", custom_id=button_2_id))
                messages.append(f"Button for role {role_2.mention} was added.\nButton ID: `{button_2_id}`\nMode: {mode}")
                documents.append(db.button_roles(guildid=ctx.guild_id, button_id=button_2_id, channelid=channel.id, msg_id=message.id, roleid=role_2.id, mode=mode))
            if role_3 is not None:
                button_3_id = await button_id_generator(ctx, channel, message)
                components.append(Button(style=button_colour, label=f"{role_3.name}", custom_id=button_3_id))
                messages.append(f"Button for role {role_3.mention} was added.\nButton ID: `{button_3_id}`\nMode: {mode}")
                documents.append(db.button_roles(guildid=ctx.guild_id, button_id=button_3_id, channelid=channel.id, msg_id=message.id, roleid=role_3.id, mode=mode))
            if role_4 is not None:
                button_4_id = await button_id_generator(ctx, channel, message)
                components.append(Button(style=button_colour, label=f"{role_4.name}", custom_id=button_4_id))
                messages.append(f"Button for role {role_4.mention} was added.\nButton ID: `{button_4_id}`\nMode: {mode}")
                documents.append(db.button_roles(guildid=ctx.guild_id, button_id=button_4_id, channelid=channel.id, msg_id=message.id, roleid=role_4.id, mode=mode))
            if role_5 is not None:
                button_5_id = await button_id_generator(ctx, channel, message)
                components.append(Button(style=button_colour, label=f"{role_5.name}", custom_id=button_5_id))
                messages.append(f"Button for role {role_5.mention} was added.\nButton ID: `{button_5_id}`\nMode: {mode}")
                documents.append(db.button_roles(guildid=ctx.guild_id, button_id=button_5_id, channelid=channel.id, msg_id=message.id, roleid=role_5.id, mode=mode))
            if len(components) > 25:
                return await ctx.send("There can't be more than 25 components on one message")
            
            rows = []
            button_row = []
            for component in components:
                if component is not None and component.type == ComponentTypes.BUTTON:
                    button_row.append(component)

                    if len(button_row) == 5:
                        rows.append(ActionRow(*button_row))
                        button_row = []

                    continue

                if button_row:
                    rows.append(ActionRow(*button_row))
                    button_row = []

                if component is not None:
                    if component.type == ComponentTypes.ACTION_ROW:
                        rows.append(component)
                    elif component.type == ComponentTypes.SELECT:
                        rows.append(ActionRow(component))
            if button_row:
                rows.append(ActionRow(*button_row))

            if len(rows) > 5:
                raise ValueError("Number of rows exceeds 5.")

            await db.button_roles.insert_many(documents)
            await message.edit(components=rows)
            for m in messages:
                await ctx.send(embed=Embed(color=0x0c73d3, description=m))
    
    @slash_command(name='rolebuttons', sub_cmd_name='edit', sub_cmd_description="Edit a behaviour of a role button", scopes=[435038183231848449,149167686159564800])
    @message_id()
    @button_id()
    @channel()
    @slash_option(name="mode",description="Choose the mode this set of buttons will be in. Default: Click to get/remove a role",required=False,opt_type=OptionTypes.INTEGER,
    choices=[SlashCommandChoice(name="Get or remove a role", value=1),SlashCommandChoice(name="Get a role, no removing", value=2),SlashCommandChoice(name="Only one role allowed", value=3)])
    @new_role()
    @slash_option(name="button_colour",description="Choose what colour the button will be. Default: Blurple",required=False,opt_type=OptionTypes.INTEGER,
    choices=[SlashCommandChoice(name="Blurple", value=1),SlashCommandChoice(name="Green", value=3),SlashCommandChoice(name="Red", value=4),SlashCommandChoice(name="Gray", value=2)])
    @slash_option(name="requirement_role",description="Choose a role. Members will be required to have this role to use the button.",required=False,opt_type=OptionTypes.ROLE)
    @slash_option(name="ignore_role",description="Choose a role. Members with this role will be ignored.",required=False,opt_type=OptionTypes.ROLE)
    @slash_option(name='name', description='Give the button a custom name', opt_type=OptionTypes.STRING, required=False)
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def rb_edit(self, ctx: InteractionContext, message_id:OptionTypes.STRING, button_id:OptionTypes.STRING, channel:OptionTypes.CHANNEL=None, mode:OptionTypes.INTEGER=None,
    button_colour:OptionTypes.INTEGER=None, new_role: OptionTypes.ROLE = None, requirement_role: OptionTypes.ROLE = None, ignore_role: OptionTypes.ROLE = None, name: OptionTypes.STRING=None):
        if (mode is None) and (button_colour is None) and (new_role is None) and (requirement_role is None) and (ignore_role is None):
            return await ctx.send('You have to change at least one option to change')
        if channel is None:
            channel = ctx.channel
        edits = ''
        message = await channel.fetch_message(message_id)
        if message is not None:
            if (button_colour is None) and (new_role is None) and (name is None):
                return await ctx.send("`Name`, `Button colour` and `New Role` can't be edited together")
            if button_colour is not None:
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
                        if button_colour == 1:
                            colour = 'Blurple'
                        elif button_colour == 2:
                            colour = 'Gray'
                        elif button_colour == 3:
                            colour = 'Green'
                        elif button_colour == 4:
                            colour = 'Red'
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
                button.requirement_role_id = requirement_role.id
                await button.save()
                edits = edits + f"Requirement Role: {requirement_role.mention}\n"
            if ignore_role is not None:
                button.ignored_role_id= ignore_role.id
                await button.save()
                edits = edits + f"Ignore Role: {ignore_role.mention}\n"
            await ctx.send(embed=Embed(color=0x0c73d3,description=f"Button `{button_id}` succesfully edited\n{edits}"))
        else:
            await ctx.send('Message not found')

    @slash_command(name='rolebuttons', sub_cmd_name='remove', sub_cmd_description="Edit a behaviour of a role button", scopes=[435038183231848449,149167686159564800])
    @button_id()
    @message_id()
    @channel()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def rb_remove(self, ctx: InteractionContext, message_id:OptionTypes.STRING, button_id:OptionTypes.STRING, channel:OptionTypes.CHANNEL=None):
        if channel is None:
            channel = ctx.channel
        message = await channel.fetch_message(message_id)
        if message is None:
            return await ctx.send(f"Can't find a message with that id", ephemeral=True)
        components = []
        if message.components != []:
            for ob in message.components:
                components = components + ob.components
        
        for b in components:
            if b.custom_id == button_id:
                components.remove(b)
        
        rows = []
        button_row = []
        for component in components:
            if component is not None and component.type == ComponentTypes.BUTTON:
                button_row.append(component)

                if len(button_row) == 5:
                    rows.append(ActionRow(*button_row))
                    button_row = []

                continue

            if button_row:
                rows.append(ActionRow(*button_row))
                button_row = []

            if component is not None:
                if component.type == ComponentTypes.ACTION_ROW:
                    rows.append(component)
                elif component.type == ComponentTypes.SELECT:
                    rows.append(ActionRow(component))
        if button_row:
            rows.append(ActionRow(*button_row))

        if len(rows) > 5:
            raise ValueError("Number of rows exceeds 5.")

        await message.edit(components=rows)

        button = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':channel.id, 'msg_id':message.id, 'button_id':button_id})
        await button.delete()
        await ctx.send(f"Button `{button_id}` successfully deleted")

    @slash_command(name='rolebuttons', sub_cmd_name='list', sub_cmd_description="List all role buttons on this server", scopes=[435038183231848449,149167686159564800])
    async def rb_list(self, ctx: InteractionContext):
        from dis_snek.ext.paginators import Paginator
        def chunks(l, n):
            n = max(1, n)
            return (l[i:i+n] for i in range(0, len(l), n))
        
        def mlis(lst, s, e):
            nc = list(chunks(lst, 20))
            mc = ''
            for testlist in nc[s:e]:
                for m in testlist:
                    mc = mc + m
            return mc

        def newpage(title, buttoninfo):
            embed = Embed(title=title,
            description=buttoninfo,
            color=0x0c73d3)
            return embed
        
        role_buttons = db.button_roles.find({'guildid':ctx.guild_id})
        
        buttons = []
        async for button in role_buttons:
            role = ctx.guild.get_role(button.roleid)
            if role is None:
                role = 'Role missing'
            elif role is not None:
                role = role.mention
            if button.requirement_role_id is not None:
                req_role = ctx.guild.get_role(button.requirement_role_id)
                if req_role is None:
                    reqrole = 'Req. role missing'
                elif role is not None:
                    reqrole = req_role.mention
            else:
                reqrole = 'No req. role'
            if button.ignored_role_id is not None:
                ign_role = ctx.guild.get_role(button.ignored_role_id)
                if ign_role is None:
                    ignrole = 'Ign. role missing'
                elif role is not None:
                    ignrole = ign_role.mention
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
        nc = list(chunks(buttons, 20))
        
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
    async def on_button_press_role_add_mode_1(self, event: Component):
        ctx = event.context
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':1})
        if rolebutton is not None:
            role_to_add = ctx.guild.get_role(rolebutton.roleid)
            if role_to_add is not None:
                if ctx.author.has_permission(Permissions.ADMINISTRATOR) == False:
                    if rolebutton.ignored_role_id is not None:
                        ign_role = ctx.guild.get_role(rolebutton.ignored_role_id)
                        if ign_role is not None:
                            if ign_role in ctx.author.roles:
                                return await ctx.send(f"I can't give members with {ign_role.mention} role the {role_to_add.mention} role", ephemeral=True)
                    
                    if rolebutton.requirement_role_id is not None:
                        req_role = ctx.guild.get_role(rolebutton.requirement_role_id)
                        if req_role is not None:
                            if req_role not in ctx.author.roles:
                                return await ctx.send(f"You don't have {req_role.mention}, which you need to have for me to give you {role_to_add.mention}", ephemeral=True)
                
                if role_to_add not in ctx.author.roles:
                    await ctx.author.add_role(role_to_add)
                    await ctx.send(embed=Embed(color=0x0c73d3, description=f"I gave you role {role_to_add.mention}"), ephemeral=True)
    
    @listen()
    async def on_button_press_role_add_mode_2(self, event: Component):
        ctx = event.context
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':2})
        if rolebutton is not None:
            role_to_add = ctx.guild.get_role(rolebutton.roleid)
            if role_to_add is not None:
                if ctx.author.has_permission(Permissions.ADMINISTRATOR) == False:
                    if rolebutton.ignored_role_id is not None:
                        ign_role = ctx.guild.get_role(rolebutton.ignored_role_id)
                        if ign_role is not None:
                            if ign_role in ctx.author.roles:
                                return await ctx.send(f"I can't give members with {ign_role.mention} role the {role_to_add.mention} role", ephemeral=True)
                    
                    if rolebutton.requirement_role_id is not None:
                        req_role = ctx.guild.get_role(rolebutton.requirement_role_id)
                        if req_role is not None:
                            if req_role not in ctx.author.roles:
                                return await ctx.send(f"You don't have {req_role.mention}, which you need to have for me to give you {role_to_add.mention}", ephemeral=True)
            
                if role_to_add not in ctx.author.roles:
                    await ctx.author.add_role(role_to_add)
                    await ctx.send(embed=Embed(color=0x0c73d3, description=f"I gave you role {role_to_add.mention}"), ephemeral=True)
                elif role_to_add in ctx.author.roles:
                    await ctx.send(embed=Embed(color=0x0c73d3, description=f"This role {role_to_add.mention} can't be taken away from you"), ephemeral=True)
    
    @listen()
    async def on_button_press_role_add_mode_3(self, event: Component):
        ctx = event.context
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':3})
        if rolebutton is not None:
            role_to_add = ctx.guild.get_role(rolebutton.roleid)                 
            if role_to_add is not None:
                if ctx.author.has_permission(Permissions.ADMINISTRATOR) == False:
                    if rolebutton.ignored_role_id is not None:
                        ign_role = ctx.guild.get_role(rolebutton.ignored_role_id)
                        if ign_role is not None:
                            if ign_role in ctx.author.roles:
                                return await ctx.send(f"I can't give members with {ign_role.mention} role the {role_to_add.mention} role", ephemeral=True)
                    
                    if rolebutton.requirement_role_id is not None:
                        req_role = ctx.guild.get_role(rolebutton.requirement_role_id)
                        if req_role is not None:
                            if req_role not in ctx.author.roles:
                                return await ctx.send(f"You don't have {req_role.mention}, which you need to have for me to give you {role_to_add.mention}", ephemeral=True)
                
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
                                    old_roles = old_roles + f'{old_role.mention} '
                
                if old_roles == 'and took away ':
                    old_roles = ''
            
                if role_to_add not in ctx.author.roles:
                    await ctx.author.add_role(role_to_add)
                    await ctx.send(embed=Embed(color=0x0c73d3, description=f"I gave you role {role_to_add.mention} {old_roles}"), ephemeral=True)

    @listen()
    async def on_button_press_role_remove_mode_1(self, event: Component):
        ctx = event.context
        rolebutton = await db.button_roles.find_one({'guildid':ctx.guild_id, 'channelid':ctx.channel.id, 'msg_id':ctx.message.id, 'button_id':ctx.custom_id, 'mode':1})
        if rolebutton is not None:
            role_to_remove = ctx.guild.get_role(rolebutton.roleid)
            if role_to_remove is not None:
                if role_to_remove in ctx.author.roles:
                    await ctx.author.remove_role(role_to_remove)
                    await ctx.send(embed=Embed(color=0x0c73d3, description=f"I took away a role {role_to_remove.mention} from you"), ephemeral=True)

    @listen()
    async def on_button_press_role_remove_mode_3(self, event: Component):
        ctx = event.context
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
                                old_roles = old_roles + f'{old_role.mention} '

            role_to_remove = ctx.guild.get_role(rolebutton.roleid)                 
            if role_to_remove is not None:
                if role_to_remove in ctx.author.roles:
                    await ctx.author.remove_role(role_to_remove)
                    old_roles = old_roles + f'{role_to_remove.mention} '
                    await ctx.send(embed=Embed(color=0x0c73d3, description=f"I took away {old_roles}"), ephemeral=True)

def setup(bot):
    ButtonRoles(bot)