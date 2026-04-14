import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import json
import os
from typing import Optional

from . import repository

# Файл для хранения привязанных каналов
CONFIG_FILE = "emission_config.json"

# Часовой пояс MSK (UTC+3)
MSK_TZ = timezone(timedelta(hours=3))


def load_config() -> dict:
    """Загружает конфигурацию привязки каналов"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"channels": {}}


def save_config(config: dict):
    """Сохраняет конфигурацию"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def format_time_diff(dt_str: str) -> str:
    """Форматирует разницу во времени для человека (MSK)"""
    if not dt_str:
        return "Неизвестно"
    
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        # Конвертируем в MSK
        dt_msk = dt.astimezone(MSK_TZ)
        now = datetime.now(MSK_TZ)
        diff = now - dt
        
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours} ч {minutes} мин назад"
        else:
            return f"{minutes} мин назад"
    except:
        return "Ошибка"


def format_time_msk(dt_str: str) -> str:
    """Форматирует время в MSK для Discord"""
    if not dt_str:
        return "Неизвестно"
    
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        # Конвертируем в MSK
        dt_msk = dt.astimezone(MSK_TZ)
        unix_ts = int(dt_msk.timestamp())
        return f"<t:{unix_ts}:F>"  # Полная дата и время
    except:
        return "Ошибка"


def format_time_relative_msk(dt_str: str) -> str:
    """Форматирует относительное время в MSK для Discord"""
    if not dt_str:
        return "Неизвестно"
    
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        # Конвертируем в MSK
        dt_msk = dt.astimezone(MSK_TZ)
        unix_ts = int(dt_msk.timestamp())
        return f"<t:{unix_ts}:R>"  # Относительное время ("2 часа назад")
    except:
        return "Ошибка"


class EmissionCog(commands.Cog):
    """Ког для уведомлений о выбросах"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_config()
        self.last_emission_start = None
        self.emission_check.start()
    
    def cog_unload(self):
        """Останавливает задачу при выгрузке кога"""
        self.emission_check.cancel()
    
    @commands.command(name="emission")
    async def emission(self, ctx: commands.Context, subcommand: Optional[str] = None, *, arg: Optional[str] = None):
        """
        🌪️ Настройка уведомлений:
        • `!emission bind #канал` — привязать канал для уведомлений (только админ)
        • `!emission unbind` — отвязать канал (только админ)
        • `!emission check` — проверить привязанный канал (только админ)
        • `!emission time` — время с последнего выброса (все)
        • `!emission info` — полная информация о выбросах (все)
        """
        
        if subcommand == "bind":
            # 🔐 Привязка канала (только админ)
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ Только администраторы могут привязывать каналы!", delete_after=10)
                return
            
            # Получаем канал из упоминания или по ID
            channel = None
            if ctx.message.channel_mentions:
                channel = ctx.message.channel_mentions[0]
            elif arg and arg.isdigit():
                try:
                    channel = await self.bot.fetch_channel(int(arg))
                except:
                    pass
            
            if not channel:
                await ctx.send("❌ Укажите канал: `!emission bind #канал`")
                return
            
            # Сохраняем привязку для этого сервера
            guild_id = str(ctx.guild.id)
            self.config["channels"][guild_id] = str(channel.id)
            save_config(self.config)
            
            await ctx.send(f"✅ Канал {channel.mention} привязан для уведомлений о выбросах!")
        
        elif subcommand == "unbind":
            # 🔐 Отвязка канала (только админ)
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ Только администраторы могут отвязывать каналы!", delete_after=10)
                return
            
            guild_id = str(ctx.guild.id)
            if guild_id in self.config["channels"]:
                del self.config["channels"][guild_id]
                save_config(self.config)
                await ctx.send("✅ Канал отвязан от уведомлений о выбросах.")
            else:
                await ctx.send("❌ Для этого сервера не привязан канал.")
        
        elif subcommand == "check":
            # 🔐 Проверка привязанного канала (только админ)
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ Только администраторы могут проверять настройки!", delete_after=10)
                return
            
            guild_id = str(ctx.guild.id)
            channel_id = self.config["channels"].get(guild_id)
            
            if channel_id:
                try:
                    channel = await self.bot.fetch_channel(int(channel_id))
                    embed = discord.Embed(
                        title="🌪️ Настройки уведомлений о выбросах",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="📺 Канал", value=channel.mention, inline=False)
                    embed.add_field(name="🆔 ID канала", value=f"`{channel_id}`", inline=True)
                    embed.add_field(name="🏷 Название", value=channel.name, inline=True)
                    embed.set_footer(text="Используйте !emission unbind для отвязки")
                    await ctx.send(embed=embed)
                except:
                    await ctx.send(f"⚠️ Канал с ID `{channel_id}` не найден. Возможно, он был удалён.")
            else:
                await ctx.send("❌ Для этого сервера не привязан канал.\nИспользуйте `!emission bind #канал` для привязки.")
        
        elif subcommand == "time":
            # 👥 Время с последнего выброса (публично)
            await ctx.defer()
            try:
                data = await repository.get_emission_data()
                if not data:
                    await ctx.send("❌ Не удалось получить данные о выбросах.")
                    return
                
                prev_start = data.get("previousStart")
                time_str = format_time_diff(prev_start)
                
                embed = discord.Embed(
                    title="🌪️ Последний выброс",
                    description=f"Прошло: **{time_str}**",
                    color=discord.Color.purple(),
                    timestamp=datetime.now(MSK_TZ)
                )
                
                if prev_start:
                    msk_time = format_time_msk(prev_start)
                    embed.add_field(name="🕐 Время начала ", value=msk_time, inline=False)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"⚠️ Ошибка: `{str(e)}`")
        
        elif subcommand == "info":
            # 👥 Полная информация (публично)
            await ctx.defer()
            try:
                data = await repository.get_emission_data()
                if not data:
                    await ctx.send("❌ Не удалось получить данные о выбросах.")
                    return
                
                embed = discord.Embed(
                    title="🌪️ Статус выбросов",
                    color=discord.Color.purple(),
                    timestamp=datetime.now(MSK_TZ)
                )
                
                # Текущий выброс
                current = data.get("currentStart")
                if current:
                    msk_time = format_time_msk(current)
                    relative_time = format_time_relative_msk(current)
                    embed.add_field(
                        name="🔴 Текущий выброс",
                        value=f"Начался: {relative_time}\n{msk_time}",
                        inline=False
                    )
                
                # Предыдущий выброс
                prev_start = data.get("previousStart")
                prev_end = data.get("previousEnd")
                if prev_start:
                    prev_info = f"Начало: {format_time_msk(prev_start)}"
                    if prev_end:
                        prev_info += f"\nОкончание: {format_time_msk(prev_end)}"
                    embed.add_field(name="⚪ Предыдущий выброс", value=prev_info, inline=False)

                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"⚠️ Ошибка: `{str(e)}`")
        
        else:
            # Справка
            embed = discord.Embed(
                title="🌪️ Команды выбросов",
                description=(
                    "• `!emission bind #канал` — привязать канал (админ)\n"
                    "• `!emission unbind` — отвязать канал (админ)\n"
                    "• `!emission check` — проверить настройки (админ)\n"
                    "• `!emission time` — время с последнего выброса (все)\n"
                    "• `!emission info` — полная информация (все)"
                ),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
    
    @tasks.loop(seconds=10)
    async def emission_check(self):
        """ Проверка новых выбросов каждые 5 минут"""
        try:
            data = await repository.get_emission_data()
            if not data:
                return
            
            current_start = data.get("currentStart")
            if not current_start:
                return
            
            # Если это новый выброс (не совпадает с запомненным)
            if current_start != self.last_emission_start:
                self.last_emission_start = current_start
                
                # Конвертируем время в MSK
                try:
                    dt = datetime.fromisoformat(current_start.replace("Z", "+00:00"))
                    dt_msk = dt.astimezone(MSK_TZ)
                    unix_ts = int(dt_msk.timestamp())
                    msk_time_full = f"<t:{unix_ts}:F>"  # Полное время
                except:
                    msk_time_full = current_start
                
                # Отправляем уведомления во все привязанные каналы
                for guild_id, channel_id in self.config["channels"].items():
                    try:
                        guild = self.bot.get_guild(int(guild_id))
                        if not guild:
                            continue
                        
                        channel = guild.get_channel(int(channel_id))
                        if not channel:
                            continue
                        
                        embed = discord.Embed(
                            title="🌪️ НАЧАЛСЯ ВЫБРОС!",
                            description=f"⚠️ **В Зоне начался выброс!**\n\n{msk_time_full}",
                            color=discord.Color.red(),
                            timestamp=datetime.now(MSK_TZ)
                        )
                        embed.set_footer(text="Stalcraft: X Emission Alert")
                        
                        await channel.send(embed=embed)
                        print(f"✅ Уведомление о выбросе отправлено в канал {channel_id}")
                        
                    except Exception as e:
                        print(f"❌ Не удалось отправить уведомление в канал {channel_id}: {e}")
                        
        except Exception as e:
            print(f"❌ Ошибка в emission_check: {e}")
    
    @emission_check.before_loop
    async def before_emission_check(self):
        """Ждём готовности бота перед запуском задачи"""
        await self.bot.wait_until_ready()
        try:
            data = await repository.get_emission_data()
            if data:
                self.last_emission_start = data.get("currentStart")
                print(f"🌪️ Последний выброс при старте: {self.last_emission_start}")
        except Exception as e:
            print(f"⚠️ Не удалось инициализировать выбросы: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(EmissionCog(bot))