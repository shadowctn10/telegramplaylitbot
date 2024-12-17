import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from pydub import AudioSegment

# --- متغیرهای مهم ---
TOKEN = "7830811506:AAHyRQAEQkgntjl66aWb2bG9pdvqLoaqLc0"  # توکن ربات تلگرام
GENIUS_API_TOKEN = "1k3ljpOFJhSQs52wnj8MaAnfFqVfLGOzBXUhBakw7aD1SAvQsVqih4RK8ds8CLNx"  # توکن API سایت Genius
DEMO_DURATION_MS = 60000  # مدت زمان دمو (1 دقیقه)

# تنظیم مسیر FFmpeg و ffprobe
AudioSegment.converter = "/usr/bin/ffmpeg"
AudioSegment.ffprobe = "/usr/bin/ffprobe"
# --- تابع برای دریافت لیریک ---
def get_lyrics(song_name: str) -> str:
    headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    search_url = "https://api.genius.com/search"
    params = {"q": song_name}

    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code == 200:
        hits = response.json()["response"]["hits"]
        if hits:
            song_url = hits[0]["result"]["url"]
            return f"📃 متن آهنگ را می‌توانید در لینک زیر مشاهده کنید:\n{song_url}"
        else:
            return "متأسفم! متن آهنگ پیدا نشد. 😔"
    else:
        return "خطا در ارتباط با سرور لیریک!"

# --- تابع برای پردازش و ایجاد دمو ---
async def process_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.audio:
        file = update.message.audio
        file_id = file.file_id
        audio_name = file.file_name if hasattr(file, "file_name") else "Demo"

        # دانلود فایل صوتی
        new_file = await context.bot.get_file(file_id)
        file_path = "input_audio.ogg"
        await new_file.download_to_drive(file_path)

        try:
            # ایجاد دمو از فایل صوتی
            audio = AudioSegment.from_file(file_path)
            demo_audio = audio[:DEMO_DURATION_MS]
            demo_audio.export("demo_audio.ogg", format="ogg")

            # ارسال دمو همراه با دکمه Lyrics
            keyboard = [[InlineKeyboardButton("🎶 Lyrics", callback_data=f"lyrics:{audio_name}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            with open("demo_audio.ogg", "rb") as voice_file:
                await context.bot.send_voice(
                    chat_id=update.effective_chat.id,
                    voice=voice_file,
                    caption=audio_name,
                    reply_to_message_id=update.message.message_id,
                    reply_markup=reply_markup
                )

            # حذف فایل‌های موقت
            os.remove("input_audio.ogg")
            os.remove("demo_audio.ogg")
        except Exception as e:
            await update.message.reply_text(f"خطا در پردازش فایل صوتی: {str(e)}")
    else:
        await update.message.reply_text("لطفاً یک فایل صوتی ارسال کنید!")

# --- هندلر برای دکمه Lyrics ---
async def lyrics_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # استخراج نام آهنگ از callback_data
    song_name = query.data.split(":")[1]
    lyrics = get_lyrics(song_name)

    # ارسال لیریک به پیوی کاربر
    user_id = query.from_user.id  # شناسه کاربر
    await context.bot.send_message(chat_id=user_id, text=lyrics)
    await query.message.reply_text("🎶 متن آهنگ به پیوی شما ارسال شد!")

# --- تابع شروع ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! آهنگ خود را ارسال کنید تا دمو و متن لیریک آن را دریافت کنید. 🎵")

# --- تابع اصلی برای اجرای ربات ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO, process_audio))
    app.add_handler(CallbackQueryHandler(lyrics_button, pattern="^lyrics:"))

    print("ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
