import logging
import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# دریافت توکن‌ها از متغیرهای محیطی
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # نام متغیر صحیح
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# بررسی اینکه توکن‌ها مقدار دارند یا نه
if not TOKEN:
    raise ValueError("🚨 خطا: `TELEGRAM_BOT_TOKEN` مقدار ندارد! لطفاً متغیر محیطی را تنظیم کنید.")
if not OPENAI_API_KEY:
    raise ValueError("🚨 خطا: `OPENAI_API_KEY` مقدار ندارد! لطفاً متغیر محیطی را تنظیم کنید.")

# مقداردهی اولیه ربات
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("سلام! 🎤 به بات تبدیل صوت به متن خوش آمدید.\n"
                        "لطفا فایل صوتی خود را ارسال کنید.")

@dp.message_handler(content_types=[types.ContentType.AUDIO, types.ContentType.VOICE])
async def handle_audio(message: types.Message):
    try:
        file_id = message.audio.file_id if message.audio else message.voice.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

        await message.reply("✅ فایل دریافت شد! در حال پردازش...")

        local_file = f"temp_{file_id}.ogg"

        # دانلود فایل صوتی
        with open(local_file, 'wb') as f:
            f.write(requests.get(file_url).content)

        # ارسال به Whisper API (OpenAI)
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        files = {
            "file": open(local_file, "rb")
        }
        data = {
            "model": "whisper-1",
            "language": "fa"  # 🔹 زبان فارسی
        }

        response = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data)
        files["file"].close()

        if response.status_code == 200:
            transcript_text = response.json().get("text", "متنی یافت نشد.")
            await message.reply(f"📝 متن استخراج‌شده:\n\n{transcript_text}")
            await message.reply("✅ امیدوارم از تبدیل رضایت کامل داشته باشی.\n"
                                "این ربات توسط **Rez1Ren0** طراحی شده است.\n"
                                "اگر مشکلی داشتی، به او اطلاع بده تا کمکت کنه! 🚀")
        else:
            await message.reply(f"❌ خطا در پردازش: {response.status_code} - {response.text}")

    except Exception as e:
        await message.reply(f"⚠ خطایی رخ داد: {str(e)}")
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)

if __name__ == "__main__":
    logging.info("🚀 Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
