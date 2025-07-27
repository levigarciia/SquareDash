import os
import logging

from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

logger = logging.getLogger('__name__')

# Configurações de Intents
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
bot = commands.Bot(command_prefix='!', intents=intents)
bot.logger = logging.getLogger("squarebot")

@bot.event
async def on_ready():
    bot.logger.info("Conectado como %s", bot.user.name)
    await bot.tree.sync()

async def carregar_cogs():
    logger.info("Carregando Cogs...")
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cogs")
    for arquivo in os.listdir(caminho):
        if arquivo.endswith('.py') and arquivo != '__init__.py':
            nome_cog = arquivo[:-3]
            try:
                await bot.load_extension(f'cogs.{nome_cog}')
                logger.info(f"✅ {nome_cog} carregada com sucesso.")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar cog {nome_cog}: {e}")

async def main():
    await carregar_cogs()
    token = os.getenv('BOT_TOKEN')
    await bot.start(token)

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot desconectado.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")
