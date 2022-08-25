from naff import Client, Extension, Permissions, Embed, slash_command, InteractionContext, OptionTypes, check, ModalContext, Guild, listen, SlashCommand, modal
from utils.slash_options import *
from utils.customchecks import *
from extentions.touk import BeanieDocuments as db
from naff_audio import NaffQueue, YTAudio
from youtube_search import YoutubeSearch

def geturl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)
    for x in [x[0] for x in url]:
        return x

class Melody(Extension):
    def __init__(self, bot: Client):
        self.bot = bot
    
    melody = SlashCommand(name='melody', description='Allows me to play songs in the voice chat.')
    
    @melody.subcommand('play', sub_cmd_description='Plays a song from provided name or url')
    @slash_option("song", "The song to play", 3, True)
    async def melody_play(self, ctx: InteractionContext, song: str):
        if not ctx.voice_state:
            await ctx.author.voice.channel.connect()
        vc = ctx.voice_state

        url = geturl(song)
        if url is None:
            results = YoutubeSearch(song, max_results=1).to_dict()
            audio = await YTAudio.from_url(f"https://youtube.com{results[0]['url_suffix']}")
            playing = f"https://youtube.com{results[0]['url_suffix']}"
        else:
            audio = await YTAudio.from_url(url)
            playing = song
        
        await ctx.send(f"Now Playing: **{playing}**")
        await vc.play(audio)
    
    @melody.subcommand('queue', sub_cmd_description='Adds a song to a queue from provided name or url')
    @slash_option("song", "The song to play", 3, True)
    async def melody_queue(self, ctx: InteractionContext, song: str):
        if not ctx.voice_state:
            await ctx.author.voice.channel.connect()
        vc = ctx.voice_state
        
        queue = NaffQueue(vc)

        url = geturl(song)
        if url is None:
            results = YoutubeSearch(song, max_results=1).to_dict()
            audio = await YTAudio.from_url(f"https://youtube.com{results[0]['url_suffix']}")
            playing = f"https://youtube.com{results[0]['url_suffix']}"
        else:
            audio = await YTAudio.from_url(url)
            playing = song

        await ctx.send(f"Added to queue: **{playing}**")
        queue.put(audio)
        queue.start()
    
    @melody.subcommand('resume', sub_cmd_description='Resume playback.')
    async def melody_resume(self, ctx: InteractionContext):
        vc = ctx.voice_state
        if not vc:
            return await ctx.send("Can't do that. I'm not in a voice channel.")
        if vc.playing:
            return await ctx.send("I'm already playing a song.")
        if vc.stopped:
            return await ctx.send("Can't do that. I'm not playing anything.")
        if vc.paused:
            vc.resume()
            await ctx.send("I'm resuming your song.")
        else:
            await ctx.send("Can't do that. I'm already playing a song.")
    
    @melody.subcommand('pause', sub_cmd_description='Pause playback.')
    async def melody_pause(self, ctx: InteractionContext):
        vc = ctx.voice_state
        if not vc:
            return await ctx.send("Can't do that. I'm not in a voice channel.")
        if vc.stopped:
            return await ctx.send("Can't do that. I'm not playing anything.")
        if vc.paused:
            await ctx.send("I've already paused the playback.")
        if vc.playing:
            vc.pause()
            await ctx.send("I'm pausing your song.")
        else:
            await ctx.send("I'm not playing anyting.")
    
    @melody.subcommand('stop', sub_cmd_description='Stop playback.')
    async def melody_stop(self, ctx: InteractionContext):
        vc = ctx.voice_state
        if not vc:
            return await ctx.send("Can't do that. I'm not in a voice channel.")
        if vc.stopped:
            return await ctx.send("Can't do that. I'm not playing anything.")
        await vc.stop()
        await ctx.send("I've stopped the playback.")
    
    @melody.subcommand('leave', sub_cmd_description='Stop the playback and leave the voice chat.')
    async def melody_disconnect(self, ctx: InteractionContext):
        vc = ctx.voice_state
        if not vc:
            return await ctx.send("Can't do that. I'm not in a voice channel.")
        if not vc.stopped:
            await vc.stop()
        await ctx.send("I'm leaving the VC.")
        await vc.disconnect()
    
    @melody.subcommand('join', sub_cmd_description='Join a VC')
    async def melody_join(self, ctx: InteractionContext):
        vc = ctx.voice_state
        if vc:
            return await ctx.send("I'm already in a voice channel.")
        await ctx.send("I'm joining a VC.")
        await ctx.author.voice.channel.connect()

def setup(bot):
    Melody(bot)