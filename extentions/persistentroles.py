from dis_snek import Snake, slash_command, InteractionContext, OptionTypes, Permissions, Scale, Embed, check, listen, AutoDefer
from .src.mongo import *
from .src.slash_options import *
from .src.customchecks import *

class PersistentRoles(Scale):
    def __init__(self, bot: Snake):
        self.bot = bot
    
    @slash_command(name='persistentroles', sub_cmd_name='add', sub_cmd_description="Make a role persistent", scopes=[435038183231848449])
    @role()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def persistent_roles_add(self, ctx, role:OptionTypes.ROLE=None):
        if role == None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a role"), ephemeral=True)
        elif role == ctx.guild.my_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is my role, you cannot manage this role"), ephemeral=True)
        elif role == ctx.guild.default_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is a default role, you cannot manage this role"), ephemeral=True)
        db = await odm.connect()
        ranks = await db.find_one(leveling_roles, {'guildid':ctx.guild_id, 'roleid':role.id})
        if ranks != None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is a rank, which makes it already a persistant role."), ephemeral=True)
        pers_roles = await db.find_one(persistent_roles_settings, {'guildid':ctx.guild_id, 'roleid':role.id})
        if pers_roles != None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is already a persistent role."), ephemeral=True)
        await db.save(persistent_roles_settings(guildid=ctx.guild_id, roleid=role.id))
        if ctx.author.guild_avatar != None:
            avatarurl = f'{ctx.author.guild_avatar.url}.png'
        else:
            avatarurl = f'{ctx.author.avatar.url}.png'
        embed = Embed(description=f"I have made {role.mention} a persistent role.",
                                  color=0x0c73d3)
        embed.set_footer(text=f'{ctx.author}|{ctx.author.id}',icon_url=avatarurl)
        await ctx.send(embed=embed)

    @slash_command(name='persistentroles', sub_cmd_name='remove', sub_cmd_description="Remove role from persistent roles", scopes=[435038183231848449])
    @role()
    @check(member_permissions(Permissions.ADMINISTRATOR))
    async def persistent_roles_remove(self, ctx, role:OptionTypes.ROLE=None):
        if role == None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a role"), ephemeral=True)
        elif role == ctx.guild.my_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is my role, you cannot manage this role"), ephemeral=True)
        elif role == ctx.guild.default_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is a default role, you cannot manage this role"), ephemeral=True)
        db = await odm.connect()
        ranks = await db.find_one(leveling_roles, {'guildid':ctx.guild_id, 'roleid':role.id})
        if ranks.roleid == role.id:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is a rank, which makes it a persistant role that you can't remove from persistent roles."), ephemeral=True)
        pers_roles = await db.find_one(persistent_roles_settings, {'guildid':ctx.guild_id, 'roleid':role.id})
        if pers_roles.roleid != role.id:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is not a persistent role."), ephemeral=True)
        await db.delete(pers_roles)
        if ctx.author.guild_avatar != None:
            avatarurl = f'{ctx.author.guild_avatar.url}.png'
        else:
            avatarurl = f'{ctx.author.avatar.url}.png'
        embed = Embed(description=f"I have removed {role.mention} from persistent roles.",
                                  color=0x0c73d3)
        embed.set_footer(text=f'{ctx.author}|{ctx.author.id}',icon_url=avatarurl)
        await ctx.send(embed=embed)
    
    @slash_command(name='persistentroles', sub_cmd_name='list', sub_cmd_description="List all the persistent roles", scopes=[435038183231848449])
    async def persistent_roles_list(self, ctx):
        from .src.paginators import Paginator
        def chunks(l, n):
            n = max(1, n)
            return (l[i:i+n] for i in range(0, len(l), n))
        
        def mlis(lst, s, e):
            nc = list(chunks(lst, 20))
            mc = ''
            for l in nc[s:e]:
                for m in l:
                    mc = mc + m
            return mc

        def newpage(title, roles):
            embed = Embed(title=title,
            color=0x0c73d3)
            embed.add_field(name='Roles', value=roles, inline=True)
            return embed

        db = await odm.connect()
        level_roles = await db.find(leveling_roles, {"guildid":ctx.guild.id})
        pr = await db.find(persistent_roles_settings, {'guildid':ctx.guild.id})
        level_roles = [lvl.roleid for lvl in level_roles]
        pers_roles = [r.roleid for r in pr]
        all_persistent_roles = level_roles+pers_roles

        if all_persistent_roles == []:
            embed = Embed(description=f"There are no persistent roles for {ctx.guild.name}.",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
            return
        roles = []
        for r in all_persistent_roles:
            role = await ctx.guild.get_role(r)
            if role == None:
                roles.append(f'{r}[ROLE NOT FOUND]\n')
            else:
                roles.append(f"{role.mention}\n")

        s = -1
        e = 0
        embedcount = 1
        nc = list(chunks(roles, 20))
        
        embeds = []
        while embedcount <= len(nc):
            s = s+1
            e = e+1
            embeds.append(newpage(f'List of persistent roles for {ctx.guild.name}', mlis(roles, s, e)))
            embedcount = embedcount+1
            
        paginator = Paginator(
            client=self.bot, 
            pages=embeds,
            timeout_interval=80,
            show_select_menu=False)
        await paginator.send(ctx)
    
    @listen()
    async def on_member_remove(self, event):
        guild= event.member.guild
        member = event.member
        member_roles = [role.id for role in member.roles if role.name != '@everyone' if role.name != 'Limbo']
        if member_roles == []:
            return
        db = await odm.connect()
        level_roles = await db.find(leveling_roles, {"guildid":guild.id})
        pers_roles = await db.find(persistent_roles_settings, {'guildid':guild.id})
        level_roles = [lvl.roleid for lvl in level_roles]
        pers_roles = [r.roleid for r in pers_roles]
        all_persistent_roles = level_roles+pers_roles
        member_roles = [str(role.id) for role in member.roles if role.id in all_persistent_roles]
        if member_roles == []:
            return
        roles = ','.join(member_roles)
        await db.save(persistent_roles(guildid=guild.id, user=member.id, roles=roles))
    
    @listen()
    async def on_member_add(self, event):
        guild = event.member.guild
        member = event.member
        db = await odm.connect()
        p_r = await db.find_one(persistent_roles, {'guildid':guild.id, 'user':member.id})
        if p_r != None:
            roles = [await guild.get_role(int(id_)) for id_ in p_r.roles.split(",") if len(id_)]
            for role in roles:
                if role not in member.roles:
                    await member.add_role(role, '[pt]persistent_role stored in db was added back to member on rejoin')
        else:
            p_r = await db.find_one(persistentroles, {'guildid':guild.id, 'userid':member.id})
            if p_r != None:
                roles = [await guild.get_role(int(id_)) for id_ in p_r.roles.split(",") if len(id_)]
                level_roles = await db.find(leveling_roles, {"guildid":guild.id})
                pers_roles = await db.find(persistent_roles_settings, {'guildid':guild.id})
                level_roles = [lvl.roleid for lvl in level_roles]
                pers_roles = [r.roleid for r in pers_roles]
                all_persistent_roles = level_roles+pers_roles
                member_roles = [role.id for role in roles if role.id in all_persistent_roles]
                for role in member_roles:
                    if role not in member.roles:
                        await member.add_role(role, '[pt]persistent_role stored in db was added back to member on rejoin')
            else:
                mem_lvl = await db.find_one(leveling, {'guildid':guild.id, 'memberid':member.id})
                if mem_lvl != None:
                    level_roles = await db.find(leveling_roles, {"guildid":guild.id, 'level':{'$lte':mem_lvl.level}})
                    if level_roles != None:
                        for roleid in level_roles:
                            role = await guild.get_role(roleid.roleid)
                            if role not in member.roles:
                                await member.add_role(role)

def setup(bot):
    PersistentRoles(bot)