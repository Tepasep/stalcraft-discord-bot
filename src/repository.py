import aiohttp
import time
from typing import Optional, Dict, Any
import urllib.parse

from . import config

# Кэш для Application Token
_token_cache: Dict[str, Any] = {
    "access_token": None,
    "expires_at": 0
}

# Кэш для данных игроков
_player_cache: Dict[str, Dict[str, Any]] = {}


async def _get_app_token() -> str:
    """Получает Application Token через client_credentials"""
    now = time.time()
    
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]
    
    data = {
        "grant_type": "client_credentials",
        "client_id": config.STALCRAFT_CLIENT_ID,
        "client_secret": config.STALCRAFT_CLIENT_SECRET
    }
    
    # Правильный OAuth URL
    auth_url = "https://exbo.net/oauth/token"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, data=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    _token_cache["access_token"] = token_data["access_token"]
                    _token_cache["expires_at"] = now + token_data.get("expires_in", 3600) - 60
                    print("✅ [AUTH] Application Token получен")
                    return _token_cache["access_token"]
                else:
                    err_text = await resp.text()
                    print(f"❌ [AUTH] Ошибка {resp.status}: {err_text[:200]}")
                    raise RuntimeError(f"Не удалось получить токен: {resp.status}")
    except Exception as e:
        print(f"❌ [AUTH] Ошибка соединения: {e}")
        raise


async def fetch_from_api(endpoint_path: str, use_token: bool = True) -> Optional[Dict]:
    """Делает GET запрос к API"""
    
    if use_token:
        token = await _get_app_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "StalcraftStatsBot/1.0"
        }
    else:
        # Для публичных endpoint'ов без авторизации
        headers = {
            "Accept": "application/json",
            "User-Agent": "StalcraftStatsBot/1.0"
        }
    
    url = f"{config.API_BASE_URL}/{config.STALCRAFT_REGION}/{endpoint_path}"

    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    print("⚠️ [DEBUG] 401: Токен недействителен")
                    _token_cache["expires_at"] = 0
                    return None
                elif response.status == 404:
                    print(f"❌ [DEBUG] 404: Ресурс не найден")
                    return None
                else:
                    text = await response.text()
                    print(f"⚠️ [DEBUG] Ошибка {response.status}: {text[:200]}")
                    return None
    except Exception as e:
        print(f"❌ [DEBUG] Сетевая ошибка: {e}")
        return None


def get_cached(key: str) -> Optional[Dict]:
    if key in _player_cache:
        entry = _player_cache[key]
        if time.time() < entry["expires"]:
            return entry["data"]
        else:
            del _player_cache[key]
    return None


def set_cache(key: str,  data:Dict):
    _player_cache[key] = {
        "data": data,
        "expires": time.time() + config.CACHE_TTL
    }


async def get_player_stats(nickname: str) -> Optional[Dict]:
    """Получает статистику игрока через Character Profile endpoint"""
    cache_key = f"player:{config.STALCRAFT_REGION}:{nickname.lower()}"
    
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    # URL-кодируем никнейм
    safe_nick = urllib.parse.quote(nickname, safe="")
    
    # Правильный endpoint из документации
    endpoint = f"character/by-name/{safe_nick}/profile"
    
    print(f"🔍 Запрос профиля игрока: {nickname}")
    player_data = await fetch_from_api(endpoint, use_token=True)
    
    if player_data is not None:
        print(f"✅ Профиль получен")
        set_cache(cache_key, player_data)
        
    return player_data
async def get_emission_data(region: str = None) -> Optional[Dict]:
    """Получает данные о выбросах"""
    from . import config
    reg = region or config.STALCRAFT_REGION
    
    endpoint = "emission"
    data = await fetch_from_api(endpoint, use_token=True)
    
    if data and isinstance(data, dict):
        return data
    return None