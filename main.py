import discord
from discord.ext import commands, tasks
import os
import asyncio
import re

# إعدادات الـ Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# الثوابت (IDs)
SERVER_ID = 1474476686262145146
ROLE_EVERYONE = 1478799212312531089 
CHANNEL_SOURCE = 1511089965424054292
CHANNEL_DEST = 1508470750456315974
CHANNEL_NEWS = 1506417724010528928
KEEP_ALIVE_CHANNEL = 1511851709704704020

# متغيرات النظام
match_data = {}
live_mode = False

# دالة تحويل الوقت
def parse_time(time_str):
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    match = re.match(r"(\d+)([dhms])", time_str.lower())
    if match:
        return int(match.group(1)) * units[match.group(2)]
    return 0

# نظام البقاء نشطاً (رندر)
@tasks.loop(seconds=5)
async def keep_alive():
    channel = bot.get_channel(KEEP_ALIVE_CHANNEL)
    if channel:
        msg = await channel.send("تم، أنا أعمل..")
        await asyncio.sleep(5)
        await msg.delete()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    keep_alive.start()

# 1. أمر !رتب المطور
@bot.command()
async def رتب(ctx, role1: discord.Role, role2: discord.Role):
    if ctx.channel.id != CHANNEL_SOURCE:
        return

    await ctx.send(f"تم اختيار {role1.name} ضد {role2.name}. كم باقي وتبدأ؟ (مثال: 2d, 1h, 30m, 10s)")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    msg = await bot.wait_for('message', check=check)
    total_seconds = parse_time(msg.content)
    
    if total_seconds == 0:
        await ctx.send("صيغة الوقت غير صحيحة.")
        return

    embed = discord.Embed(title="⚽ مباراة جديدة قادمة", color=discord.Color.blue())
    embed.add_field(name="المواجهة", value=f"{role1.mention} VS {role2.mention}", inline=False)
    
    target_channel = bot.get_channel(CHANNEL_DEST)
    timer_msg = await target_channel.send(content=f"<@&{ROLE_EVERYONE}>", embed=embed)
    
    while total_seconds >= 0:
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_format = f"{hours:02}:{minutes:02}:{seconds:02}"
        
        embed.set_field_at(0, name="المواجهة", value=f"{role1.mention} VS {role2.mention}\n⏰ الموعد: {time_format}", inline=False)
        await timer_msg.edit(embed=embed)
        
        await asyncio.sleep(1)
        total_seconds -= 1
        
    await timer_msg.edit(content="⚽ المباراة بدأت الآن!")

# 2. أمر !صار
@bot.command()
async def صار(ctx, role1: discord.Role, role2: discord.Role):
    await ctx.send("كم النتيجة؟")
    msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    embed = discord.Embed(title="⚽ تحديث نتيجة المباراة", color=0xFFD700)
    embed.add_field(name="المواجهة", value=f"{role1.mention} VS {role2.mention}", inline=False)
    embed.add_field(name="النتيجة الحالية", value=f"**{msg.content}**", inline=False)
    target_channel = bot.get_channel(CHANNEL_DEST)
    if target_channel: await target_channel.send(embed=embed)

# 3. أمر !خبر
@bot.command()
async def خبر(ctx, *, content):
    target_channel = bot.get_channel(CHANNEL_NEWS)
    if target_channel:
        embed = discord.Embed(title="📢 خبر عاجل", description=content, color=0xFF0000)
        await target_channel.send(content=f"<@&{ROLE_EVERYONE}>", embed=embed)
        await ctx.send("تم نشر الخبر!")

# 4. أوامر !اخبار و !الغاء
@bot.command()
async def اخبار(ctx):
    global live_mode
    live_mode = True
    await ctx.send("تم تفعيل وضع الأخبار.")

@bot.command()
async def الغاء(ctx):
    global live_mode
    live_mode = False
    await ctx.send("تم إيقاف وضع الأخبار.")

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if live_mode and message.channel.id == CHANNEL_SOURCE and not message.content.startswith('!'):
        target_channel = bot.get_channel(CHANNEL_DEST)
        if target_channel:
            embed = discord.Embed(description=message.content, color=0x00FF00)
            embed.set_author(name="تغطية حية", icon_url=bot.user.avatar.url)
            await target_channel.send(embed=embed)
    await bot.process_commands(message)

bot.run(os.getenv('DISCORD_TOKEN'))
