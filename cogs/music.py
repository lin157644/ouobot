import discord, datetime
import wavelink
import json
from core.classes import Cog_Extension
from discord_slash import cog_ext
from discord_slash import context
from discord_slash.utils.manage_commands import create_option, create_choice
from dotenv import load_dotenv

with open('setting.json', 'r', encoding='utf8') as jfile:
    jdata = json.load(jfile)
GUILD_ID=jdata['guild_id']

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracks = []

    def add(self, track):
        self.tracks.append(track)
    
    async def playQ(self):
        await self.play(self.tracks[0])
    
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

    @wavelink.WavelinkMixin.listener('on_node_ready')
    async def on_node_ready(self, node: wavelink.Node):
         print(f'Node {node.identifier} is ready!')
    
    async def start_nodes(self):
        await self.bot.wait_until_ready()

        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        await self.bot.wavelink.initiate_node(host='127.0.0.1',
                                              port=2333,
                                              rest_uri='http://127.0.0.1:2333',
                                              password='aaaabbbb',
                                              identifier='NextBot',
                                              region='hong_kong')

    # Method Overloading in Python
    # Retrieve a player for the given guild ID. If None, a player will be created and returned.
    def get_player(self, obj):
        if isinstance(obj, discord.Guild):
            return self.bot.wavelink.get_player(obj.id, cls=Player)
        elif isinstance(obj, context.SlashContext):
            return self.bot.wavelink.get_player(obj.guild.id, cls=Player)
        

    @cog_ext.cog_slash(name="connent", description="連接至當前頻道", guild_ids=GUILD_ID)
    async def connect_slash(self, ctx, *, channel: discord.VoiceChannel=None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise discord.DiscordException('No channel to join. Please either specify a valid channel or join one.')
        # cls (Optional[class]) – An optional class to pass to build from, overriding the default Player class. This must be similar to Player. E.g a subclass.
        player = self.get_player(ctx)
        await ctx.send(f'Connecting to **`{channel.name}`**')
        await player.connect(channel.id)

    @cog_ext.cog_slash(name="play", description="播放", guild_ids=GUILD_ID)
    async def play_slash(self, ctx, *, query: str):
        await ctx.defer()
        newtracks = await self.bot.wavelink.get_tracks(f'ytsearch:{query}')
        
        if not newtracks:
            return await ctx.send('Could not find any songs with that query.')

        if isinstance(newtracks, wavelink.TrackPlaylist):
            newtracks = newtracks.tracks[0]
        else:
            newtracks = newtracks[0]
            
        player = self.get_player(ctx)
        if not player.is_connected:
            try:
                await player.connect(ctx.author.voice.channel.id)
            except AttributeError:
                raise discord.DiscordException('No channel to join. Please either specify a valid channel or join one.')
            
        
        embed=discord.Embed(title="已加入佇列: \n"+newtracks.title, url=newtracks.uri, color=0x575757, timestamp=datetime.datetime.now())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=newtracks.thumb)
        await ctx.send("", embed=embed)
        if len(player.tracks) == 0:
            player.add(newtracks)
            await player.playQ()
        else:
            player.add(newtracks)
    
    @cog_ext.cog_slash(name="queue", description="顯示佇列", guild_ids=GUILD_ID)
    async def queue_slash(self, ctx):
        channel = None
        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            await ctx.send("你不在頻道裡")
        else:
            channel = ctx.author.voice.channel
        
        player = self.get_player(ctx)

        if player.tracks:
            output = ""
            for index in range(len(player.tracks)):
                output = output + ('正在播放:\n   ' if index==0 else f'{index}. ') + player.tracks[index].title + '\n'
            await ctx.send(output)
        else:
            await ctx.send("佇列是空的")

    @cog_ext.cog_slash(name="volume", description="更改音量", options=[create_option(name='amount', description='輸入音量0~200(預設100)', option_type=4, required=True)], guild_ids=GUILD_ID)
    async def volume_slash(self, ctx, amount):
        player = self.get_player(ctx.guild)
        await player.set_volume(max(0,min(amount, 200)))
        await ctx.send(f'音量:{amount}%')
    
    @cog_ext.cog_slash(name="pause", description="暫停", guild_ids=GUILD_ID)
    async def pause_slash(self, ctx):
        player = self.get_player(ctx)
        await player.set_pause(not player.is_paused)
        await ctx.send('已暫停' if player.is_paused else '已繼續播放')

    @cog_ext.cog_slash(name="skip", description="跳過", guild_ids=GUILD_ID)
    async def skip_slash(self, ctx):
        player = self.get_player(ctx)
        await player.stop()
        await ctx.send('已跳過')
    
    @cog_ext.cog_slash(name="clear", description="清空佇列", guild_ids=GUILD_ID)
    async def clear_slash(self, ctx):
        player = self.get_player(ctx)
        player.tracks.clear()
        await ctx.send('已清空佇列')
    
    @cog_ext.cog_slash(name="disconnect", description="要機器人滾蛋", guild_ids=GUILD_ID)
    async def disconnect_slash(self, ctx):
        player = self.get_player(ctx)
        try:
            await player.destroy()
            await ctx.send('**輕輕的我走了，正如我輕輕的來**')
        except KeyError:
            await ctx.send('◢▆▅▄▃崩╰(〒皿〒)╯潰▃▄▅▇◣')
    
    @cog_ext.cog_slash(name="stop", description="終止播放", guild_ids=GUILD_ID)
    async def stop_slash(self, ctx):
        player = self.get_player(ctx)
        player.tracks.clear()
        await player.stop()
        await ctx.send('**已終止**')
        
def setup(bot):
    bot.add_cog(Music(bot))
