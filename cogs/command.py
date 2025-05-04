import random
import time
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands import BucketType, CommandOnCooldown
from datetime import datetime, timedelta
from cogs.counter import get_count, update_count


async def check_channel_and_delete(message):
    """檢查頻道並刪除訊息，返回是否需要停止處理"""
    # 需要判斷用戶是否擁有這三個身份組中的任一個
    allowed_roles = ["可愛天才世界第一", "湊的工具人(MOD)", "管管"]
    
    # 獲取用戶所有身份組名稱
    user_roles = [role.name for role in message.author.roles]

    # 如果用戶擁有這三個身份組中的任意一個，則不刪除訊息
    if any(role in allowed_roles for role in user_roles):
        return False  # 不刪除訊息，繼續執行後續操作

    # 如果是 "湊湊福神社🍀" 頻道且用戶沒有上述身份組，則刪除訊息
    if message.channel.name == "湊湊福神社🍀" and not message.content.startswith("!每日抽籤"):
        print(f"{message.author} 在湊湊福神社🍀 頻道輸入了：{message.content}")  # 記錄訊息
        await message.delete()  # 刪除訊息
        await message.channel.send(f"{message.author.mention} 只能使用 `!每日抽籤` 指令喔！")
        return True  # 停止處理，消息已刪除

    return False  # 不需要刪除訊息，繼續處理

class CommandCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.lottery_cooldowns = {}  # user_id: datetime
        self.cooldowns = {}          # (user_id, tag): datetime
        self.cooldown_seconds = 5    # 可調整通用冷卻時間
        self.fortunes = [
            ("大吉：你的運氣極好，今後一段時間內，無論做什麼都會非常順利！成功將屬於你！", 10, "🎉"),
            ("中吉：這是個相對穩定的時期。努力會有所回報，保持積極心態，運氣會越來越好。", 10, "😊"),
            ("吉：今後會有些許順利。雖然並不完全是最好的運勢，但你會收穫一些小確幸。", 10, "🍀"),
            ("小吉：今天的運勢偏向小範圍的好運。雖然有些小困難，但仍然能夠順利克服，事事如意。", 10, "🌸"),
            ("半吉：今有些小波折，但並不會嚴重影響你的行程。調整心態，保持冷靜，你仍能度過。", 10, "🍃"),
            ("末吉：即使現在的運勢不太好，但它也只是暫時的。耐心等待，未來有轉機。", 10, "🍂"),
            ("ㄐ吉：不可思議的命運之力降臨，你被神秘的「ㄐ吉怪人」選中，這是命中注定的奇異時刻！你的未來將充滿未知與挑戰，迎接這場難以預料的命運之旅吧！", 0.1, "🌟"),
            ("凶：小心！近期的運勢偏向不利。不要輕易做出重大決策，保持冷靜並尋求他人建議。", 10, "💀"),
            ("大凶：運氣極差，可能會面臨一些不利的情況或挑戰。此時應該避開風險，做好準備。", 10, "☠️"),
        ]

    def get_today_reset_time(self):
        """取得今天的重置時間（早上 6 點），如果現在還沒到 6 點就回傳昨天 6 點"""
        now = datetime.now()
        reset_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now < reset_time:
            reset_time -= timedelta(days=1)
        return reset_time
    
    def is_lottery_on_cooldown(self, user_id):
        last_time = self.lottery_cooldowns.get(user_id)
        if last_time is None:
            return False
        return last_time >= self.get_today_reset_time()  # 你原本的邏輯

    def set_lottery_cooldown(self, user_id):
        self.lottery_cooldowns[user_id] = datetime.now()

    def is_on_cooldown(self, user_id, tag=None):
        key = (user_id, tag)
        last_time = self.cooldowns.get(key)
        if last_time is None:
            return False
        return last_time >= datetime.now() - timedelta(seconds=self.cooldown_seconds)

    def set_cooldown(self, user_id, tag=None):
        key = (user_id, tag)
        self.cooldowns[key] = datetime.now()
        
    
    @commands.command(name="每日抽籤")
    async def daily_fortune(self, message):
        """每天抽籤指令"""
        if message.channel.name != "湊湊福神社🍀":
            await message.channel.send(f"{message.author.mention} 只有在「湊湊福神社🍀」這個頻道可以抽籤喔！")
            return

        user_id = message.author.id
        if self.is_on_cooldown(user_id):
            await message.channel.send(f"{message.author.mention} 你今天已經抽過籤了，明天早上6點之後再來吧！")
            return

        # 抽籤開始
        self.set_lottery_cooldown(user_id)
        draw_msg = await message.channel.send("🎴")

        total_weight = sum(weight for _, weight, _ in self.fortunes)
        rand_num = random.uniform(0, total_weight)
        cumulative_weight = 0
        for fortune, weight, emoji in self.fortunes:
            cumulative_weight += weight
            if rand_num <= cumulative_weight:
                result = fortune
                result_emoji = emoji
                break

        await draw_msg.edit(content=result_emoji)
        await asyncio.sleep(0.4)
        await draw_msg.edit(content=f"{message.author.mention} 你的抽籤結果是：\n{result_emoji} {result}")
        print(f"{message.author}: 你的抽籤結果是：\n{result_emoji} {result}")

    @commands.command(name="清空抽籤")
    @commands.is_owner()  # 只有機器人擁有者可以使用，或你可以改成 @commands.has_permissions(...)
    async def clear_cooldowns(self, message):
        self.cooldowns.clear()
        print("[清空抽籤] 所有 cooldown 已清除")
        await message.channel.send("✅ 已清空所有使用者的抽籤紀錄。")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # 確保只有在 "湊湊福神社🍀" 頻道處理
        if await check_channel_and_delete(message):
            return

        content = message.content.strip()
        user_id = message.author.id

        if content in ["?", "？", "蛤", "三小"]:
            if not self.is_on_cooldown(user_id, "問號"):
                print(f"{message.author}: ?")  # log 印出
                await message.channel.send("蛤？三小")
                self.set_cooldown(user_id, "問號")

        elif any(kw in content for kw in ["安安", "早安", "早ㄤ", "你好", "ㄤㄤ"]):
            if not self.is_on_cooldown(user_id, "早安"):
                print(f"{message.author}: 早安")  # log 印出
                await message.channel.send(random.choice([
                    "安安今天過得好嗎",
                    "早安你好阿～今天也要元氣滿滿喔！",
                    "嗨嗨～新的一天又開始啦！",
                    "起床啦～不要賴床嘿～",
                    "哎呀～你終於醒啦～",
                    "早ㄤ早ㄤ ☀️ 今天天氣不錯喔～",
                    "咕咕咕～🐔 該起床囉～",
                    "早安早安！記得吃早餐唷～",
                    "嗚哇～天亮啦！打個哈欠 ☁️",
                    "新的開始～今天也要加油 💪"
                ]))
                self.set_cooldown(user_id, "早安")

        elif any(kw in content for kw in ["我要睡了", "晚安", "晚ㄤ"]):
            if not self.is_on_cooldown(user_id, "晚安"):
                print(f"{message.author}: 晚安")  # log 印出
                await message.channel.send(random.choice([
                    "晚安～祝你有個好夢～",
                    "晚ㄤ！夢裡見啦～",
                    "好啦好啦 快去睡，不然阿湊生氣氣 >:(",
                    "晚安世界，明天再繼續冒險！",
                    "晚安安安安～累了一天該休息囉～",
                    "阿湊祝你有個甜甜的夢 🌙🍬",
                    "休息是為了明天的耍廢 ✨",
                    "該上床了～晚安 🌃",
                    "晚安！蓋好棉被別著涼～",
                    "明天見啦，晚安 🌝"
                ]))
                self.set_cooldown(user_id, "晚安")

        elif any(kw in content for kw in ["該不該", "該嗎"]):
            if not self.is_on_cooldown(user_id, "該"):
                print(f"{message.author}: 該")  # log 印出
                await message.channel.send(random.choice([
                    # 該
                    "當然該啊，你還猶豫什麼！",
                    "該爆，這還用問嗎！",
                    "馬上就該，直接上！",
                    "必須該，沒得選！",
                    "現在就是最該的時候！",
                    # 不該
                    "不該啦，你冷靜一點。",
                    "先不要，現在不是時候。",
                    "不該，會後悔的！",
                    "理智點，這時候不行。",
                    "忍住，現在不該。"
                ]))
                self.set_cooldown(user_id, "該")

        elif "笑死" in content:
            if not self.is_on_cooldown(user_id, "笑死"):
                print(f"{message.author}: 笑死")  # log 印出
                await message.channel.send("真的 笑死")
                self.set_cooldown(user_id, "笑死")

        elif "sb" in content.lower():
            if not self.is_on_cooldown(user_id, "SB"):
                print(f"{message.author}: SB")  # log 印出
                await message.channel.send(f"{message.author.mention} 你才SB")
                self.set_cooldown(user_id, "SB")

        elif "ㄐㄐ" in content:
            if not self.is_on_cooldown(user_id, "ㄐㄐ"):
                print(f"{message.author}: ㄐㄐ")  # log 印出
                count = get_count("ㄐㄐ") + 1
                update_count("ㄐㄐ", count)
                await message.channel.send(f"我已經說ㄐㄐ第{count}次了！ㄐㄐ！")
                self.set_cooldown(user_id, "ㄐㄐ")

        elif "🍪" in content:
            if not self.is_on_cooldown(user_id, "🍪"):
                print(f"{message.author}: 🍪")  # log 印出
                count = get_count("🍪") + 1
                update_count("🍪", count)
                await message.channel.send(f"{message.author.mention} 阿嬤生產了第{count}片 🍪 了")
                self.set_cooldown(user_id, "🍪")

    # 靜默處理冷卻錯誤
    @commands.Cog.listener()
    async def on_command_error(self, message, error):
        if isinstance(error, CommandOnCooldown):
            return  # 冷卻中就什麼都不做
        raise error  # 其他錯誤繼續丟出來

    @commands.command(name="益生菌")
    @commands.cooldown(1, 5.0, BucketType.default)
    async def probiotic(self, message):
        if await check_channel_and_delete(message):
            return
        print(f"{message.author}: 益生菌")  # log 印出
        count = get_count("益生菌") + 1
        update_count("益生菌", count)
        await message.channel.send(f"餵阿湊吃第{count}包益生菌")

    @commands.command(name="可愛")
    @commands.cooldown(1, 5.0, BucketType.default)
    async def i_am_cute(self, message):
        if await check_channel_and_delete(message):
            return
        print(f"{message.author}: 可愛")  # log 印出
        count = get_count("可愛") + 1
        update_count("可愛", count)
        await message.channel.send(f"我很可愛對不對？快點誇我可愛！才誇了第{count}次而已！")

    @commands.command(name="🍪")
    @commands.cooldown(1, 5.0, BucketType.default)
    async def cookie(self, message):
        if await check_channel_and_delete(message):
            return
        print(f"{message.author}: 🍪")  # log 印出
        count = get_count("🍪") + 1
        update_count("🍪", count)
        await message.channel.send(f"{message.author.mention}阿嬤生產了第{count}片 🍪 了")

    @commands.command(name="買")
    @commands.cooldown(1, 5.0, BucketType.default)
    async def buy(self, message, *args):
        if await check_channel_and_delete(message):
            return
        print(f"{message.author}: 買")  # log 印出
        if len(args) != 2:
            await message.channel.send("用法錯誤！正確格式：`!買 A B`")
            return
        A, B = args
        await message.channel.send(f"{A}，其實你想要的是{B}對吧！？你的慾望阿，就像是一顆橡皮球一樣...")

    @commands.command(name="還")
    @commands.cooldown(1, 5.0, BucketType.default)
    async def again(self, message, *args):
        if await check_channel_and_delete(message):
            return
        print(f"{message.author}: 還")  # log 印出
        if len(args) != 2:
            await message.channel.send("用法錯誤！正確格式：`!還 A B`")
            return
        A, B = args
        await message.channel.send(f"{A}你還在{B}！叫你不要你還繼續！")

    @commands.command(name="外送")
    @commands.cooldown(1, 5.0, BucketType.default)
    async def delivery(self, message):
        if await check_channel_and_delete(message):
            return
        print(f"{message.author}: 外送")  # log 印出
        await message.channel.send(f"這裡沒有外送，誰再講外送就600，說的就是你 {message.author.mention}")

    @commands.command(name="指令")
    @commands.cooldown(1, 5.0, BucketType.default)
    async def show_commands(self, message):
        if await check_channel_and_delete(message):
            return
        print(f"{message.author}: 指令")  # log 印出
        commands_list = """```txt
!益生菌 : 餵阿湊吃益生菌
!買 A B : 慫恿你買東西
!還 A B : 叫你不要你還繼續
!可愛 : 快點誇阿湊
!外送 : 不準提
🍪 : 餅乾星人做🍪
ㄐㄐ : 喊ㄐㄐ
該不該 : 問問機爪人你該不該
!每日抽籤 : 抽取今日運勢
```"""
        await message.channel.send(commands_list)

async def setup(bot):
    await bot.add_cog(CommandCog(bot))
