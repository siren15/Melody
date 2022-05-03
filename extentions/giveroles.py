import re

from dis_snek import Snake, slash_command, InteractionContext, OptionTypes, Permissions, Scale, Embed, check
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *

class GiveRoles(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @slash_command(name='giveyou', sub_cmd_name='_', sub_cmd_description="Give members a role from predefined list of roles")
    @user()
    @giveyou_name()
    @check(member_permissions(Permissions.BAN_MEMBERS))
    async def giveyourole(self, ctx: InteractionContext, user:OptionTypes.USER=None, giveyou_name:str=None):
        if user is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a user"), ephemeral=True)
        if giveyou_name is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a giveyou name"), ephemeral=True)

        
        regx = {'$regex': f"^{giveyou_name}$", '$options':'i'}
        gy = await db.giveyou.find_one({'name':regx, 'guildid': ctx.guild_id})

        if gy is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: Couldn't find `{giveyou_name}` as a giveyou for {ctx.guild.name}"), ephemeral=True)

        role = ctx.guild.get_role(gy.roleid)

        if role in user.roles:
            await user.remove_role(role, reason=f'{ctx.author.display_name}|{ctx.author.id} removed a giveyou {giveyou_name}')
            embed = Embed(
                description=f"I have removed {role.mention} from {user.mention}",
                color=0x0c73d3)
        elif role not in user.roles:
            await user.add_role(role, reason=f'{ctx.author.display_name}|{ctx.author.id} assigned a giveyou {giveyou_name}')
            embed = Embed(
                description=f"I have assigned {role.mention} to {user.mention}",
                color=0x0c73d3)
        await ctx.send(embed=embed)
    
    @slash_command(name='giveyou', sub_cmd_name='create', sub_cmd_description="Create giveyou's")
    @giveyou_name()
    @role()
    @check(member_permissions(Permissions.MANAGE_ROLES))
    async def giveyourole_create(self, ctx: InteractionContext, giveyou_name:str=None, role:OptionTypes.ROLE=None):
        if giveyou_name is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a giveyou name"), ephemeral=True)
        if role is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a role"), ephemeral=True)

        
        regx = {'$regex': f"^{giveyou_name}$", '$options':'i'}
        gy = await db.giveyou.find_one({'name':regx, 'guildid': ctx.guild_id})

        if gy is not None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: `{giveyou_name}` already exists as a giveyou for {ctx.guild.name}"), ephemeral=True)

        await db.giveyou(guildid=ctx.guild_id, name=giveyou_name, roleid=role.id).insert()
        await ctx.send(embed=Embed(color=0x0c73d3, description=f"giveyou `{giveyou_name}` created for {role.mention}"))
    
    @slash_command(name='giveyou', sub_cmd_name='delete', sub_cmd_description="Delete giveyou's")
    @giveyou_name()
    @check(member_permissions(Permissions.MANAGE_ROLES))
    async def giveyourole_delete(self, ctx: InteractionContext, giveyou_name:str=None):
        if giveyou_name is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a giveyou name"), ephemeral=True)

        regx = {'$regex': f"^{giveyou_name}$", '$options':'i'}
        gy = await db.giveyou.find_one({'name':regx, 'guildid': ctx.guild_id})

        if gy is not None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: `{giveyou_name}` is not a giveyou for {ctx.guild.name}"), ephemeral=True)

        role = ctx.guild.get_role(gy.roleid)
        await ctx.send(embed=Embed(color=0x0c73d3, description=f"giveyou `{giveyou_name}` deleted from {role.mention}"))
        await gy.delete()
    
    @slash_command(name='giveyou', sub_cmd_name='list', sub_cmd_description="Lists all giveyous for guild")
    @check(member_permissions(Permissions.BAN_MEMBERS))
    async def giveyourole_list(self, ctx: InteractionContext):
        
        from dis_snek.ext.paginators import Paginator
        def chunks(l, n):
            n = max(1, n)
            return (l[i:i+n] for i in range(0, len(l), n))
        
        def page_list(lst, s, e):
            nc = list(chunks(lst, 20))
            mc = ''
            for testlist in nc[s:e]:
                for m in testlist:
                    mc = mc + m
            return mc

        def newpage(title, names, roles):
            embed = Embed(title=title,
            color=0x0c73d3)
            embed.add_field(name='Giveyou', value=names, inline=True)
            embed.add_field(name='Role', value=roles, inline=True)
            return embed

        
        gy = db.giveyou.find({"guildid":ctx.guild_id})
        names = []
        roles = []
        async for g in gy:
            names.append(f"{g.name}\n")
            role = ctx.guild.get_role(g.roleid)
            if role is None:
                roles.append(f'[ROLE NOT FOUND]({g.roleid})\n')
            else:
                roles.append(f"{role.mention}\n")
        if names == []:
            embed = Embed(description=f"There are no giveyous for {ctx.guild.name}.",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
            return
        s = -1
        e = 0
        embedcount = 1
        nc = list(chunks(names, 20))
        
        embeds = []
        while embedcount <= len(nc):
            s = s+1
            e = e+1
            embeds.append(newpage(f'List of giveyous for {ctx.guild.name}', page_list(names, s, e), page_list(roles, s, e)))
            embedcount = embedcount+1
            
        paginator = Paginator(
            client=self.bot, 
            pages=embeds,
            timeout_interval=80,
            show_select_menu=False)
        await paginator.send(ctx)
    
    @slash_command(name='role', description="Add/remove users to a role or roles")
    @members()
    @roles()
    @check(member_permissions(Permissions.MANAGE_ROLES))
    async def give_role(self, ctx: InteractionContext, members:str=None, roles:str=None):
        if members is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a user"), ephemeral=True)
        if roles is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a role"), ephemeral=True)

        raw_mem_list = members.split(',')
        member_list =[]
        for m in raw_mem_list:
            m = m.replace('<', '')
            m = m.replace('@', '')
            m = m.replace('!', '')
            m = m.replace('&', '')
            m = m.replace('>', '')
            member_list.append(m)

        raw_roles_list = roles.split(',')
        roles_list = []
        for r in raw_roles_list:
            r = r.replace('<', '')
            r = r.replace('@', '')
            r = r.replace('!', '')
            r = r.replace('&', '')
            r = r.replace('>', '')
            roles_list.append(r)
        
        for member_id in member_list:
            member = ctx.guild.get_member(member_id)
            removed_roles = 'I have removed: '
            added_roles = 'I have assigned: '
            for role_id in roles_list:
                role = ctx.guild.get_role(role_id)
                if member.has_role(role) == True:
                    await member.remove_role(role)
                    removed_roles = removed_roles + f' {role.mention}'
                else:
                    await member.add_role(role)
                    added_roles = added_roles + f' {role.mention}'
            embed = Embed(description=f'Roles changed for {member.mention}\n\n{added_roles}\n\n{removed_roles}', color=0x0c73d3)
            await ctx.send(embed=embed)

    # @slash_command(name='colourme', description="Give yourself a colour role from predefined list of roles. You are able to have just one.")
    # @colourme_name()
    # async def colourme_add(self, ctx: InteractionContext, colourme_name:str=None):
    #     await ctx.defer()
    #     member = ctx.author
    #     if colourme_name is None:
    #         embed = Embed(
    #             description=":x: Please provide a colourme name",
    #             color=0xDD2222)
    #         await ctx.send(embed=embed)
    #         return
    #     
    #     cm_regx = re.compile(f"^{colourme_name}$", re.IGNORECASE)
    #     cr = await db.find_one(colourme, {"colourme_name":cm_regx, "guildid":ctx.guild_id})
    #     if cr is None:
    #         await ctx.send(embed=Embed(color=0xDD2222, description=f':x: {colourme_name} not found in colourme roles'))
    #         return
        
    #     if cr.ignore_role_id is not None:
    #         ignore_roles = re.sub('[<@&>]', '', cr.ignore_role_id)
    #         ignore_roles = ignore_roles.split(',')
    #         member_roles = [role.id for role in member.roles]
    #         ign_roles = set(ignore_roles) & set(member_roles)
    #         if len(ign_roles) == 1:
    #             for i in ign_roles:
    #                 role = ctx.guild.get_role(int(i))
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f":x: You have {role.mention}, members with this role can't get {colourme_name}"))
    #             return
    #         elif len(ign_roles) > 1:
    #             rs = ''
    #             for i in ign_roles:
    #                 role = ctx.guild.get_role(int(i))
    #                 rs = rs+f' {role.mention}'
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f":x: You have {rs}, members with these roles can't get {colourme_name}"))
    #             return
        
    #     if cr.requirement_role_id is not None:
    #         reqire_roles = re.sub('[<@&>]', '', cr.requirement_role_id)
    #         reqire_roles = reqire_roles.split(',')
    #         member_roles = [role.id for role in member.roles]
    #         req_roles = set(reqire_roles) & set(member_roles)
    #         if len(req_roles) == 1:
    #             for i in req_roles:
    #                 role = ctx.guild.get_role(int(i))
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f":x: You are missing {role.mention}, you have to have this role to get {colourme_name}"))
    #             return
    #         elif len(req_roles) > 1:
    #             rs = ''
    #             for i in req_roles:
    #                 role = ctx.guild.get_role(int(i))
    #                 rs = rs+f' {role.mention}'
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f":x: You are missing {rs}, you have to have these roles to get {colourme_name}"))
    #             return          

    #     nr = await db.find(colourme, {"guildid":ctx.guild_id})
    #     def get_other_role(member, nr):
    #         other_roles = [id.colourme_role_id for id in nr]
    #         member_roles = [r.id for r in member.roles]
    #         other_role = set(other_roles) & set(member_roles)
    #         for other_role in other_role:
    #             return other_role
    #         return None

    #     if get_other_role(member, nr) is None:
    #         colourme_role = ctx.guild.get_role(cr.colourme_role_id)
    #         await member.add_role(colourme_role)
    #         await ctx.send(embed=Embed(color=0x0c73d3, description=f'I have assigned {colourme_name}|{colourme_role.mention} to you'))
    #         return
    #     else:
    #         other_role = ctx.guild.get_role(get_other_role(member, nr))
        
    #     if other_role.id == cr.colourme_role_id:
    #         await member.remove_role(other_role)
    #         await ctx.send(embed=Embed(color=0x0c73d3, description=f'I have removed {colourme_name}|{other_role.mention} from you'))
    #         return
    #     else:
    #         await member.remove_role(other_role)
    #         colourme_role = ctx.guild.get_role(cr.colourme_role_id)
    #         await member.add_role(colourme_role)
    #         await ctx.send(embed=Embed(color=0x0c73d3, description=f'I have assigned {colourme_name}|{colourme_role.mention} to you'))
    
    # @slash_command(name='colorme', sub_cmd_name='create', sub_cmd_description="Creates a colourme")
    # @colourme_name()
    # @role()
    # async def colourme_create(self, ctx: InteractionContext, colourme_name:str=None, role:OptionTypes.ROLE=None):
    #     await ctx.defer()
    #     perms = await has_perms(ctx.author, Permissions.MANAGE_ROLES)
    #     if (perms == True):
    #         if role is None:
    #             await ctx.send('You have to include a role', ephemeral=True)
    #             return
    #         elif colourme_name is None:
    #             await ctx.send('You have to include a colourme name', ephemeral=True)
    #             return
            
    #         
    #         cm_regx = re.compile(f"^{colourme_name}$", re.IGNORECASE)
    #         cr = await db.find_one(colourme, {"colourme_name":cm_regx, "guildid":ctx.guild_id})
    #         if cr is not None:
    #             crole = ctx.guild.get_role(cr.colourme_role_id)
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f':x: {colourme_name} is already a colourme for {crole.mention}'))
    #             return
    #         cr = await db.find_one(colourme, {"colourme_role_id":role.id, "guildid":ctx.guild_id})
    #         if cr is not None:
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f':x: {role.mention} is already a colourme as {cr.colourme_name}'))
    #             return
    #         await db.save(colourme(guildid=ctx.guild_id, colourme_name=colourme_name, colourme_role_id=role.id))
    #         await ctx.send(embed=Embed(color=0x0c73d3, description=f'Colourme {colourme_name}|{role.mention} was created'))
    
    # @slash_command(name='colorme', sub_cmd_name='add_reqirement', sub_cmd_description="Adds a requirement role to colourme")
    # @colourme_name()
    # @role()
    # async def colourme_req_add(self, ctx: InteractionContext, colourme_name:str=None, role:OptionTypes.ROLE=None):
    #     await ctx.defer()
    #     perms = await has_perms(ctx.author, Permissions.MANAGE_ROLES)
    #     if (perms == True):
    #         if role is None:
    #             await ctx.send('You have to include a role', ephemeral=True)
    #             return
    #         
    #         cm_regx = re.compile(f"^{colourme_name}$", re.IGNORECASE)
    #         cr = await db.find_one(colourme, {"colourme_name":cm_regx, "guildid":ctx.guild_id})
    #         if cr is None:
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f':x: {colourme_name} is not a colourme in this server'))
    #             return
    #         if cr.requirement_role_id is None:
    #             cr.requirement_role_id = f'<@&{role.id}>'
    #         else:
    #             reqire_roles = re.sub('[<@&>]', '', cr.requirement_role_id)
    #             reqire_roles = reqire_roles.split(',')
    #             if role.id in reqire_roles:
    #                 await ctx.send(embed=Embed(color=0xDD2222, description=f':x: {role.mention} is already a requirement role for `{colourme_name}`'))
    #                 return
    #             cr.requirement_role_id = f'{cr.requirement_role_id}, <@&{role.id}>'
    #         await db.save(cr)
    #         await ctx.send(embed=Embed(color=0x0c73d3, description=f'Requirement role {role.mention} was added for colourme {colourme_name}'))
    
    # @slash_command(name='colorme', sub_cmd_name='add_ingore', sub_cmd_description="Adds a role to colourme")
    # @colourme_name()
    # @role()
    # async def colourme_ign_add(self, ctx: InteractionContext, colourme_name:str=None, role:OptionTypes.ROLE=None):
    #     await ctx.defer()
    #     perms = await has_perms(ctx.author, Permissions.MANAGE_ROLES)
    #     if (perms == True):
    #         if role is None:
    #             await ctx.send('You have to include a role', ephemeral=True)
    #             return
    #         
    #         cm_regx = re.compile(f"^{colourme_name}$", re.IGNORECASE)
    #         cr = await db.find_one(colourme, {"colourme_name":cm_regx, "guildid":ctx.guild_id})
    #         if cr is None:
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f':x: {colourme_name} is not a colourme in this server'))
    #             return
    #         if cr.ignore_role_id is None:
    #             cr.ignore_role_id = f'<@&{role.id}>'
    #         else:
    #             ignore_roles = re.sub('[<@&>]', '', cr.ignore_role_id)
    #             ignore_roles = ignore_roles.split(',')
    #             if role.id in ignore_roles:
    #                 await ctx.send(embed=Embed(color=0xDD2222, description=f':x: {role.mention} is already an ignore role for `{colourme_name}`'))
    #                 return
    #             cr.ignore_role_id = f'{cr.ignore_role_id}, <@&{role.id}>'
    #         await db.save(cr)
    #         await ctx.send(embed=Embed(color=0x0c73d3, description=f'Ignore role {role.mention} was added for colourme {colourme_name}'))
    
    # @slash_command(name='colorme', sub_cmd_name='delete', sub_cmd_description="Deletes a colourme")
    # @colourme_name()
    # async def colourme_delete(self, ctx: InteractionContext, colourme_name:str=None):
    #     await ctx.defer()
    #     perms = await has_perms(ctx.author, Permissions.MANAGE_ROLES)
    #     if (perms == True):
    #         if colourme_name is None:
    #             await ctx.send('You have to include a colourme name', ephemeral=True)
    #             return

    #         
    #         cm_regx = re.compile(f"^{colourme_name}$", re.IGNORECASE)
    #         cr = await db.find_one(colourme, {"colourme_name":cm_regx, "guildid":ctx.guild_id})
    #         if cr is None:
    #             await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {colourme_name} isn't a colourme for this guild"))
    #             return
    #         role = ctx.guild.get_role(cr.colourme_role_id)
    #         await ctx.send(embed=Embed(color=0x0c73d3, description=f'Colourme {colourme_name}|{role.mention} was deleted'))
    #         await db.delete(cr)
    
    # @slash_command(name='colorme', sub_cmd_name='list', sub_cmd_description="Lists all colourmes for guild")
    # async def colourme_list(self, ctx: InteractionContext):
    #     await ctx.defer()
    #     from dis_snek.ext.paginators import Paginator
    #     def chunks(l, n):
    #         n = max(1, n)
    #         return (l[i:i+n] for i in range(0, len(l), n))
        
    #     def mlis(lst, s, e):
    #         nc = list(chunks(lst, 20))
    #         mc = ''
    #         for l in nc[s:e]:
    #             for m in l:
    #                 mc = mc + m
    #         return mc

    #     def newpage(title, names):
    #         embed = Embed(title=title,
    #         color=0x0c73d3)
    #         embed.add_field(name='Colourme | Role | Requirement | Ignored', value=names, inline=True)
    #         return embed

    #     
    #     cnames = await db.find(colourme, {"guildid":ctx.guild_id})
        
    #     if cnames is None:
    #         embed = Embed(description=f"There are no colourmes for {ctx.guild}.",
    #                     color=0x0c73d3)
    #         await ctx.send(embed=embed)
    #         return
    #     for n in cnames:
    #         if (n.requirement_role_id is None) and (n.ignore_role_id is None):
    #             names = [f"{name.colourme_name} | <@&{name.colourme_role_id}> | No requirement roles | No ignore roles\n\n" for name in cnames]
    #         elif (n.requirement_role_id is None) and (n.ignore_role_id is not None):
    #             names = [f"{name.colourme_name} | <@&{name.colourme_role_id}> | No requirement roles | {name.ignore_role_id}\n\n" for name in cnames]
    #         elif (n.requirement_role_id is not None) and (n.ignore_role_id is None):
    #             names = [f"{name.colourme_name} | <@&{name.colourme_role_id}> | {name.requirement_role_id} | No ignore roles\n\n" for name in cnames]
    #         else:
    #             names = [f"{name.colourme_name} | <@&{name.colourme_role_id}> | {name.requirement_role_id} | {name.ignore_role_id}\n\n" for name in cnames]

    #     s = -1
    #     e = 0
    #     embedcount = 1
    #     nc = list(chunks(names, 20))
        
    #     embeds = []
    #     while embedcount <= len(nc):
    #         s = s+1
    #         e = e+1
    #         embeds.append(newpage(f'List of colourmes for {ctx.guild.name}', mlis(names, s, e)))
    #         embedcount = embedcount+1
            
    #     paginator = Paginator(
    #         client=self.bot, 
    #         pages=embeds,
    #         timeout_interval=80,
    #         show_select_menu=False)
    #     await paginator.send(ctx)

def setup(bot):
    GiveRoles(bot)