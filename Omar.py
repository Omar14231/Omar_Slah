import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# الثوابت (IDs)
SERVER_ID = 1474476686262145146
ROLE_EVERYONE = 1478799212312531089 
CHANNEL_SOURCE = 1511089965424054292 # روم الإعداد / المصدر
CHANNEL_DEST = 1508470750456315974 # روم السجل / العرض
CHANNEL_NEWS = 1506417724010528928 # روم أخبار المباريات

# متغيرات النظام
match_data = {}
live_mode = False

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 1. أمر !رتب
@bot.command()
async def رتب(ctx, role1: discord.Role, role2: discord.Role):
    if ctx.channel.id != CHANNEL_SOURCE:
        return

    match_data[ctx.author.id] = {"r1": role1, "r2": role2}
    await ctx.send(f"تم اختيار {role1.name} ضد {role2.name}. كم باقي وتبدأ المباراة؟")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for('message', check=check)
    time_str = msg.content
    
    embed = discord.Embed(title="⚽ مباراة جديدة قادمة", color=discord.Color.blue())
    embed.add_field(name="الفريق الأول", value=role1.mention, inline=True)
    embed.add_field(name="ضد", value="VS", inline=True)
    embed.add_field(name="الفريق الثاني", value=role2.mention, inline=True)
    embed.add_field(name="موعد البداية", value=time_str, inline=False)
    
    target_channel = bot.get_channel(CHANNEL_DEST)
    await target_channel.send(content=f"<@&{ROLE_EVERYONE}>", embed=embed)
    await ctx.send("تم إرسال تفاصيل المباراة إلى روم السجل!")

# 2. أمر !صار
@bot.command()
async def صار(ctx, role1: discord.Role, role2: discord.Role):
    await ctx.send("كم النتيجة؟ (اكتبها مثل: 1 - 0)")
    msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    
    embed = discord.Embed(title="⚽ تحديث نتيجة المباراة", color=0xFFD700)
    embed.add_field(name="المواجهة", value=f"{role1.mention} VS {role2.mention}", inline=False)
    embed.add_field(name="النتيجة الحالية", value=f"**{msg.content}**", inline=False)
    
    target_channel = bot.get_channel(CHANNEL_DEST)
    await target_channel.send(embed=embed)
    await ctx.send("تم تحديث النتيجة!")

# 3. أمر !خبر
@bot.command()
async def خبر(ctx, *, content):
    target_channel = bot.get_channel(CHANNEL_NEWS)
    embed = discord.Embed(title="📢 خبر عاجل", description=content, color=0xFF0000)
    await target_channel.send(content=f"<@&{ROLE_EVERYONE}>", embed=embed)
    await ctx.send("تم نشر الخبر!")

# 4. نظام !اخبار و !الغاء
@bot.command()
async def اخبار(ctx):
    global live_mode
    live_mode = True
    await ctx.send("تم تفعيل وضع الأخبار! كل رسالة هنا ستبث للروم الثاني.")

@bot.command()
async def الغاء(ctx):
    global live_mode
    live_mode = False
    await ctx.send("تم إيقاف وضع الأخبار.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if live_mode and message.channel.id == CHANNEL_SOURCE and not message.content.startswith('!'):
        target_channel = bot.get_channel(CHANNEL_DEST)
        embed = discord.Embed(description=message.content, color=0x00FF00)
        embed.set_author(name="تغطية حية", icon_url=bot.user.avatar.url)
        await target_channel.send(embed=embed)
    await bot.process_commands(message)

bot.run('9957')
