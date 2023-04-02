from interactions import Client, Extension, Permissions, Embed, SlashContext, slash_command, InteractionContext, OptionType, check, ModalContext, Guild, listen, SlashCommand, Modal, AllowedMentions
from interactions.api.events.discord import MessageCreate
from utils.slash_options import *
from utils.customchecks import *
from extentions.touk import BeanieDocuments as db
import os
from ytmusicapi import YTMusic
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
load_dotenv()
database_url = os.getenv('database_url')

spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=os.getenv('spcid'), client_secret=os.getenv('spcs')))
ytmusic = YTMusic()

def get_spotify_url(string):
    regex = r"(https://open.spotify.com/(track|album)/[a-zA-Z0-9]+)"
    url = re.findall(regex,string)
    for x in [x[0] for x in url]:
        return x

class SpotifyToYoutube(Extension):
    def __init__(self, bot: Client):
        self.bot = bot

    @listen() 
    async def spotify_link_listen(self, event: MessageCreate):
        user = event.message.author # get the user who sent the message
        message = event.message.content # get the content of the message
        if user.bot: # if the user is a bot, return
            return
        if message is None: # if the message is empty, return
            return
        settings = await db.sp2yt.find_one({'guildid':event.message.guild.id}) # get the settings for the guild from the database
        if settings is None: # if there are no settings for the guild, insert default settings
            return await db.sp2yt(guildid=event.message.guild.id).insert()
        if not user.has_permission(Permissions.ADMINISTRATOR): # if the user is not an administrator
            if settings.ignored_users is not None: # if there are ignored users in the settings
                if user.id in settings.ignored_users: # if the user is in the ignored users list, return
                    return
            if settings.ignored_roles is not None: # if there are ignored roles in the settings
                if any(role for role in user.roles if role.id in settings.ignored_roles): # if the user has an ignored role, return
                    return
        if settings.music_channels is not None: # if there are music channels in the settings
            if event.message.channel.id not in settings.music_channels: # if the message is not in a music channel, return
                return
        spotify_url = get_spotify_url(message) # get the Spotify URL from the message
        if spotify_url is not None: # if there is a Spotify URL in the message
            if "track" in spotify_url: # if the URL is for a track
                song = spotify.track(spotify_url) # get the track information from the Spotify API
                query_type = 'songs'
            if "album" in spotify_url: # if the URL is for an album
                song = spotify.album(spotify_url) # get the album information from the Spotify API
                query_type = 'albums'
            youtube_search = ytmusic.search(f"{song['artists'][0]['name']} {song['name']}", query_type) # search for the song on YouTube Music
            if query_type == 'songs': # if the search is for a song
                url = f"https://music.youtube.com/watch?v={youtube_search[0]['videoId']}" # get the URL for the song on YouTube Music
            elif query_type == 'albums': # if the search is for an album
                albumsearch = ytmusic.get_album(youtube_search[0]['browseId']) # get the album information from YouTube Music
                url = f"https://music.youtube.com/playlist?list={albumsearch['audioPlaylistId']}" # get the URL for the album on YouTube Music
            await event.message.reply(url, allowed_mentions=AllowedMentions(replied_user=False)) # reply to the message with the YouTube Music URL

    @slash_command(name='sp2yt', description='Translate Spotify links to YouTube Music links')
    @slash_option(name='url', description='Spotify URL to translate', opt_type=OptionType.STRING, required=True)
    async def sp2yt(self, ctx:SlashContext, url: str):
        """/sp2yt
        Description:
            The sp2yt function takes a Spotify URL and converts it to a YouTube Music URL.
            It does this by first checking if the url is valid, then checks if it's either an album or song.
            If it's an album, we search for the album on YTMusic and get its playlist ID. We then send that playlist ID as a link to the user in chat.
            If it's not an album but instead is a song, we search for that song on YTMusic and get its videoId (the unique identifier of each video). We then send that videoId as a link to the user in chat
        
        Args:
            url: The spotify URL
        """
        settings = await db.sp2yt.find_one({'guildid':ctx.guild.id})
        if settings is None:
            return await db.sp2yt(guildid=ctx.guild.id).insert()
        spotify_url = get_spotify_url(url)
        if spotify_url is not None:
            if "track" in spotify_url:
                song = spotify.track(spotify_url)
                query_type = 'songs'
            if "album" in spotify_url:
                song = spotify.album(spotify_url)
                query_type = 'albums'
            # print(song["artists"][0]["name"], song['name'])
            youtube_search = ytmusic.search(f"{song['artists'][0]['name']} {song['name']}", query_type)
            # print(youtube_search[0])
            if query_type == 'songs':
                url = f"https://music.youtube.com/watch?v={youtube_search[0]['videoId']}"
            elif query_type == 'albums':
                albumsearch = ytmusic.get_album(youtube_search[0]['browseId'])
                url = f"https://music.youtube.com/playlist?list={albumsearch['audioPlaylistId']}"
            await ctx.send(url)
        else:
            await ctx.send("This is either not a Spotify URL or this Spotify URL is not supported. I only support Spotify Track and Album URLs.")
    
    sp2yt_manage = SlashCommand(name='sp2yt_manage', default_member_permissions=Permissions.ADMINISTRATOR, description='Manage the Spotify to YouTube settings.')

    @sp2yt_manage.subcommand('music_channel', 'add', 'Add a channel to music channels.')
    @channel()
    async def add_music_channel(self, ctx:InteractionContext, channel: OptionType.CHANNEL=None):
        """/sp2yt_manage music_channel add
        Description:
            Add a channel to the list of music channels. The bot will listen to spotify links in these channels.
        
        Args:
            channel (OptionType.CHANNEL): Specify the channel you want to add to the music channels list
        """
        await ctx.defer(ephemeral=True)
        if channel is None:
            channel = ctx.channel
        settings = await db.sp2yt.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.sp2yt(guildid=ctx.guild.id).insert()
            settings = await db.sp2yt.find_one({"guildid":ctx.guild.id})
        music_channels = settings.music_channels
        if music_channels is None:
            music_channels = list()
        if channel.id in music_channels:
            await ctx.send(f'{channel.mention} is already a music channel..', ephemeral=True)
        music_channels.append(channel.id)
        await settings.save()
        channel_mentions = [ctx.guild.get_channel(id) for id in music_channels]
        channel_mentions = [ch.mention for ch in channel_mentions if ch is not None]
        channel_mentions = ' '.join(channel_mentions)
        embed = Embed(description=f"Channel {channel.mention} set as a music channel.")
        embed.add_field('Music Channels', channel_mentions)
        await ctx.send(embed=embed, ephemeral=True)

    @sp2yt_manage.subcommand('music_channel', 'remove', 'Remove a channel from music channels.')
    @channel()
    async def remove_music_channel(self, ctx:InteractionContext, channel: OptionType.CHANNEL=None):
        """/sp2yt_manage music_channel remove
        description:
            Remove a channel from the list of music channels.
            If no channel is specified, it will remove the current channel.
        
        Args:
            channel (OptionType.CHANNEL): Specify the channel that is being removed from the music channels list
        """
        await ctx.defer(ephemeral=True)
        if channel is None:
            channel = ctx.channel
        settings = await db.sp2yt.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.sp2yt(guildid=ctx.guild.id).insert()
        music_channels = settings.music_channels
        if music_channels is None:
            music_channels = list()
        if channel.id not in music_channels:
            await ctx.send(f'{channel.mention} is not a music channel.', ephemeral=True)
        music_channels.remove(channel.id)
        await settings.save()
        channel_mentions = [ctx.guild.get_channel(id) for id in music_channels]
        channel_mentions = [ch.mention for ch in channel_mentions if ch is not None]
        channel_mentions = ' '.join(channel_mentions)
        embed = Embed(description=f"Channel {channel.mention} removed from being a music channel.")
        embed.add_field('Music Channels', channel_mentions)
        await ctx.send(embed=embed, ephemeral=True)
    
    @sp2yt_manage.subcommand('ignored_role', 'add', 'Make a role to be ignored in music channels.')
    @role()
    async def MusicAddIgnoredRoles(self, ctx:InteractionContext, role: OptionType.ROLE):
        """/sp2yt_manage ignored_role add
        Description:
            Add a role to the list of roles ignored in music channels.
            
        Args:
            role (OptionType.ROLE): Get the role that is being ignored
        """
        await ctx.defer(ephemeral=True)
        settings = await db.sp2yt.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.sp2yt(guildid=ctx.guild.id).insert()
        ignored_roles = settings.ignored_roles
        if ignored_roles is None:
            ignored_roles = list()
        if role.id in ignored_roles:
            await ctx.send(f'{role.mention} is already ignored in music channels.', ephemeral=True)
        ignored_roles.append(role.id)
        await settings.save()
        role_mentions = [ctx.guild.get_role(id) for id in ignored_roles]
        role_mentions = [r.mention for r in role_mentions if r is not None]
        role_mentions = ' '.join(role_mentions)
        embed = Embed(description=f"Role {role.mention} was added to roles ignored in music channels.")
        embed.add_field('Ignored Roles', role_mentions)
        await ctx.send(embed=embed, ephemeral=True)

    @sp2yt_manage.subcommand('ignored_role', 'remove', 'Remove a role from being ignored in music channels.')
    @role()
    async def MusicRemoveIgnoredRoles(self, ctx:InteractionContext, role: OptionType.ROLE):
        """/sp2yt_manage ignored_role remove
        Remove a role from the list of roles that are ignored in music channels.
        
        Args:
            role (OptionType.ROLE): Role that is gonna be ignored
        """
        await ctx.defer(ephemeral=True)
        settings = await db.sp2yt.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.sp2yt(guildid=ctx.guild.id).insert()
        ignored_roles = settings.ignored_roles
        if ignored_roles is None:
            ignored_roles = list()
        if role.id not in ignored_roles:
            await ctx.send(f'{role.mention} is not being ignored in music channels.', ephemeral=True)
        ignored_roles.remove(role.id)
        await settings.save()
        role_mentions = [ctx.guild.get_role(id) for id in ignored_roles]
        role_mentions = [r.mention for r in role_mentions if r is not None]
        role_mentions = ' '.join(role_mentions)
        embed = Embed(description=f"Role {role.mention} was removed from being ignored in music channels.")
        embed.add_field('Ignored Roles', role_mentions)
        await ctx.send(embed=embed, ephemeral=True)
    
    @sp2yt_manage.subcommand('ignored_member', 'add', 'Make a member to be ignored in music channels.')
    @user()
    async def MusicAddIgnoredMember(self, ctx:InteractionContext, user: OptionType.USER):
        """/sp2yt_manage ignored_member add
        Description:
            Add a user to the list of ignored users in music channels.
            This means that they will not be able to use any commands in music channels.
        
        Args:
            user (OptionType.USER): User to add to the ignored list
        """
        await ctx.defer(ephemeral=True)
        settings = await db.sp2yt.find_one({"guildid":ctx.guild.id})
        if settings is None:
            await db.sp2yt(guildid=ctx.guild.id).insert()
        ignored_users = settings.ignored_users
        if ignored_users is None:
            ignored_users = list()
        if user.id in ignored_users:
            await ctx.send(f'{user}|{user.id} is already ignored in music channels.', ephemeral=True)
        ignored_users.append(user.id)
        await settings.save()
        users = [ctx.guild.get_member(id) for id in ignored_users]
        users = [f'{r}({r.id})' for r in users if r is not None]
        users = ' '.join(users)
        embed = Embed(description=f"Member {user}({user.id}) was added to members ignored in music channels.")
        embed.add_field('Ignored Members', users)
        await ctx.send(embed=embed, ephemeral=True)


    @sp2yt_manage.subcommand('ignored_member', 'remove', 'Remove a member from being ignored in music channels.')
    @user()
    async def MusicRemoveIgnoredMember(self, ctx:InteractionContext, user: OptionType.USER):
        """/sp2yt_manage ignored_member remove
        Description:
            Remove a user from the ignored list for music channels.
            
        
        Args:
            user (OptionType.USER): Specify the user to be removed from the ignored list
        """
        await ctx.defer(ephemeral=True)
        settings = await db.sp2yt.find_one({"guildid":ctx.guild.id})
        if settings is None:
           await db.sp2yt(guildid=ctx.guild.id).insert()
        ignored_users = settings.ignored_users
        if ignored_users is None:
            ignored_users = list()
        if user.id not in ignored_users:
            await ctx.send(f'{user}|{user.id} is not being ignored in music channels.', ephemeral=True)
        ignored_users.remove(user.id)
        await settings.save()
        users = [ctx.guild.get_member(id) for id in ignored_users]
        users = [f'{r}({r.id})' for r in users if r is not None]
        users = ' '.join(users)
        embed = Embed(description=f"Member {user}({user.id}) was removed from being ignored in music channels.")
        embed.add_field('Ignored Members', users)
        await ctx.send(embed=embed, ephemeral=True)

def setup(bot):
    SpotifyToYoutube(bot)