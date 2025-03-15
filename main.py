from pyrogram import Client, filters
from test import server 

from pyrogram.types import Message
from pyrogram.errors import (
    UserIsBlocked, 
    PeerIdInvalid, 
    UserDeactivatedBan,
    ChatWriteForbidden
)
import aiohttp
import json

# تهيئة البوت الرئيسي (القرآن)
app = Client(
    "QuranBot",
    api_id="12812035",
    api_hash="b7f9c6c7802fbc7ef756daaa22b1c114",
    bot_token="7536360793:AAHMw8eBeefIS8xRBHywaZANJaVuhzYM8_I"
)

# تهيئة بوت الإذاعة
broadcast_bot = Client(
    "BroadcastBot",
    api_id="12812035",
    api_hash="b7f9c6c7802fbc7ef756daaa22b1c114",
    bot_token="5788618886:AAGzMidHKE48f4QlRuNBdPinMaFvIqH-gqY"
)

# معرف المالك
OWNER_ID = 1558155028

# رابط API لمعرفات المستخدمين
USERS_API_URL = "http://mysqlfortelegrambotquran.pythonanywhere.com/send_broad"

async def get_users_from_api():
    """جلب معرفات المستخدمين من API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(USERS_API_URL) as response:
                users_data = await response.json()
                return [int(user_id) for user_id in users_data]
    except Exception as e:
        print(f"خطأ في جلب معرفات المستخدمين من API: {str(e)}")
        return []

# دالة للتحقق من المالك
def is_owner(func):
    async def wrapper(client, message):
        if message.from_user.id != OWNER_ID:
            await message.reply_text("⚠️ عذراً، هذا الأمر متاح فقط للمالك.")
            return
        return await func(client, message)
    return wrapper

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """رسالة البداية"""
    if message.from_user.id == OWNER_ID:
        await message.reply_text(
            "مرحباً بك في بوت الإذاعة! 📢\n\n"
            "الأوامر المتاحة:\n"
            "• /broadcast - الرد على أي رسالة للإذاعة\n"
            "• /stats - عرض إحصائيات البوت\n\n"
            "يمكنك إرسال:\n"
            "- نصوص\n"
            "- صور\n"
            "- فيديوهات\n"
            "- ملفات صوتية\n"
            "- ملفات\n"
            "- الملصقات\n"
            "ثم الرد عليها بـ /broadcast للإذاعة"
        )
    else:
        await message.reply_text("مرحباً! هذا بوت مخصص للإذاعة فقط. 🔒")

@app.on_message(filters.command("broadcast") & filters.reply)
@is_owner
async def broadcast_command(client, message: Message):
    """أمر الإذاعة - متاح فقط للمالك"""
    replied_message = message.reply_to_message
    
    # جلب قائمة المستخدمين من API
    users_list = await get_users_from_api()
    
    if not users_list:
        await message.reply_text("⚠️ لم يتم العثور على مستخدمين في قاعدة البيانات")
        return

    success_count = 0
    fail_count = 0
    blocked_users = []
    deleted_users = []
    
    # إرسال رسالة لإظهار بدء الإذاعة
    status_msg = await message.reply_text("جارِ إرسال الإذاعة... ⏳")

    # بدء البوت وإرسال الرسائل
    async with broadcast_bot:
        for user_id in users_list:
            try:
                if replied_message.text:
                    await broadcast_bot.send_message(user_id, replied_message.text)
                elif replied_message.photo:
                    await broadcast_bot.send_photo(
                        user_id,
                        replied_message.photo.file_id,
                        caption=replied_message.caption
                    )
                elif replied_message.video:
                    await broadcast_bot.send_video(
                        user_id,
                        replied_message.video.file_id,
                        caption=replied_message.caption
                    )
                elif replied_message.audio:
                    await broadcast_bot.send_audio(
                        user_id,
                        replied_message.audio.file_id,
                        caption=replied_message.caption
                    )
                elif replied_message.document:
                    await broadcast_bot.send_document(
                        user_id,
                        replied_message.document.file_id,
                        caption=replied_message.caption
                    )
                elif replied_message.sticker:
                    await broadcast_bot.send_sticker(
                        user_id,
                        replied_message.sticker.file_id
                    )
                elif replied_message.voice:
                    await broadcast_bot.send_voice(
                        user_id,
                        replied_message.voice.file_id,
                        caption=replied_message.caption
                    )
                elif replied_message.video_note:
                    await broadcast_bot.send_video_note(
                        user_id,
                        replied_message.video_note.file_id
                    )
                
                success_count += 1
            except UserIsBlocked:
                blocked_users.append(user_id)
                fail_count += 1
            except (PeerIdInvalid, UserDeactivatedBan):
                deleted_users.append(user_id)
                fail_count += 1
            except Exception as e:
                fail_count += 1
                print(f"فشل إرسال الإذاعة للمستخدم {user_id}: {str(e)}")
            
            # تحديث حالة الإرسال كل 20 مستخدم
            if (success_count + fail_count) % 20 == 0:
                await status_msg.edit_text(
                    f"جارِ إرسال الإذاعة...\n"
                    f"✅ نجح: {success_count}\n"
                    f"❌ فشل: {fail_count}\n"
                    f"🚫 حظر: {len(blocked_users)}\n"
                    f"❌ محذوف: {len(deleted_users)}"
                )
    
    # تحضير تقرير المستخدمين المحظورين والمحذوفين
    blocked_report = ""
    if blocked_users:
        blocked_report = "\n\n🚫 المستخدمين الذين حظروا البوت:\n"
        for user_id in blocked_users:
            blocked_report += f"• `{user_id}`\n"
    
    deleted_report = ""
    if deleted_users:
        deleted_report = "\n\n❌ الحسابات المحذوفة:\n"
        for user_id in deleted_users:
            deleted_report += f"• `{user_id}`\n"
    
    # إرسال التقرير النهائي
    await status_msg.edit_text(
        f"📊 **تقرير الإذاعة**\n\n"
        f"✅ تم الإرسال بنجاح: {success_count}\n"
        f"❌ فشل الإرسال: {fail_count}\n"
        f"🚫 عدد من حظر البوت: {len(blocked_users)}\n"
        f"❌ عدد الحسابات المحذوفة: {len(deleted_users)}\n"
        f"📝 إجمالي المستخدمين: {len(users_list)}"
        f"{blocked_report}"
        f"{deleted_report}"
    )

@app.on_message(filters.command("stats"))
@is_owner
async def stats_command(client, message):
    """إحصائيات البوت"""
    users_list = await get_users_from_api()
    await message.reply_text(
        f"📊 **إحصائيات البوت**\n\n"
        f"👥 عدد المستخدمين: {len(users_list)}"
    )

# تشغيل البوت
server()

print("Broadcast Bot is running...")
app.run()
