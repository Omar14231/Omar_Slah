import discord
from discord.ext import commands, tasks
import os
import asyncio
import re
from aiohttp import web

# إعدادات الـ Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# الثوابت (IDs)
CHANNEL_SOURCE = 1511089965424054292
CHANNEL_DEST = 1508470750456315974
CHANNEL_NEWS = 1506417724010528928
KEEP_ALIVE_CHANNEL = 1511851709704704020
ROLE_EVERYONE = 1478799212312531089 

live_mode = False

# دالة تحويل الوقت
def parse_time(time_str):
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    match = re.match(r"(\d+)([dhms])", time_str.lower())
    if match:
        return int(match.group(1)) * units[match.group(2)]
    return 0

# سيرفر وهمي لإرضاء رندر
async def web_server(request):
    return web.Response(text="البوت يعمل!")

async def start_server():
    app = web.Application()
    app.router.add_get('/', web_server)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080)))
    await site.start()

# نظام البقاء نشطاً (إرسال وحذف)
@tasks.loop(seconds=5)
async def keep_alive():
    channel = bot.get_channel(KEEP_ALIVE_CHANNEL)
    if channel:
        msg = await channel.send("تم، أنا أعمل..")
        await asyncio.sleep(4)
        await msg.delete()

@bot.event
async def on_ready():
    print(f'البوت يعمل كـ {bot.user}')
    await start_server()
    if not keep_alive.is_running():
        keep_alive.start()

# 1. أمر !رتب
@bot.command()
async def رتب(ctx, role1: discord.Role, role2: discord.Role):
    if ctx.channel.id != CHANNEL_SOURCE:
        return

    await ctx.send(f"تم اختيار {role1.name} ضد {role2.name}. اكتب الوقت (مثال: 1h أو 30m):")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    msg = await bot.wait_for('message', check=check)
    total_seconds = parse_time(msg.content)
    
    if total_seconds <= 0:
        await ctx.send("صيغة الوقت غير صحيحة.")
        return

    embed = discord.Embed(title="⚽ مباراة جديدة", color=discord.Color.blue())
    embed.add_field(name="المواجهة", value=f"{role1.mention} VS {role2.mention}", inline=False)
    
    target_channel = bot.get_channel(CHANNEL_DEST)
    timer_msg = await target_channel.send(content=f"<@&{ROLE_EVERYONE}>", embed=embed)
    
    while total_seconds >= 0:
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        time_format = f"{hours:02}:{minutes:02}:{seconds:02}"
        
        embed.set_field_at(0, name="المواجهة", value=f"{role1.mention} VS {role2.mention}\n⏰ الموعد: {time_format}", inline=False)
        await timer_msg.edit(embed=embed)
        
        await asyncio.sleep(1)
        total_seconds -= 1
        
    await timer_msg.edit(content="⚽ المباراة بدأت الآن!", embed=embed)

# 2. أمر !صار
@bot.command()
async def صار(ctx, role1: discord.Role, role2: discord.Role):
    await ctx.send("اكتب النتيجة (مثال: 1-0):")
    msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    embed = discord.Embed(title="⚽ نتيجة المباراة", color=0xFFD700)
    embed.add_field(name="المواجهة", value=f"{role1.mention} VS {role2.mention}", inline=False)
    embed.add_field(name="النتيجة", value=f"**{msg.content}**", inline=False)
    target_channel = bot.get_channel(CHANNEL_DEST)
    if target_channel: await target_channel.send(embed=embed)

# 3. أمر !خبر
@bot.command()
async def خبر(ctx, *, content):
    target_channel = bot.get_channel(CHANNEL_NEWS)
    if target_channel:
        embed = discord.Embed(title="📢 خبر عاجل", description=content, color=0xFF0000)
        await target_channel.send(content=f"<@&{ROLE_EVERYONE}>", embed=embed)
        await ctx.send("تم نشر الخبر.")

# 4. أوامر البث
@bot.command()
async def اخبار(ctx):
    global live_mode
    live_mode = True
    await ctx.send("تم تفعيل وضع البث الحي.")

@bot.command()
async def الغاء(ctx):
    global live_mode
    live_mode = False
    await ctx.send("تم إيقاف وضع البث الحي.")

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if live_mode and message.channel.id == CHANNEL_SOURCE and not message.content.startswith('!'):
        target_channel = bot.get_channel(CHANNEL_DEST)
        if target_channel:
            embed = discord.Embed(description=message.content, color=0x00FF00)
            await target_channel.send(embed=embed)
    await bot.process_commands(message)

bot.run(os.getenv('DISCORD_TOKEN'))
