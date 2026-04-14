import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN не найден в .env")

# Stalcraft API
STALCRAFT_CLIENT_ID = os.getenv("STALCRAFT_CLIENT_ID")
STALCRAFT_CLIENT_SECRET = os.getenv("STALCRAFT_CLIENT_SECRET")
STALCRAFT_REGION = os.getenv("STALCRAFT_REGION", "EU")
API_BASE_URL = os.getenv("STALCRAFT_API_BASE", "https://eapi.stalcraft.net")

# Настройки бота
CACHE_TTL = 300  