import os
import sys
import re
import asyncio
import logging

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from aiogram.enums import ChatAction, ParseMode
from aiogram.client.default import DefaultBotProperties

import config
import database
import downloader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Memory store for active pending video links { url_hash: full_url }
pending_urls = {}

def get_url_hash(url: str) -> str:
    import hashlib
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:10]

# ----------------------------------------------------
# /start Handler
# ----------------------------------------------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = message.from_user
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    referrer_id = int(args.replace("ref", "")) if args and args.startswith("ref") and args.replace("ref", "").isdigit() else 0

    database.register_user(user.id, user.username, user.full_name, referrer_id)

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user.id}"

    welcome_text = (
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        "⚡ Я бот для <b>быстрого скачивания YouTube Shorts</b> и видео в любом качестве!\n\n"
        "📥 <b>Как мной пользоваться:</b>\n"
        "1. Скопируйте ссылку на любой <b>YouTube Shorts</b> или видео.\n"
        "2. Отправьте ссылку прямо сюда в чат.\n"
        "3. Выберите нужное качество (<b>1080p, 720p, 480p</b> или <b>MP3</b>) и получите готовый файл!\n\n"
        f"🎁 <b>Ваша реферальная ссылка:</b>\n<code>{ref_link}</code>\n"
        "<i>Делитесь с друзьями и пользуйтесь без ограничений!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Помощь и Инструкция", callback_data="help_menu")],
        [InlineKeyboardButton(text="⭐ Мой профиль / VIP", callback_data="profile_menu")]
    ])

    await message.answer(welcome_text, reply_markup=kb)

# ----------------------------------------------------
# /help & /stats Handlers
# ----------------------------------------------------
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📖 <b>Инструкция по скачиванию:</b>\n\n"
        "1️⃣ Откройте <b>YouTube</b> и скопируйте ссылку на Shorts или видео.\n"
        "2️⃣ Отправьте ссылку боту (например: <code>https://youtube.com/shorts/...</code>).\n"
        "3️⃣ Нажмите кнопку с нужным качеством видео.\n"
        "4️⃣ Бот скачает ролик и пришлет его прямо в чат!\n\n"
        "✨ <b>Поддерживаемые форматы:</b>\n"
        "• 🌟 <b>1080p Full HD</b> (максимальная четкость)\n"
        "• 📱 <b>720p HD</b> (стандарт)\n"
        "• ⚡ <b>480p SD</b> (быстро и мало весит)\n"
        "• 🎵 <b>MP3</b> (извлечение только музыки/звука)"
    )
    await message.answer(help_text)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    stats = database.get_stats()
    stats_text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"📥 Всего скачиваний: <b>{stats['total_downloads']}</b>\n"
        f"⚡ Скачано сегодня: <b>{stats['today_downloads']}</b>"
    )
    await message.answer(stats_text)

# ----------------------------------------------------
# URL Processing Handler
# ----------------------------------------------------
URL_REGEX = r'(https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be|tiktok\.com|instagram\.com)/\S+)'

@dp.message(F.text)
async def handle_incoming_link(message: types.Message):
    text = message.text.strip()
    match = re.search(URL_REGEX, text)
    
    if not match:
        await message.answer("⚠️ Пожалуйста, отправьте корректную ссылку на YouTube Shorts или видео.")
        return

    url = match.group(0)
    user = message.from_user
    database.register_user(user.id, user.username, user.full_name)

    # Status notification
    status_msg = await message.answer("🔍 <i>Получаю информацию о видео...</i>")

    try:
        info = await downloader.async_extract_info(url)
        url_hash = get_url_hash(url)
        pending_urls[url_hash] = url

        title = info['title']
        channel = info['uploader']
        duration = info['duration_str']
        views = f"{info['view_count']:,}".replace(',', ' ')
        is_short = "⚡ <b>YouTube Shorts</b>" if info['is_short'] else "🎬 <b>YouTube Video</b>"

        card_caption = (
            f"{is_short}\n"
            f"📌 <b>{title}</b>\n\n"
            f"👤 <b>Канал:</b> {channel}\n"
            f"⏱ <b>Длительность:</b> {duration}\n"
            f"👁 <b>Просмотров:</b> {views}\n\n"
            "👇 <b>Выберите качество для скачивания:</b>"
        )

        buttons = []
        row1 = []
        if info['has_1080']:
            row1.append(InlineKeyboardButton(text="🌟 1080p HD", callback_data=f"dl:1080:{url_hash}"))
        row1.append(InlineKeyboardButton(text="📱 720p HD", callback_data=f"dl:720:{url_hash}"))
        buttons.append(row1)

        row2 = [
            InlineKeyboardButton(text="⚡ 480p", callback_data=f"dl:480:{url_hash}"),
            InlineKeyboardButton(text="🎵 MP3 Звук", callback_data=f"dl:audio:{url_hash}")
        ]
        buttons.append(row2)
        buttons.append([InlineKeyboardButton(text="🌟 Максимальное (Best)", callback_data=f"dl:best:{url_hash}")])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await status_msg.delete()
        if info.get('thumbnail'):
            await message.answer_photo(photo=info['thumbnail'], caption=card_caption, reply_markup=kb)
        else:
            await message.answer(text=card_caption, reply_markup=kb)

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Ошибка:</b> Не удалось получить видео.\n<i>{str(e)[:150]}</i>")

# ----------------------------------------------------
# Quality Selection & Download Callback
# ----------------------------------------------------
@dp.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка запроса", show_alert=True)
        return

    quality = parts[1]
    url_hash = parts[2]
    url = pending_urls.get(url_hash)

    if not url:
        await callback.answer("Срок действия ссылки истек. Отправьте её заново.", show_alert=True)
        return

    quality_labels = {
        'best': '🌟 Максимальное',
        '1080': '🌟 1080p Full HD',
        '720': '📱 720p HD',
        '480': '⚡ 480p SD',
        'audio': '🎵 MP3 Аудио'
    }
    label = quality_labels.get(quality, quality)

    await callback.answer(f"Загружаю {label}...")
    status_msg = await callback.message.reply(f"⏳ <b>Скачиваю видео в качестве {label}...</b>\n<i>Пожалуйста, подождите несколько секунд</i>")

    try:
        # Show upload action in Telegram
        if quality == 'audio':
            await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VOICE)
        else:
            await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)

        result = await downloader.async_download_video(url, quality)
        filepath = result['filepath']
        size_mb = result['size_bytes'] / (1024 * 1024)

        if size_mb > 50:
            await status_msg.edit_text(
                f"⚠️ Файл слишком большой ({size_mb:.1f} MB) для отправки стандартным ботом Telegram (лимит 50 MB).\n"
                "💡 Попробуйте выбрать качество 720p или 480p."
            )
            downloader.cleanup_file(filepath)
            return

        await status_msg.edit_text("📤 <b>Отправляю файл в Telegram...</b>")
        video_input = FSInputFile(filepath)
        caption = f"🎬 <b>{result['title']}</b>\nКачество: <b>{label}</b>{config.AD_CAPTION_FOOTER}"

        if result['is_audio']:
            await callback.message.reply_audio(
                audio=video_input,
                title=result['title'],
                performer="YouTube",
                duration=result.get('duration', 0),
                caption=caption
            )
        else:
            await callback.message.reply_video(
                video=video_input,
                caption=caption,
                duration=result.get('duration', 0),
                width=result.get('width', 0),
                height=result.get('height', 0),
                supports_streaming=True
            )

        database.record_download(callback.from_user.id, result['title'], url, quality)
        await status_msg.delete()
        downloader.cleanup_file(filepath)

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Ошибка при скачивании:</b>\n<i>{str(e)[:150]}</i>")

# ----------------------------------------------------
# Menu Callbacks
# ----------------------------------------------------
@dp.callback_query(F.data == "help_menu")
async def cb_help(callback: CallbackQuery):
    await callback.answer()
    await callback.message.reply(
        "💡 <b>Как пользоваться ботом:</b>\n\n"
        "Просто отправьте ссылку на любой ролик Shorts или обычное видео прямо в этот чат!\n"
        "Бот сам предложит варианты качества для сохранения."
    )

@dp.callback_query(F.data == "profile_menu")
async def cb_profile(callback: CallbackQuery):
    await callback.answer()
    user = database.get_user(callback.from_user.id)
    downloads = user.get('downloads_count', 0) if user else 0
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{callback.from_user.id}"

    profile_text = (
        f"👤 <b>Ваш профиль:</b>\n\n"
        f"🆔 ID: <code>{callback.from_user.id}</code>\n"
        f"📥 Скачано видео: <b>{downloads}</b>\n"
        f"⭐ Статус: <b>Базовый (Безлимитный)</b>\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n<code>{ref_link}</code>"
    )
    await callback.message.reply(profile_text)

from aiohttp import web

async def handle_health(request):
    return web.Response(text="Telegram Bot is alive and running!")

async def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web health check server running on port {port}")

# ----------------------------------------------------
# Main Startup
# ----------------------------------------------------
async def main():
    database.init_db()
    if os.environ.get("PORT"):
        await start_health_server()
    bot_user = await bot.get_me()
    print("==================================================")
    print(f"🤖 Telegram Bot @{bot_user.username} успешно запущен!")
    print("==================================================")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
