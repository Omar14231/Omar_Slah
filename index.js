const { Client, GatewayIntentBits, EmbedBuilder, ActivityType, REST, Routes } = require('discord.js');
const express = require('express');
const app = express();
const port = 3000;

// --- نظام 24/7 ---
app.get('/', (req, res) => res.send('البوت يعمل 24/7'));
app.listen(port, () => console.log(`الخادم يعمل على المنفذ ${port}`));

// --- إعدادات البوت ---
const TOKEN = process.env.TOKEN; // 
const APPLICATION_ID = '1461900883871662204'; // ضع آيدي البوت هنا

const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.GuildMessages, 
        GatewayIntentBits.MessageContent
    ] 
});

const CHANNEL_SOURCE = "1511089965424054292";
const CHANNEL_DEST = "1508470750456315974";
const CHANNEL_NEWS = "1506417724010528928";
const ROLE_EVERYONE = "1478799212312531089";
let live_mode = false;

function parseTime(timeStr) {
    const match = timeStr.match(/(\d+)([dhms])/);
    if (!match) return 0;
    const val = parseInt(match[1]);
    const unit = match[2];
    const units = { 'd': 86400, 'h': 3600, 'm': 60, 's': 1 };
    return val * (units[unit] || 0);
}

// --- أحداث البوت ---
client.once('ready', async () => {
    console.log(`✅ البوت جاهز ويعمل كـ ${client.user.tag}`);
    
    // تفعيل البث البنفسجي
    client.user.setActivity("كاس العالم 2026", { 
        type: ActivityType.Streaming,
        url: 'https://www.twitch.tv/adsqwertt11'
    });

    // تسجيل الأوامر (لضمان أنها تعمل)
    const rest = new REST({ version: '10' }).setToken(TOKEN);
    try {
        await rest.put(Routes.applicationCommands(APPLICATION_ID), { body: [{ name: 'ping', description: 'اختبار البوت' }] });
    } catch (e) { console.error(e); }
});

client.on('messageCreate', async message => {
    if (message.author.bot) return;

    // أوامر المباريات والأخبار (نفس كودك السابق)
    if (live_mode && message.channel.id === CHANNEL_SOURCE && !message.content.startsWith('!')) {
        const destChannel = client.channels.cache.get(CHANNEL_DEST);
        if (destChannel) {
            const embed = new EmbedBuilder().setDescription(message.content).setColor(0x00FF00);
            await destChannel.send({ embeds: [embed] });
        }
    }

    if (!message.content.startsWith('!')) return;
    const args = message.content.slice(1).split(/ +/);
    const command = args.shift().toLowerCase();

    if (command === 'رتب' && message.channel.id === CHANNEL_SOURCE) {
        const role1 = message.mentions.roles.at(0);
        const role2 = message.mentions.roles.at(1);
        if (!role1 || !role2) return message.reply("يجب منشن رتبتين!");
        await message.channel.send("اكتب الوقت (مثال: 1h):");
        const collected = await message.channel.awaitMessages({ filter: m => m.author.id === message.author.id, max: 1, time: 60000 });
        let totalSeconds = parseTime(collected.first()?.content || "");
        if (totalSeconds <= 0) return message.reply("صيغة الوقت غير صحيحة.");
        const embed = new EmbedBuilder().setTitle("⚽ مباراة جديدة").setColor(0x0000FF).addFields({ name: "المواجهة", value: `${role1} VS ${role2}` });
        const timerMsg = await client.channels.cache.get(CHANNEL_DEST).send({ content: `<@&${ROLE_EVERYONE}>`, embeds: [embed] });
        while (totalSeconds >= 0) {
            const h = Math.floor(totalSeconds / 3600);
            const m = Math.floor((totalSeconds % 3600) / 60);
            const s = totalSeconds % 60;
            embed.setFields({ name: "المواجهة", value: `${role1} VS ${role2}\n⏰ الموعد: ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}` });
            await timerMsg.edit({ embeds: [embed] }).catch(() => {});
            await new Promise(r => setTimeout(r, 1000));
            totalSeconds--;
        }
        await timerMsg.edit({ content: "⚽ المباراة بدأت الآن!", embeds: [embed] });
    }

    if (command === 'صار') {
        const role1 = message.mentions.roles.at(0);
        const role2 = message.mentions.roles.at(1);
        if (!role1 || !role2) return;
        await message.channel.send("اكتب النتيجة (مثال: 1-0):");
        const collected = await message.channel.awaitMessages({ filter: m => m.author.id === message.author.id, max: 1 });
        const embed = new EmbedBuilder().setTitle("⚽ نتيجة المباراة").setColor(0xFFD700).addFields({ name: "المواجهة", value: `${role1} VS ${role2}` }, { name: "النتيجة", value: collected.first().content });
        client.channels.cache.get(CHANNEL_DEST)?.send({ embeds: [embed] });
    }

    if (command === 'خبر') {
        const content = args.join(" ");
        const embed = new EmbedBuilder().setTitle("📢 خبر عاجل").setDescription(content).setColor(0xFF0000);
        client.channels.cache.get(CHANNEL_NEWS)?.send({ content: `<@&${ROLE_EVERYONE}>`, embeds: [embed] });
        message.reply("تم نشر الخبر.");
    }

    if (command === 'اخبار') { live_mode = true; message.reply("تم تفعيل وضع البث الحي."); }
    if (command === 'الغاء') { live_mode = false; message.reply("تم إيقاف وضع البث الحي."); }
});

client.login(TOKEN);
