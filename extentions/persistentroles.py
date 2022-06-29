from naff import Client, slash_command, InteractionContext, OptionTypes, Permissions, Extension, Embed, check, listen, AutoDefer, SlashCommand
from extentions.touk import BeanieDocuments as db
from utils.slash_options import *
from utils.customchecks import *

class PersistentRoles(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
    persistent_roles = SlashCommand(name='persistentroles',  description='Manage persistent roles', default_member_permissions=Permissions.ADMINISTRATOR)
    @persistent_roles.subcommand(sub_cmd_name='add', sub_cmd_description="Make a role persistent")
    @role()
    async def persistent_roles_add(self, ctx, role:OptionTypes.ROLE=None):
        # if role is None:
        #     return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a role"), ephemeral=True)
        if role == ctx.guild.my_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is my role, you cannot manage this role"), ephemeral=True)
        elif role == ctx.guild.default_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is a default role, you cannot manage this role"), ephemeral=True)
        
        ranks = await db.leveling_roles.find_one({'guildid':ctx.guild_id, 'roleid':role.id})
        if ranks is not None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is a rank, which makes it already a persistant role."), ephemeral=True)
        pers_roles = await db.persistent_roles_settings.find_one({'guildid':ctx.guild_id, 'roleid':role.id})
        if pers_roles is not None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is already a persistent role."), ephemeral=True)
        await db.persistent_roles_settings(guildid=ctx.guild_id, roleid=role.id).insert()
        if ctx.author.guild_avatar is not None:
            avatarurl = f'{ctx.author.guild_avatar.url}.png'
        else:
            avatarurl = f'{ctx.author.avatar.url}.png'
        embed = Embed(description=f"I have made {role.mention} a persistent role.",
                                  color=0x0c73d3)
        embed.set_footer(text=f'{ctx.author}|{ctx.author.id}',icon_url=avatarurl)
        await ctx.send(embed=embed)

    @persistent_roles.subcommand(sub_cmd_name='remove', sub_cmd_description="Remove role from persistent roles")
    @role()
    async def persistent_roles_remove(self, ctx, role:OptionTypes.ROLE=None):
        if role is None:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: Please provide a role"), ephemeral=True)
        elif role == ctx.guild.my_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is my role, you cannot manage this role"), ephemeral=True)
        elif role == ctx.guild.default_role:
            return await ctx.send(embed=Embed(color=0xDD2222, description=":x: This is a default role, you cannot manage this role"), ephemeral=True)
        
        ranks = await db.leveling_roles.find_one({'guildid':ctx.guild_id, 'roleid':role.id})
        if ranks.roleid == role.id:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is a rank, which makes it a persistant role that you can't remove from persistent roles."), ephemeral=True)
        pers_roles = await db.persistent_roles_settings.find_one({'guildid':ctx.guild_id, 'roleid':role.id})
        if pers_roles.roleid != role.id:
            return await ctx.send(embed=Embed(color=0xDD2222, description=f":x: {role.mention} is not a persistent role."), ephemeral=True)
        await pers_roles.delete()
        if ctx.author.guild_avatar is not None:
            avatarurl = f'{ctx.author.guild_avatar.url}.png'
        else:
            avatarurl = f'{ctx.author.avatar.url}.png'
        embed = Embed(description=f"I have removed {role.mention} from persistent roles.",
                                  color=0x0c73d3)
        embed.set_footer(text=f'{ctx.author}|{ctx.author.id}',icon_url=avatarurl)
        await ctx.send(embed=embed)
    
    @persistent_roles.subcommand(sub_cmd_name='list', sub_cmd_description="List all the persistent roles")
    async def persistent_roles_list(self, ctx):
        from naff.ext.paginators import Paginator
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

        
        leveling_roles = db.leveling_roles.find({"guildid":ctx.guild.id})
        level_roles = []
        async for lvl in leveling_roles:
            level_roles.append(lvl.roleid)
        pr = db.persistent_roles_settings.find({'guildid':ctx.guild.id})
        pers_roles = []
        async for r in pr:
            pers_roles.append(r.roleid)

        all_persistent_roles = level_roles+pers_roles
        if all_persistent_roles == []:
            embed = Embed(description=f"There are no persistent roles for {ctx.guild.name}.",
                        color=0x0c73d3)
            await ctx.send(embed=embed)
            return
        roles = []
        for r in all_persistent_roles:
            role = ctx.guild.get_role(r)
            if role is None:
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
        member_roles = [role.id for role in member.roles if role.name != '@everyone']
        if member_roles == []:
            return
        
        p_r = await db.persistent_roles.find_one({'guildid':guild.id, 'user':member.id})
        if p_r is not None:
            await p_r.delete()
        leveling_roles = db.leveling_roles.find({"guildid":guild.id})
        level_roles = []
        async for lvl in leveling_roles:
            level_roles.append(lvl.roleid)

        persistent_roles = db.persistent_roles_settings.find({'guildid':guild.id})
        pers_roles = []
        async for r in persistent_roles:
            pers_roles.append(r.roleid)

        all_persistent_roles = level_roles+pers_roles
        member_roles = [str(role.id) for role in member.roles if role.id in all_persistent_roles]
        if member_roles == []:
            return
        roles = ','.join(member_roles)
        await db.persistent_roles(guildid=guild.id, user=member.id, roles=roles).insert()
    
    @listen()
    async def on_member_add(self, event):
        guild = event.member.guild
        member = event.member

        warnings = db.strikes.find({'guildid':guild.id, 'user':member.id, 'action':{'$regex':'^warn$', '$options':'i'}})
        warncount = []
        async for warn in warnings:
            if warn.type != 'Minor':
                warncount.append(warn.strikeid)
        if warncount != []:
            wrc = 0
            while wrc != len(warncount):
                warnrolename = f'Warning-{wrc+1}'
                wrc = wrc+1
                warn_role = [role for role in guild.roles if role.name == warnrolename]
                if warn_role == []:
                    role = await guild.create_role(name=warnrolename, reason='[automod]|[warn]created new warnrole as warnrole with this number did not exist yet')
                    await member.add_role(role, '[automod] Given back warnrole on server rejoin')
                else:
                    for role in warn_role:
                        await member.add_role(role, '[automod] Given back warnrole on server rejoin')

        p_r = await db.persistent_roles.find_one({'guildid':guild.id, 'user':member.id})
        if p_r is not None:
            roles = [guild.get_role(int(id_)) for id_ in p_r.roles.split(",") if len(id_)]
            for role in roles:
                if role not in member.roles:
                    await member.add_role(role, '[pt]persistent_role stored in db was added back to member on rejoin')
        else:
            p_r = await db.persistentroles.find_one({'guildid':guild.id, 'userid':member.id})
            if p_r is not None:
                roles = [guild.get_role(int(id_)) for id_ in p_r.roles.split(",") if len(id_)]
                leveling_roles = db.leveling_roles.find({"guildid":guild.id})
                level_roles = []
                async for lvl in leveling_roles:
                    level_roles.append(lvl.roleid)

                persistent_roles = db.persistent_roles_settings.find({'guildid':guild.id})
                pers_roles = []
                async for r in persistent_roles:
                    pers_roles.append(r.roleid)
                
                all_persistent_roles = level_roles+pers_roles
                member_roles = [role.id for role in roles if role.id in all_persistent_roles]
                for role in member_roles:
                    if role not in member.roles:
                        await member.add_role(role, '[pt]persistent_role stored in db was added back to member on rejoin')
            else:
                mem_lvl = await db.leveling.find_one({'guildid':guild.id, 'memberid':member.id})
                if mem_lvl is not None:
                    level_roles = db.leveling_roles.find({"guildid":guild.id, 'level':{'$lte':mem_lvl.level}})
                    roles = []
                    async for role in level_roles:
                        roles.append(role.roleid)
                    if level_roles != []:
                        for role_id in roles:
                            role = guild.get_role(role_id)
                            if role not in member.roles:
                                await member.add_role(role)

def setup(bot):
    PersistentRoles(bot)