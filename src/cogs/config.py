## Comandos de configuração da Square dentro do discord
import logging
import discord
from discord import app_commands
from discord.ext import commands

import squarecloud

import json
import os


def _carregar_config() -> dict:
    """Lê o arquivo config.json se existir."""
    raiz = os.path.dirname(os.path.dirname(__file__))
    caminho = os.path.join(raiz, "config.json")
    if os.path.isfile(caminho):
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return {}

def definir_token(token: str):
    """Salva o token da Square Cloud em config.json."""
    dados = _carregar_config()
    dados["token"] = token
    raiz = os.path.dirname(os.path.dirname(__file__))
    caminho = os.path.join(raiz, "config.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)


def definir_pagamento(token_mp: str, url_zip: str, preco: float):
    """Salva as configurações de pagamento."""
    dados = _carregar_config()
    dados["mercadopago_token"] = token_mp
    dados["zip_url"] = url_zip
    dados["preco"] = preco
    raiz = os.path.dirname(os.path.dirname(__file__))
    caminho = os.path.join(raiz, "config.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)

class ConfigModal(discord.ui.Modal, title="Configurar"):
    token = discord.ui.TextInput(
        label="Token da Square Cloud",
        style=discord.TextStyle.short,
        required=True,
    )
    mp_token = discord.ui.TextInput(
        label="Token Mercado Pago",
        style=discord.TextStyle.short,
        required=False,
    )
    zip_url = discord.ui.TextInput(
        label="Link do ZIP de deploy",
        style=discord.TextStyle.short,
        required=False,
    )
    preco = discord.ui.TextInput(
        label="Preço (R$)",
        style=discord.TextStyle.short,
        required=False,
    )
    admin_id = discord.ui.TextInput(
        label="ID do Administrador",
        style=discord.TextStyle.short,
        required=False,
    )

    def __init__(self, cog: commands.Cog):
        super().__init__(title="Configurações Gerais")
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        token_sc = str(self.token)
        token_mp = str(self.mp_token).strip()
        zip_url = str(self.zip_url).strip()
        preco_txt = self.preco.value.strip()
        admin_txt = self.admin_id.value.strip()

        definir_token(token_sc)

        if token_mp and zip_url and preco_txt:
            try:
                valor = float(preco_txt)
            except ValueError:
                await interaction.response.send_message(
                    "Preço inválido.", ephemeral=True
                )
                return
            definir_pagamento(token_mp, zip_url, valor)
            pagamentos = self.cog.bot.get_cog("Pagamentos")
            if pagamentos:
                pagamentos.atualizar_config(token_mp, zip_url, valor)
        if admin_txt:
            from .notificacao import definir_admin

            try:
                admin_id = int(admin_txt)
            except ValueError:
                await interaction.response.send_message(
                    "ID do administrador inválido.",
                    ephemeral=True,
                )
                return
            definir_admin(admin_id)
            notificador = self.cog.bot.get_cog("Notificador")
            if notificador:
                notificador.id_admin = admin_id
        gestao = self.cog.bot.get_cog("Gestao")
        if gestao:
            gestao.cliente = squarecloud.Client(token_sc)
        await interaction.response.send_message("✅ Configurações salvas!", ephemeral=True)

class ConfigCog(commands.Cog):
    """Comandos de configuração da Square dentro do Discord."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @app_commands.command(
        name="configurar",
        description="Define tokens, pagamento e administrador.",
    )
    async def configurar(self, interaction: discord.Interaction):
        """Abre um modal para configurar todas as chaves."""
        await interaction.response.send_modal(ConfigModal(self))

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCog(bot))
