const { Client, GatewayIntentBits, EmbedBuilder } = require('discord.js');
const http = require('http');

const bot = new Client({ 
    intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.GuildMessages, 
        GatewayIntentBits.MessageContent
    ] 
});

// ضع هنا الـ IDs الجديدة للقنوات الموجودة عندك حالياً
const CHANNEL_SOURCE = "ضع_ID_الروم_هنا";
const CHANNEL_DEST = "ضع_ID_الروم_هنا";
const CHANNEL_NEWS = "ضع_ID_الروم_هنا";
const KEEP_ALIVE_CHANNEL = "ضع_ID_الروم_هنا";
const ROLE_EVERYONE = "ضع_ID_رتبة_الافريوان_هنا";

let live_mode = false;

function parse_time(time_str) {
    const units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1};
    const match = time_str.toLowerCase().match(/(\d+)([dhms])/);
    if (match) return parseInt(match[1]) * units[match[2]];
    return 0;
}

http.createServer((req, res) => {
    res.write("البوت يعمل!");
    res.end();
}).listen(process.env.PORT || 8080);

setInterval(async () => {
    try {
        const channel = await bot.channels.fetch(KEEP_ALIVE_CHANNEL);
        if (channel) {
            const msg = await channel.send("تم، أنا أعمل..");
            setTimeout(() => msg.delete().catch(() => {}), 4000);
        }
    } catch (e) { console.log("خطأ في قناة البقاء نشطاً"); }
}, 300000); // تم تعديل الوقت لـ 5 دقائق لتجنب الضغط

bot.once('ready', () => {
    console.log(`البوت يعمل كـ ${bot.user.tag}`);
});

bot.on('messageCreate', async (message) => {
    if (message.author.bot) return;

    if (message.content.startsWith('!رتب')) {
        if (message.channel.id !== CHANNEL_SOURCE) return;
        const role1 = message.mentions.roles.first();
        const role2 = message.mentions.roles.at(1);
        if(!role1 || !role2) return message.reply("يجب منشن رتبتين!");

        await message.channel.send(`تم اختيار ${role1.name} ضد ${role2.name}. اكتب الوقت (مثال: 1h أو 30m):`);
        const filter = m => m.author.id === message.author.id;
        const collected = await message.channel.awaitMessages({ filter, max: 1 });
        let total_seconds = parse_time(collected.first().content);
        
        if (total_seconds <= 0) return message.channel.send("صيغة الوقت غير صحيحة.");

        const embed = new EmbedBuilder().setTitle("⚽ مباراة جديدة").setColor(0x0000FF)
            .addFields({ name: "المواجهة", value: `${role1} VS ${role2}`, inline: false });
        
        const target_channel = await bot.channels.fetch(CHANNEL_DEST);
        const timer_msg = await target_channel.send({ content: `<@&${ROLE_EVERYONE}>`, embeds: [embed] });
        
        while (total_seconds >= 0) {
            let h = Math.floor(total_seconds / 3600);
            let m = Math.floor((total_seconds % 3600) / 60);
            let s = total_seconds % 60;
            embed.setFields({ name: "المواجهة", value: `${role1} VS ${role2}\n⏰ الموعد: ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`, inline: false });
            await timer_msg.edit({ embeds: [embed] });
            await new Promise(r => setTimeout(r, 1000));
            total_seconds -= 1;
        }
        await timer_msg.edit({ content: "⚽ المباراة بدأت الآن!", embeds: [embed] });
    }

    if (message.content.startsWith('!صار')) {
        const role1 = message.mentions.roles.first();
        const role2 = message.mentions.roles.at(1);
        await message.channel.send("اكتب النتيجة:");
        const collected = await message.channel.awaitMessages({ filter: m => m.author.id === message.author.id, max: 1 });
        const embed = new EmbedBuilder().setTitle("⚽ نتيجة المباراة").setColor(0xFFD700)
            .addFields({ name: "المواجهة", value: `${role1} VS ${role2}`, inline: false }, { name: "النتيجة", value: `**${collected.first().content}**`, inline: false });
        (await bot.channels.fetch(CHANNEL_DEST)).send({ embeds: [embed] });
    }

    if (message.content.startsWith('!خبر')) {
        const content = message.content.replace('!خبر', '').trim();
        (await bot.channels.fetch(CHANNEL_NEWS)).send({ content: `<@&${ROLE_EVERYONE}>`, embeds: [new EmbedBuilder().setTitle("📢 خبر عاجل").setDescription(content).setColor(0xFF0000)] });
    }

    if (message.content === '!اخبار') live_mode = true;
    if (message.content === '!الغاء') live_mode = false;
    if (live_mode && message.channel.id === CHANNEL_SOURCE && !message.content.startsWith('!')) {
        (await bot.channels.fetch(CHANNEL_DEST)).send({ embeds: [new EmbedBuilder().setDescription(message.content).setColor(0x00FF00)] });
    }
});

bot.login(process.env.DISCORD_TOKEN);
