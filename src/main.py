import logging
import discord
from discord.ext import commands

from . import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True  # Разрешить чтение содержимого сообщений
intents.members = True 

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("------")

    await bot.load_extension("src.emission_cog")

    try:
        await bot.load_extension("src.commands")
        logger.info("✅ Extension 'src.commands' loaded successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load extension: {e}")

    await bot.change_presence(activity=discord.Game(name="STALCRAFT X | Tepas"))


def main():
    try:
        bot.run(config.DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Token provided in .env")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")


if __name__ == "__main__":
    main()