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

def setup(bot):
    GiveRoles(bot)