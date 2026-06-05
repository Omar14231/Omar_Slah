const { Client, GatewayIntentBits, EmbedBuilder, ActivityType } = require('discord.js');
const http = require('http');

// إعدادات الـ Intents
const bot = new Client({ 
    intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.GuildMessages, 
        GatewayIntentBits.MessageContent
    ] 
});

// الثوابت (IDs)
const CHANNEL_SOURCE = "1511089965424054292";
const CHANNEL_DEST = "1508470750456315974";
const CHANNEL_NEWS = "1506417724010528928";
const KEEP_ALIVE_CHANNEL = "1511851709704704020";
const ROLE_EVERYONE = "1478799212312531089";

let live_mode = false;

// دالة تحويل الوقت
function parse_time(time_str) {
    const units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1};
    const match = time_str.toLowerCase().match(/(\d+)([dhms])/);
    if (match) {
        return parseInt(match[1]) * units[match[2]];
    }
    return 0;
}

// سيرفر وهمي لإرضاء رندر
http.createServer((req, res) => {
    res.write("البوت يعمل!");
    res.end();
}).listen(process.env.PORT || 8080);

// نظام البقاء نشطاً (إرسال وحذف)
setInterval(async () => {
    const channel = await bot.channels.fetch(KEEP_ALIVE_CHANNEL);
    if (channel) {
        const msg = await channel.send("تم، أنا أعمل..");
        setTimeout(() => msg.delete(), 4000);
    }
}, 5000);

bot.once('ready', () => {
    console.log(`البوت يعمل كـ ${bot.user.tag}`);
});

// الأوامر
bot.on('messageCreate', async (message) => {
    if (message.author.bot) return;

    // 1. أمر !رتب
    if (message.content.startsWith('!رتب')) {
        const args = message.content.split(' ');
        if (message.channel.id !== CHANNEL_SOURCE) return;
        
        const role1 = message.mentions.roles.first();
        const role2 = message.mentions.roles.at(1);

        await message.channel.send(`تم اختيار ${role1.name} ضد ${role2.name}. اكتب الوقت (مثال: 1h أو 30m):`);
        
        const filter = m => m.author.id === message.author.id;
        const collected = await message.channel.awaitMessages({ filter, max: 1 });
        const timeMsg = collected.first();
        let total_seconds = parse_time(timeMsg.content);
        
        if (total_seconds <= 0) {
            await message.channel.send("صيغة الوقت غير صحيحة.");
            return;
        }

        const embed = new EmbedBuilder().setTitle("⚽ مباراة جديدة").setColor(0x0000FF)
            .addFields({ name: "المواجهة", value: `${role1} VS ${role2}`, inline: false });
        
        const target_channel = await bot.channels.fetch(CHANNEL_DEST);
        const timer_msg = await target_channel.send({ content: `<@&${ROLE_EVERYONE}>`, embeds: [embed] });
        
        while (total_seconds >= 0) {
            let hours = Math.floor(total_seconds / 3600);
            let minutes = Math.floor((total_seconds % 3600) / 60);
            let seconds = total_seconds % 60;
            let time_format = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            
            embed.setFields({ name: "المواجهة", value: `${role1} VS ${role2}\n⏰ الموعد: ${time_format}`, inline: false });
            await timer_msg.edit({ embeds: [embed] });
            
            await new Promise(r => setTimeout(r, 1000));
            total_seconds -= 1;
        }
        await timer_msg.edit({ content: "⚽ المباراة بدأت الآن!", embeds: [embed] });
    }

    // 2. أمر !صار
    if (message.content.startsWith('!صار')) {
        const role1 = message.mentions.roles.first();
        const role2 = message.mentions.roles.at(1);
        await message.channel.send("اكتب النتيجة (مثال: 1-0):");
        const collected = await message.channel.awaitMessages({ filter: m => m.author.id === message.author.id, max: 1 });
        const resMsg = collected.first().content;
        const embed = new EmbedBuilder().setTitle("⚽ نتيجة المباراة").setColor(0xFFD700)
            .addFields({ name: "المواجهة", value: `${role1} VS ${role2}`, inline: false }, { name: "النتيجة", value: `**${resMsg}**`, inline: false });
        const target_channel = await bot.channels.fetch(CHANNEL_DEST);
        await target_channel.send({ embeds: [embed] });
    }

    // 3. أمر !خبر
    if (message.content.startsWith('!خبر')) {
        const content = message.content.replace('!خبر', '').trim();
        const target_channel = await bot.channels.fetch(CHANNEL_NEWS);
        const embed = new EmbedBuilder().setTitle("📢 خبر عاجل").setDescription(content).setColor(0xFF0000);
        await target_channel.send({ content: `<@&${ROLE_EVERYONE}>`, embeds: [embed] });
        await message.channel.send("تم نشر الخبر.");
    }

    // 4. أوامر البث
    if (message.content === '!اخبار') { live_mode = true; await message.channel.send("تم تفعيل وضع البث الحي."); }
    if (message.content === '!الغاء') { live_mode = false; await message.channel.send("تم إيقاف وضع البث الحي."); }

    if (live_mode && message.channel.id === CHANNEL_SOURCE && !message.content.startsWith('!')) {
        const target_channel = await bot.channels.fetch(CHANNEL_DEST);
        const embed = new EmbedBuilder().setDescription(message.content).setColor(0x00FF00);
        await target_channel.send({ embeds: [embed] });
    }
});

bot.login(process.env.DISCORD_TOKEN);
