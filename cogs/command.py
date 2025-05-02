from discord.ext import commands
from discord.ext.commands import BucketType, CommandOnCooldown
from cogs.counter import get_count, update_count


class CommandCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # 處理 "?" 訊息與特定關鍵字
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content == "?":
            await message.channel.send("蛤？三小")
        if message.content == "早安":
            await message.channel.send(f"{message.author.mention} 早安你好阿～")
        if message.content == "晚安":
            await message.channel.send(f"{message.author.mention} 晚安～祝你有個好夢～")
        if message.content == "ㄐㄐ":
            count = get_count("ㄐㄐ") + 1
            update_count("ㄐㄐ", count)
            await message.channel.send(f"我已經說ㄐㄐ第{count}次了！ㄐㄐ！")

    # 靜默處理冷卻錯誤
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            return  # 冷卻中就什麼都不做
        raise error  # 其他錯誤繼續丟出來

    @commands.command(name="益生菌")
    @commands.cooldown(1, 2.0, BucketType.default)
    async def probiotic(self, ctx):
        count = get_count("益生菌") + 1
        update_count("益生菌", count)
        await ctx.send(f"餵阿湊吃第{count}包益生菌")

    @commands.command(name="可愛")
    @commands.cooldown(1, 2.0, BucketType.default)
    async def i_am_cute(self, ctx):
        count = get_count("可愛") + 1
        update_count("可愛", count)
        await ctx.send(f"我很可愛對不對？快點誇我可愛！才誇了第{count}次而已！")

    @commands.command(name="🍪")
    @commands.cooldown(1, 2.0, BucketType.default)
    async def cookie(self, ctx):
        count = get_count("🍪") + 1
        update_count("🍪", count)
        await ctx.send(f"{ctx.author.mention}阿嬤生產了第{count}片 🍪 了")

    @commands.command(name="買")
    @commands.cooldown(1, 2.0, BucketType.default)
    async def buy(self, ctx, *args):
        if len(args) != 2:
            await ctx.send("用法錯誤！正確格式：`!買 A B`")
            return
        A, B = args
        await ctx.send(f"{A}，其實你想要的是{B}對吧！？你的慾望阿，就像是一顆橡皮球一樣...")

    @commands.command(name="還")
    @commands.cooldown(1, 2.0, BucketType.default)
    async def again(self, ctx, *args):
        if len(args) != 2:
            await ctx.send("用法錯誤！正確格式：`!還 A B`")
            return
        A, B = args
        await ctx.send(f"{A}你還在{B}！叫你不要你還繼續！")

    @commands.command(name="外送")
    @commands.cooldown(1, 2.0, BucketType.default)
    async def delivery(self, ctx):
        await ctx.send(f"這裡沒有外送，誰再講外送就600，說的就是你 {ctx.author.mention}")

    @commands.command(name="指令")
    @commands.cooldown(1, 2.0, BucketType.default)
    async def show_commands(self, ctx):
        commands_list = """```txt
!益生菌 : 餵阿湊吃益生菌
!買 A B : 慫恿你買東西
!還 A B : 叫你不要你還繼續
!可愛 : 快點誇阿湊
!外送 : 不準提
!🍪 : 餅乾星人做🍪
ㄐㄐ : ㄐㄐ
早安 : 早安
晚安 : 晚安
```"""
        await ctx.send(commands_list)


async def setup(bot):
    await bot.add_cog(CommandCog(bot))
