import os

# Telegram Bot Token
BOT_TOKEN = "8763708640:AAFJetvPY2XLDTKW2VW_KdkL_vAtcnAzSe8"

# Admin Telegram IDs (put your Telegram user ID here to access /stats and /broadcast)
ADMIN_IDS = []

# Monetization & Channels
# Set to True and specify CHANNEL_ID / CHANNEL_URL if you want to require users to subscribe before downloading
FORCE_SUB_REQUIRED = False
REQUIRED_CHANNEL_ID = ""  # Example: "@my_channel" or "-100123456789"
REQUIRED_CHANNEL_URL = "" # Example: "https://t.me/my_channel"

# Free daily download limit (0 for unlimited)
DAILY_FREE_LIMIT = 0

# Ad caption attached to downloaded files
AD_CAPTION_FOOTER = "\n\n⚡ <i>Скачано через @TubeShortsBot</i>"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DOWNLOADS_DIR = os.path.join(BASE_DIR, "temp_downloads")
DB_PATH = os.path.join(BASE_DIR, "bot_database.db")

os.makedirs(TEMP_DOWNLOADS_DIR, exist_ok=True)
