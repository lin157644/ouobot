import json, asyncio, datetime
import discord
from discord.ext import tasks, commands
from core.classes import Cog_Extension

class Task(Cog_Extension):
    def __init__(self, *args, **kwargs):
        # 父類別.初始化屬性
        super().__init__(*args, **kwargs)
        # self.index = 0
        

        async def interval():
            print('Tasks Waiting...')
            await self.bot.wait_until_ready()
            self.channel = self.bot.get_channel(770144271503720469)
            print('Task Start')
            while not self.bot.is_closed():
                # await self.channel.send(f'現在時間:{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                await asyncio.sleep(10)
        self.isSigned = True
        self.bg_task = self.bot.loop.create_task(interval())
        self.sign_task.start()
        self.remove_idle.start()

    @commands.command()
    async def set_channel(self, ctx, ch: int):
        self.channel = self.bot.get_channel(ch)
        await ctx.send(f'Set Channel: {self.channel.mention}')

    @commands.command()
    async def set_time(self, ctx, time):
        with open('setting.json', 'r', encoding='utf8') as jfile:
            jdata = json.load(jfile)
        jdata['time'] = time
        with open('setting.json', 'w', encoding='utf8') as jfile:
            jdata = json.load(jfile)
        json.dump(jdata, jfile, indent=4)

    #內建task
    # def cog_unload(self):
    #     self.printer.cancel()

    # @tasks.loop(seconds=5.0)
    # async def printer(self):
    #     print(self.index)
    #     self.index += 1

    # @printer.before_loop
    # async def before_printer(self):
    #     print('Waiting...')
    #     await self.bot.wait_until_ready()

    @tasks.loop(seconds=1.0)
    async def remove_idle(self):
        for member in self.afkChannel.members:
            print(f'{member.name}是頑皮豹')
            await member.move_to(None)
            await member.send('你是頑皮豹')

        for member in self.msGrayChannel.members:
            if member.display_name != "格雷女士" and member != self.bot.user:
                print(f'{member.display_name}不是格雷女士')
                await member.move_to(None)
                await member.send('你不是格雷女士')

        for member in self.channelPLA.members:
            if member not in self.rolePLA.members and member != self.bot.user:
                await member.move_to(None)
                await member.send('你不是人民解放軍')
    
    @remove_idle.before_loop
    async def before_remove_idle(self):
        await self.bot.wait_until_ready()
        self.ouoserver = self.bot.get_guild(231851662761918464)
        self.afkChannel = self.bot.get_channel(815155739260616705)
        self.msGrayChannel = self.bot.get_channel(263005171049562112)
        self.channelPLA = self.bot.get_channel(551417617471111198)
        self.rolePLA = self.ouoserver.get_role(263001618579062795)
    


    @tasks.loop(hours=1.0)
    async def sign_task(self):
        channel = self.bot.get_guild(231851662761918464).get_channel(248822934460694528)
        await channel.send(f'{self.ouoserver.get_member(376687088705470464).mention} 用 [sign 簽到')
        self.isSigned = False
        await asyncio.sleep(180)
        if self.isSigned == False:
            await self.ouoserver.get_member(376687088705470464).send("你沒有簽到")
            await self.ouoserver.get_member(376687088705470464).kick()

    @sign_task.before_loop
    async def before_remove_idle(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def sign(self, ctx):
        if self.isSigned == False and ctx.author == self.ouoserver.get_member(376687088705470464):
            self.isSigned = True
            await ctx.send("已簽到")
        
        
def setup(bot):
    bot.add_cog(Task(bot))
