import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

DB_FILE = "bank_data.json"
SUPPORT_GUILD_ID = 1510395297279508620  
ADMIN_USER_ID = 1306034100544737461
ADMIN_ROLE_ID = 1510396218482757744
LOG_ROOM_EXPIRED = 1510397908653047848
LOG_ROOM_SUCCESS = 1510398868510998708

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"users": {}, "loans": {}}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_status(user_id, data):
    return data["users"].get(str(user_id), {}).get("status", "طبيعي")

async def check_admin_permission(interaction: discord.Interaction):
    if interaction.user.id == ADMIN_USER_ID: return True
    support_guild = bot.get_guild(SUPPORT_GUILD_ID)
    if not support_guild: return False
    member = support_guild.get_member(interaction.user.id)
    if not member:
        try: member = await support_guild.fetch_member(interaction.user.id)
        except: return False
    if member and any(role.id == ADMIN_ROLE_ID for role in member.roles): return True
    return False

@bot.event
async def on_ready():
    await bot.tree.sync()
    clean_expired_loans.start()
    print(f"========================================")
    print(f"🏦 تم تشغيل نظام السلف المركزي بنجاح!")
    print(f"🤖 الحساب المعرف: {bot.user.name}")
    print(f"========================================")

# ─── 1. أمر المساعدة ───
@bot.tree.command(name="help", description="عرض دليل استخدام نظام السلف (مخفي للآخرين).")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏦 نظام السلف والائتمان المركزي",
        description="أهلاً بك في نظام الضمان المالي المتقدم.\n\n"
                    "💡 **إذا كنت ترغب بطلب سلف أو استدانة كريدات من شخص آخر، يرجى استخدام الأمر التالي:**\n"
                    "👉 `/salafni`",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── 2. أمر تقديم السلف المعدل (يرسل للمنشن فوراً) ───
@bot.tree.command(name="salafni", description="تقديم طلب سلف من شخص محدد مع ذكر السبب والمبلغ.")
@app_commands.describe(المبلغ="كمية الكريدت المطلوبة", الشخص="الشخص المراد الاستدانة منه", السبب="سبب طلب السلف")
async def salafni(interaction: discord.Interaction, المبلغ: int, الشخص: discord.User, السبب: str):
    db = load_db()
    
    # التحقق من القيود وحظر الحسابات
    if get_user_status(interaction.user.id, db) == "محروم":
        await interaction.response.send_message("❌ عذراً، أنت مدرج في القائمة السوداء ومحروم من التسلف حالياً.", ephemeral=True)
        return

    if get_user_status(الشخص.id, db) == "محروم":
        await interaction.response.send_message("❌ هذا الشخص محروم من التعاملات المالية حالياً.", ephemeral=True)
        return

    if الشخص.id == interaction.user.id:
        await interaction.response.send_message("❌ لا يمكنك طلب سلف من نفسك!", ephemeral=True)
        return

    # إرسال رسالة تأكيد فورية للمستلف في السيرفر (مخفية)
    await interaction.response.send_message(f"⏳ **جاري إرسال طلب السلف إلى {الشخص.mention} في الخاص...** يرجى انتظاره ليقوم بالقبول أو الرفض.", ephemeral=True)

    # إعداد رسالة الطلب التي تذهب للمقرض (الشخص المنشن) فوراً
    lender_embed = discord.Embed(
        title="📩 طلب سلف مالي جديد وارد إليك",
        description=f"أهلاً بك، هناك عضو يطلب منك سلفاً مالياً (كريدت). هل توافق على إقراضه؟\n\n"
                    f"👤 **اسم مقدم الطلب:** {interaction.user.name} ({interaction.user.mention})\n"
                    f"💰 **المبلغ المراد استدانته:** {المبلغ:,} كريدت\n"
                    f"📝 **السبب المذكور:** {السبب}",
        color=discord.Color.gold()
    )
    
    class LenderView(discord.ui.View):
        def __init__(self): super().__init__(timeout=300) # مهلة 5 دقائق للرد
        
        @discord.ui.button(label="نعم، أوافق على إقراضه", style=discord.ButtonStyle.green)
        async def accept(self, idx: discord.Interaction, btn: discord.ui.Button):
            db_res = load_db()
            loan_id = f"{interaction.user.id}-{الشخص.id}"
            expire_date = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            
            db_res["loans"][loan_id] = {
                "borrower_id": interaction.user.id, 
                "lender_id": الشخص.id,
                "amount": المبلغ, 
                "reason": السبب, 
                "expire_at": expire_date
            }
            save_db(db_res)
            
            await idx.response.send_message(
                f"✅ **قمت بقبول الطلب بنجاح. الطرف الآخر لديه شهر واحد فقط للتسديد.**\n"
                f"في حال واجهتك أي مشكلة أو رغبت بتقديم بلاغ يرجى التوجه لسيرفر الدعم:\n"
                f"[اضغط هنا للتحدث للدعم](https://discord.gg/nQyHR8T3xs)"
            )
            
            # إشعار طالب السلف بالقبول
            try: await interaction.user.send(f"🎉 تم قبول طلب السلف الخاص بك من قِبل {الشخص.mention}. المبلغ: {المبلغ:,} كريدت. الموعد النهائي للسداد هو خلال 30 يوماً من الآن.")
            except: pass
            
            # لوق العمليات الناجحة
            log_chan = bot.get_channel(LOG_ROOM_SUCCESS)
            if log_chan:
                await log_chan.send(f"🤝 **عملية ناجحة:** تمت عملية استسلاف بين {interaction.user.mention} (طالب) و {الشخص.mention} (مقرض) بمبلغ {المبلغ:,} كريدت.")
            self.stop()

        @discord.ui.button(label="رفض الطلب", style=discord.ButtonStyle.red)
        async def decline(self, idx: discord.Interaction, btn: discord.ui.Button):
            await idx.response.send_message("❌ لقد قمت برفض هذا السلف المالي.")
            try: await interaction.user.send(f"❌ نعتذر منك، لقد تم رفض طلب السلف المقدم إلى {الشخص.name}.")
            except: pass
            self.stop()

    # إرسال الرسالة إلى الشخص المنشن مباشرة في الخاص
    try: 
        await الشخص.send(embed=lender_embed, view=LenderView())
    except discord.Forbidden:
        # إذا كانت خاصية الرسائل مقلقة عند الشخص المنشن
        await interaction.followup.send(f"❌ تعذر إرسال الرسالة إلى {الشخص.mention} لأن حساب الخاص لديه مغلق!", ephemeral=True)

# ─── 3. أمر إلغاء السلف الودي المتبادل ───
@bot.tree.command(name="إلغاء_السلف", description="إلغاء معاملة سلف جارية بالتراضي بين الطرفين.")
async def cancel_loan(interaction: discord.Interaction, الشخص: discord.User):
    db = load_db()
    id1 = f"{interaction.user.id}-{الشخص.id}"
    id2 = f"{الشخص.id}-{interaction.user.id}"
    loan_id = id1 if id1 in db["loans"] else (id2 if id2 in db["loans"] else None)

    if not loan_id:
        await interaction.response.send_message("❌ لا توجد معاملة سلف جارية وقائمة بينك وبين هذا الشخص حالياً.", ephemeral=True)
        return

    if db["loans"][loan_id]["lender_id"] == interaction.user.id:
        del db["loans"][loan_id]
        save_db(db)
        await interaction.response.send_message("✅ تم إلغاء السلف المالي بينكما وإسقاطه فوراً ومباشرة من طرف المقرِض.")
        try: await الشخص.send(f"⚠️ أحببنا إشعارك بأن {interaction.user.mention} قام بإلغاء وإسقاط السلف المالي القائم بينكما رسمياً.")
        except: pass
        return

    await interaction.response.send_message("⏳ تم إرسال طلب إلغاء السلف إلى الطرف الآخر للموافقة والتأكيد.")
    try:
        class CancelView(discord.ui.View):
            @discord.ui.button(label="موافقة على الإلغاء", style=discord.ButtonStyle.green)
            async def yes(self, idx: discord.Interaction, btn: discord.ui.Button):
                db_refresh = load_db()
                if loan_id in db_refresh["loans"]:
                    del db_refresh["loans"][loan_id]
                    save_db(db_refresh)
                await idx.response.send_message("✅ تم تأكيد موافقتك وإلغاء السلف بالكامل بين الطرفين.")
                try: await interaction.user.send(f"✅ وافق {الشخص.mention} على إلغاء السلف، وأغلقت القضية.")
                except: pass
        await الشخص.send(f"❓ يطلب {interaction.user.mention} إلغاء السلف القائم والمشترك بينكما، هل توافق؟", view=CancelView())
    except: pass

# ─── 4. أمر الدفع والتسديد ───
@bot.tree.command(name="الدفع", description="تسديد مستحقات مالية وإيقاف نظام السلف.")
async def pay_loan(interaction: discord.Interaction, الشخص: discord.User):
    db = load_db()
    loan_id = f"{interaction.user.id}-{الشخص.id}"
    if loan_id not in db["loans"]:
        await interaction.response.send_message("❌ لا يوجد سلف مسجل عليك لهذا الشخص لتدفعه.", ephemeral=True)
        return

    await interaction.response.send_message("⏳ تم إرسال طلب تأكيد استلام الدفعة المالية للمقرض للتحقق والقبول.")
    
    class PayView(discord.ui.View):
        @discord.ui.button(label="نعم، استلمت أموالي بالكامل", style=discord.ButtonStyle.green)
        async def yes(self, idx: discord.Interaction, btn: discord.ui.Button):
            db_res = load_db()
            if loan_id in db_res["loans"]: del db_res["loans"][loan_id]
            save_db(db_res)
            await idx.response.send_message("✅ تم تأكيد الاستلام المالي وأغلق السلف بنجاح.")
            try: await interaction.user.send("🎉 تم إغلاق وتأكيد سداد السلف الخاص بك بنجاح، شكراً لالتزامك!")
            except: pass

        @discord.ui.button(label="لا، لم أستلم شيء", style=discord.ButtonStyle.red)
        async def no(self, idx: discord.Interaction, btn: discord.ui.Button):
            await idx.response.send_message("❌ تم رفض التأكيد. إذا كان العضو يدّعي الكذب، يرجى تقديم بلاغ فوراً لجهة الدعم الفني.")
            try: await interaction.user.send("❌ أفاد المقرض بأنه لم يستلم الكريدات. إذا واجهت مشكلة يرجى التوجه لمركز الدعم المالي.")
            except: pass

    try: await الشخص.send(f"🔔 يدّعي {interaction.user.mention} أنه قام بسداد كامل الدين المستحق لك، هل تؤكد استلام الكريدات؟", view=PayView())
    except: pass

# ─── 5. أوامر الرتب والإدارة والرقابة ───
@bot.tree.command(name="الغاء_العامليه", description="إيقاف معاملة سلف جارية بشكل إجباري وقسري وطارئ من الإدارة.")
async def forced_cancel(interaction: discord.Interaction, اسم_الشخص: discord.User):
    if not await check_admin_permission(interaction):
        await interaction.response.send_message("❌ عذراً، أنت لا تملك رتب الإدارة في سيرفر الدعم المخولة لاستخدام هذا النظام.", ephemeral=True)
        return

    db = load_db()
    target_id = str(اسم_الشخص.id)
    found = False
    for lid, ldata in list(db["loans"].items()):
        if str(ldata["borrower_id"]) == target_id or str(ldata["lender_id"]) == target_id:
            borrower = bot.get_user(ldata["borrower_id"]) or await bot.fetch_user(ldata["borrower_id"])
            lender = bot.get_user(ldata["lender_id"]) or await bot.fetch_user(ldata["lender_id"])
            del db["loans"][lid]
            found = True
            
            try: await borrower.send(f"⚠️ نود إشعاركم بأنه تم إيقاف السلف المالي القائم بينكما بشكل كامل وإجباري بواسطة الإدارة العليا.")
            except: pass
            try: await lender.send(f"⚠️ نود إشعاركم بأنه تم إيقاف السلف المالي القائم بينكما بشكل كامل وإجباري بواسطة الإدارة العليا.")
            except: pass

    if found:
        save_db(db)
        await interaction.response.send_message(f"🚨 تم التدخل الإداري بنجاح وإيقاف السلف المتعلق بالعضو {اسم_الشخص.name} بالكامل.")
    else:
        await interaction.response.send_message("❌ لم يتم العثور على أي سلفيات جارية مسجلة تحت اسم هذا الحساب.", ephemeral=True)

@bot.tree.command(name="اشتكشاف", description="الاستعلام الفوري عن حالة حساب وتصنيفه بالسيرفر (طبيعي / محروم).")
async def check_user(interaction: discord.Interaction, اسم_الشخص: discord.User):
    if not await check_admin_permission(interaction):
        await interaction.response.send_message("❌ عذراً، هذا الأمر مخصص للإدارة والدعم الفني فقط.", ephemeral=True)
        return
    db = load_db()
    status = get_user_status(اسم_الشخص.id, db)
    await interaction.response.send_message(f"🔍 **تقرير الاستكشاف المالي:**\n👤 الحساب: {اسم_الشخص.mention}\n📊 التصنيف الحالي: **{status}**")

@bot.tree.command(name="محروم", description="إدراج حساب يدوياً بقائمة الحرمان وحظر تعاملاته الماليّة.")
async def set_blacklist(interaction: discord.Interaction, اسم_الشخص: discord.User):
    if not await check_admin_permission(interaction):
        await interaction.response.send_message("❌ هذا الأمر مخصص للإدارة والدعم الفني فقط.", ephemeral=True)
        return
    db = load_db()
    if str(اسم_الشخص.id) not in db["users"]: db["users"][str(اسم_الشخص.id)] = {}
    db["users"][str(اسم_الشخص.id)]["status"] = "محروم"
    save_db(db)
    await interaction.response.send_message(f"⛔ تم حظر وتغيير حالة {اسم_الشخص.mention} إلى **محروم من التسلوف** بنجاح.")

@bot.tree.command(name="الغاء_محروم", description="فك الحظر المالي عن حساب وإعادته إلى تصنيف الحساب الطبيعي.")
async def remove_blacklist(interaction: discord.Interaction, اسم_الشخص: discord.User):
    if not await check_admin_permission(interaction):
        await interaction.response.send_message("❌ هذا الأمر مخصص للإدارة والدعم الفني فقط.", ephemeral=True)
        return
    db = load_db()
    if str(اسم_الشخص.id) in db["users"]:
        db["users"][str(اسم_الشخص.id)]["status"] = "طبيعي"
        save_db(db)
    await interaction.response.send_message(f"🟢 تم إلغاء حرمان {اسم_الشخص.mention} بنجاح وإعادته إلى التصنيف الطبيعي.")
    try: await اسم_الشخص.send("🟢 أهلاً بك، لقد تم رفع الحرمان المالي عن حسابك مجدداً من قبل الإدارة، يرجى عدم تكرار المشاكل السابقة منعاً للعقوبات.")
    except: pass

# ─── 6. فحص الأقساط التلقائي (30 يوم) ───
@tasks.loop(hours=1)
async def clean_expired_loans():
    await bot.wait_until_ready()
    db = load_db()
    now = datetime.utcnow()
    changed = False

    for lid, ldata in list(db["loans"].items()):
        expire_dt = datetime.strptime(ldata["expire_at"], "%Y-%m-%d %H:%M:%S")
        if now > expire_dt:
            borrower_id = str(ldata["borrower_id"])
            if borrower_id not in db["users"]: db["users"][borrower_id] = {}
            db["users"][borrower_id]["status"] = "محروم"
            del db["loans"][lid]
            changed = True

            log_chan = bot.get_channel(LOG_ROOM_EXPIRED)
            if log_chan:
                await log_chan.send(
                    f"🚨🚨 **إشعار منشن للإدارة العليا** <@&{ADMIN_ROLE_ID}>\n"
                    f"⚠️ تخلف شخص عن دفع السلف في موعده المحدد (30 يوماً)!\n"
                    f"👤 **المستلف المتهرب:** <@{borrower_id}> (ID: `{borrower_id}`)\n"
                    f"💰 **المبلغ المترتب عليه:** {ldata['amount']:,} كريدت\n"
                    f"🔗 **رابط التحقق:** الحساب تلقى عقوبة **محروم** وتجميد فوري في السيرفر."
                )
    if changed: save_db(db)

bot.run("9957")
