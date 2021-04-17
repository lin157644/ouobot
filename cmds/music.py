#Lavalink is dead
import discord, datetime
import os
from discord import player
from discord.ext import commands
import youtube_dl
import asyncio
import wavelink
from core.classes import Cog_Extension
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice

guild_ids = [231851662761918464]

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracks = []

    def add(self, track):
        self.tracks.append(track)
    
    async def playQ(self):
        await self.play(self.tracks[0])
        print(self.tracks)
    
    async def advance(self):
        if len(self.tracks) == 1:
            self.tracks.pop(0)
        elif len(self.tracks) > 1:
            self.tracks.pop(0)
            await self.play(self.tracks[0])
        elif len(self.tracks) < 1:
            pass

class Music(Cog_Extension, wavelink.WavelinkMixin):

    def __init__(self, bot): 
        self.bot = bot

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    @wavelink.WavelinkMixin.listener("on_track_end")
    async def on_player_stop(self, node, payload):
        await payload.player.advance()
    
    async def start_nodes(self):
        await self.bot.wait_until_ready()

        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        await self.bot.wavelink.initiate_node(host='127.0.0.1',
                                              port=2333,
                                              rest_uri='http://127.0.0.1:2333',
                                              password='aaaabbbb',
                                              identifier='TEST',
                                              region='hong_kong')
    # Method Overloading in Python
    # Retrieve a player for the given guild ID. If None, a player will be created and returned.
    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.bot.wavelink.get_player(obj.guild.id, cls=Player)
        elif isinstance(obj, discord.Guild):
            return self.bot.wavelink.get_player(obj.id, cls=Player)
        

    @cog_ext.cog_slash(name="connent", description="連接至當前頻道", guild_ids=guild_ids)
    async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise discord.DiscordException('No channel to join. Please either specify a valid channel or join one.')
        # cls (Optional[class]) – An optional class to pass to build from, overriding the default Player class. This must be similar to Player. E.g a subclass.
        player = self.get_player(ctx)
        await ctx.send(f'Connecting to **`{channel.name}`**')
        await player.connect(channel.id)

    @cog_ext.cog_slash(name="play", description="播放", guild_ids=guild_ids)
    async def play(self, ctx, *, query: str):
        
        newtracks = await self.bot.wavelink.get_tracks(f'ytsearch:{query}')
        
        if not newtracks:
            return await ctx.send('Could not find any songs with that query.')

        if isinstance(newtracks, wavelink.TrackPlaylist):
            newtracks = newtracks.tracks[0]
        else:
            newtracks = newtracks[0]
            
        player = self.get_player(ctx.guild)
        if not player.is_connected:
            try:
                await player.connect(ctx.author.voice.channel.id)
            except AttributeError:
                raise discord.DiscordException('No channel to join. Please either specify a valid channel or join one.')
            
        
        embed=discord.Embed(title="已加入佇列: \n"+newtracks.title, url="", color=0x575757, timestamp=datetime.datetime.now())
        # embed.set_thumbnail(url=info['thumbnails'][-1]['url'])
        await ctx.send("", embed=embed)
        if len(player.tracks) == 0:
            player.add(newtracks)
            await player.playQ()
        else:
            player.add(newtracks)
    
    @cog_ext.cog_slash(name="queue", description="播放", guild_ids=guild_ids)
    async def queue(self, ctx):
        player = self.get_player(ctx)
        output = ""
        for song in player.tracks:
            output = output + song.title
        await ctx.send(output)


def setup(bot):
    bot.add_cog(Music(bot))
