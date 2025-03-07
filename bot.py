import logging
import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# تنظیمات توکن و API Key
TOKEN = "7653169627:AAGQWygfb1ADM-QmlpFkZIv9wPnHZ1AApzE"
SPEECHMATICS_API_KEY = "gnvvKVKKycDpWpxLHsu7Pl5kMrzY184z"

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

        # آپلود به Speechmatics
        upload_url = "https://asr.api.speechmatics.com/v2/jobs"
        headers = {"Authorization": f"Bearer {SPEECHMATICS_API_KEY}"}
        files = {"data_file": open(local_file, 'rb')}
        params = {"config": '{"type": "transcription", "transcription_config": {"language": "fa"}}'}

        response = requests.post(upload_url, headers=headers, files=files, data=params)
        files["data_file"].close()

        if response.status_code == 200:
            job_id = response.json()["id"]
            await message.reply("📤 فایل با موفقیت آپلود شد! در حال تبدیل...")

            progress = 0
            while progress < 100:
                status_response = requests.get(f"https://asr.api.speechmatics.com/v2/jobs/{job_id}", headers=headers)
                status_data = status_response.json()
                progress = status_data.get("progress", 0)

                await message.reply(f"⏳ در حال پردازش... {progress}% تکمیل شده است.")
                await asyncio.sleep(5)

            if status_data.get("status") == "done":
                result_url = status_data["results_url"]
                transcript_response = requests.get(result_url, headers=headers)
                transcript_text = transcript_response.json()["results"][0]["alternatives"][0]["transcript"]

                await message.reply(f"📝 متن استخراج‌شده:\n\n{transcript_text}")
                await message.reply("✅ امیدوارم از تبدیل رضایت کامل داشته باشی.\n"
                                    "این ربات توسط **Rez1Ren0** طراحی شده است.\n"
                                    "اگر مشکلی داشتی، به او اطلاع بده تا کمکت کنه! 🚀")
            else:
                await message.reply("❌ مشکلی در پردازش فایل به وجود آمد.")
        else:
            await message.reply(f"❌ خطا در آپلود: {response.status_code} - {response.text}")

    except Exception as e:
        await message.reply(f"⚠ خطایی رخ داد: {str(e)}")
    finally:
        # حذف فایل برای جلوگیری از پر شدن حافظه سرور
        if os.path.exists(local_file):
            os.remove(local_file)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
