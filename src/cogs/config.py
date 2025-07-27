## Comandos de configuração da Square dentro do discord
import logging
import discord
from discord import app_commands
from discord.ext import commands

import squarecloud

import json
import os

def definir_token(token: str):
    """Salva o token em um arquivo JSON fora do versionamento."""
    dados = {"token": token}
    # O arquivo config.json fica no diretório raiz do projeto
    raiz = os.path.dirname(os.path.dirname(__file__))
    caminho = os.path.join(raiz, "config.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)

class TokenModal(discord.ui.Modal, title="Configurar"):
    token = discord.ui.TextInput(label="Token da Square Cloud", placeholder="Insira seu token aqui", style=discord.TextStyle.short, required=True)
    def __init__(self, cog: commands.Cog):
        super().__init__(title="Configurar Token")
        self.cog = cog
    
    async def on_submit(self, interaction: discord.Interaction):
        texto_token = str(self.token)
        definir_token(texto_token)
        gestao = self.cog.bot.get_cog("Gestao")
        if gestao:
            gestao.cliente = squarecloud.Client(texto_token)
        await interaction.response.send_message("✅ Token configurado com sucesso!", ephemeral=True)

class ConfigCog(commands.Cog):
    """Comandos de configuração da Square dentro do Discord."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @app_commands.command(name="configurar", description="Configura o token da Square Cloud.")
    async def configurar(self, interaction: discord.Interaction):
        """Abre um modal para configurar o token da Square Cloud."""
        modal = TokenModal(self)
        await interaction.response.send_modal(TokenModal(self))

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCog(bot))
