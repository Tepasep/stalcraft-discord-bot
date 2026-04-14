import discord
from discord.ext import commands
from . import repository
from datetime import datetime
from typing import Dict, Any, Optional

# Маппинг группировок на русский язык
FACTION_NAMES = {
    "merc": "Наемники",
    "covenant": "Завет",
    "zarya": "Заря",
    "dolg": "Долг",
    "bandit": "Бандиты",
    "stalker": "Сталкеры",
}

# Маппинг рангов клана на русский
CLAN_RANKS = {
    "RECRUIT": "Запасной",
    "COMMONER": "Рядовой",
    "SOLDIER": "Боец",
    "SERGEANT": "Сержант",
    "OFFICER": "Офицер",
    "COLONEL": "Полковник",
    "LEADER": "Лидер"
}

# Конфигурация статистики по категориям
CATEGORY_STATS = {
    "zone": {
        "title": "🌍 Зона",
        "fields": [
            ("⏳ В игре", "pla-tim", "hours"),
            ("👥 В отряде", "par-tim", "hours"),
            ("📡 Сигналов найдено", "sgn-fnd", "number"),
            ("💬 Сообщений в чат", "cha-mes-sen", "number"),
            ("🧪 Артефактов собрано", "art-col", "number"),
            ("🦠 Мутантов убито", "mut-kil", "number"),
        ]
    },
    "open": {
        "title": "🌐 Открытый мир",
        "fields": [
            ("🚶 Пройдено пешком", "dis-on-foo", "distance"),
            ("🤫 Пройдено крадучись", "dis-sne", "distance"),
            ("💰 Заработано на посылках", "tpacks-money", "number"),
            ("🔍 Сканирований проведено", "scn-cnt", "number"),
            ("📜 Квестов завершено", "que-fin", "number"),
            ("🏆 Достижений получено", "ach-gai", "number"),
            ("🕳 Тайников выкопано", "mining-count", "number"),
        ]
    },
    "pvp": {
        "title": "⚔️ Боевая статистика",
        "fields": [
            ("📊 K/D в опене", "kd_ratio", "ratio"),
            ("💀 Убито игроков", "kil", "number"),
            ("☠️ Смертей от пуль", "bul-dea", "number"),
            ("🔫 Урон игрокам", "dam-dea-pla", "decimal"),
            ("🛡 Получено урона", "dam-rec-pla", "decimal"),
            ("🎯 Попаданий", "sho-hit", "number"),
            ("🤕 Выстрелов в голову", "sho-hea", "number"),
            ("🔪 Зарезано", "kni-kil", "number"),
        ]
    },
    "sessions": {
        "title": "🎮 Сессии",
        "fields": [
            ("🎮 Матчей", "part-bf", "number"),
            ("🏆 Побед", "won-bf", "number"),
            ("❌ Поражений", "lost-bf", "number"),
            ("💀 Убийств", "kills-bf", "number"),
            ("☠️ Смертей", "deaths-bf", "number"),
            ("📊 K/D", "bf_kd", "ratio"),
        ]
    }
}


def format_description(text: str) -> str:
    """Форматирует описание персонажа для Discord"""
    if not text:
        return "*Нет описания*"
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    clean_text = '\n'.join(lines)
    
    if len(clean_text) > 1000:
        clean_text = clean_text[:997] + "..."
        
    return clean_text if clean_text else "*Нет описания*"


class StatsView(discord.ui.View):
    """View с кнопками выбора категории статистики"""
    
    def __init__(self, character_data: Dict[str, Any], original_author: discord.Member):
        super().__init__(timeout=300)
        self.character_data = character_data
        self.original_author = original_author
        
        self.stats_dict = {stat["id"]: stat["value"] for stat in character_data.get("stats", [])}
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.original_author:
            await interaction.response.send_message("❌ Вы не можете выбирать категории в этом сообщении!", ephemeral=True)
            return False
        return True
    
    def get_stat_value(self, stat_id: str, format_type: str) -> str:
        """Получает и форматирует значение статистики"""
        
        if stat_id == "kd_ratio":
            try:
                kills = float(self.stats_dict.get("kil", 0))
                deaths = float(self.stats_dict.get("bul-dea", 1))
                return f"{round(kills / deaths, 2)}" if deaths > 0 else f"{kills:.0f}"
            except:
                return "N/A"
        
        if stat_id == "bf_wr":
            try:
                won = float(self.stats_dict.get("won-bf", 0))
                lost = float(self.stats_dict.get("lost-bf", 0))
                total = won + lost
                wr = (won / total * 100) if total > 0 else 0
                return f"{wr:.1f}%"
            except:
                return "N/A"

        if stat_id == "bf_kd":
            try:
                kills = float(self.stats_dict.get("kills-bf", 0))
                deaths = float(self.stats_dict.get("deaths-bf", 1))
                return f"{round(kills / deaths, 2)}" if deaths > 0 else f"{kills:.0f}"
            except:
                return "N/A"

        value = self.stats_dict.get(stat_id, 0)
        
        if format_type == "hours":
            try:
                val = float(value)
                if val > 10_000_000: 
                    return f"{round(val / 3_600_000, 1)} ч"
                else: 
                    return f"{round(val / 3600, 1)} ч"
            except:
                return "N/A"
        
        elif format_type == "distance":
            try:
                return f"{round(float(value) / 100000, 1)} км"
            except:
                return "N/A"
        
        elif format_type == "decimal":
            try:
                return f"{float(value):,.1f}"
            except:
                return "N/A"
        
        elif format_type == "percent":
            try:
                return f"{float(value):.1f}%"
            except:
                return "N/A"
        
        elif format_type == "ratio":
            try:
                kills = float(self.stats_dict.get("kil", 0))
                deaths = float(self.stats_dict.get("dea", 1))
                return f"{round(kills / deaths, 2)}" if deaths > 0 else f"{kills:.0f}"
            except:
                return "N/A"
        
        else:
            try:
                return f"{int(value):,}"
            except:
                return "N/A"
    
    async def show_category(self, interaction: discord.Interaction, category: str):
        """Показывает статистику выбранной категории"""
        cat_data = CATEGORY_STATS[category]
        
        embed = discord.Embed(
            title=cat_data["title"],
            color=discord.Color.blue(),
        )
        
        # Основная информация
        username = self.character_data.get("username", "Unknown")
        alliance = self.character_data.get("alliance", "none")
        faction_name = FACTION_NAMES.get(alliance.lower(), alliance.title())
        
        # Получаем тег клана
        clan_data = self.character_data.get("clan")

        clan_data = self.character_data.get("clan")
        if clan_data:
            clan_tag = clan_data.get("info", {}).get("tag", "")
            clan_display = f"[{clan_tag}]" if clan_tag else "Без клана"
        else:
            clan_display = "Без клана"
        
        # Описание: Ник | Группировка | Клан
        embed.description = f"{clan_display} | **{username}** | {faction_name}"
        
        # Добавляем поля
        for field_name, stat_id, format_type in cat_data["fields"]:
            field_value = self.get_stat_value(stat_id, format_type)
            embed.add_field(name=field_name, value=field_value, inline=True)
        
        await interaction.response.edit_message(view=self, embed=embed)

    @discord.ui.button(label="Зона", emoji="🌍", style=discord.ButtonStyle.secondary, row=0)
    async def zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_category(interaction, "zone")
    
    @discord.ui.button(label="Открытый мир", emoji="🌐", style=discord.ButtonStyle.secondary, row=0)
    async def open_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_category(interaction, "open")

    @discord.ui.button(label="PvP", emoji="⚔️", style=discord.ButtonStyle.red, row=0)
    async def pvp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_category(interaction, "pvp")

    @discord.ui.button(label="Сессии", emoji="🎮", style=discord.ButtonStyle.blurple, row=0)
    async def sessions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_category(interaction, "sessions")


class StatsCog(commands.Cog):
    """Ког с командами для просмотра статистики"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_clan_info(self, character_data: Dict[str, Any]) -> str:
        """Получает информацию о клане: [tag] name | rank"""
        clan_data = character_data.get("clan")
        
        if not clan_data or not isinstance(clan_data, dict):
            return "Нет клана"
        
        clan_info = clan_data.get("info", {})
        clan_member = clan_data.get("member", {})
        
        clan_tag = clan_info.get("tag", "")
        clan_name = clan_info.get("name", "")
        
        if not clan_name and not clan_tag:
            return "Нет клана"
        if clan_tag and clan_name:
            clan_display_name = f"[{clan_tag}] {clan_name}"
        elif clan_tag:
            clan_display_name = f"[{clan_tag}]"
        else:
            clan_display_name = clan_name
        
        rank_en = clan_member.get("rank", "RECRUIT")
        rank_ru = CLAN_RANKS.get(rank_en.upper(), rank_en.title())
        
        return f"{clan_display_name} | {rank_ru}"

    @commands.command(name="stats", aliases=["s"])
    async def stats(self, ctx: commands.Context, *, nickname: str):
        """Показать статистику игрока: !stats NickName"""
        
        loading_msg = await ctx.send(f"🔍 Ищу информацию по **{nickname}**...")
        
        try:
            raw_data = await repository.get_player_stats(nickname)
            
            if raw_data is None:
                await loading_msg.edit(content=f"❌ Игрок **{nickname}** не найден.")
                return

            character = raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
            
            view = StatsView(character, ctx.author)
            
            username = character.get("username", nickname)
            alliance = character.get("alliance", "none")
            faction_name = FACTION_NAMES.get(alliance.lower(), alliance.title())
            
            stats_dict = {stat["id"]: stat["value"] for stat in character.get("stats", [])}
            
            reg_time_val = stats_dict.get("reg-tim")
            reg_date_str = "Неизвестно"
            if reg_time_val:
                try:
                    if isinstance(reg_time_val, (int, float)):
                        dt = datetime.fromtimestamp(reg_time_val)
                    else:
                        dt = datetime.fromisoformat(str(reg_time_val).replace("Z", "+00:00"))
                    reg_date_str = f"<t:{int(dt.timestamp())}:D>"
                except:
                    reg_date_str = str(reg_time_val)[:10]

            # Получаем информацию о клане
            clan_display = await self.get_clan_info(character)

            status_text = character.get("status", "")
            formatted_status = format_description(status_text)

            embed = discord.Embed(
                title=f"👤 Профиль: {username}",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="🛡 Группировка", value=faction_name, inline=True)
            embed.add_field(name="🏰 Клан", value=clan_display, inline=True)
            embed.add_field(name="📅 Регистрация", value=reg_date_str, inline=True)
            embed.add_field(name="📝 Описание", value=formatted_status, inline=False)
            
            await loading_msg.edit(content=None, embed=embed, view=view)
            
        except Exception as e:
            await loading_msg.edit(content=f"⚠️ Произошла ошибка: `{str(e)}`")
            print(f"❌ [Stats Command Error] {e}")
            import traceback
            traceback.print_exc()


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))