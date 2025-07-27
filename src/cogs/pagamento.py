"""Integração com Mercado Pago e deploy automático."""

from __future__ import annotations

import asyncio
import io
import logging
import os
import json

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
import mercadopago
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gestao import Gestao

import squarecloud


def _carregar_config() -> dict:
    raiz = os.path.dirname(os.path.dirname(__file__))
    caminho = os.path.join(raiz, "config.json")
    if os.path.isfile(caminho):
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return {}


class Pagamentos(commands.Cog):
    """Gerencia pagamentos via Mercado Pago."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        dados = _carregar_config()
        token = dados.get("mercadopago_token")
        self.zip_url = dados.get("zip_url")
        self.preco = float(dados.get("preco", 0))
        self.sdk = mercadopago.SDK(token) if token else None

    def atualizar_config(self, token: str, url_zip: str, preco: float) -> None:
        """Atualiza o cliente, o link de deploy e o preço."""
        self.sdk = mercadopago.SDK(token)
        self.zip_url = url_zip
        self.preco = preco

    async def _verificar_pagamento(self, pref_id: str, usuario: discord.User):
        """Verifica periodicamente se o pagamento foi aprovado."""
        if not self.sdk:
            return
        for _ in range(30):
            await asyncio.sleep(10)
            busca = self.sdk.payment().search({"preference_id": pref_id})
            resultados = busca["response"].get("results")
            if resultados:
                pagamento = resultados[0]["collection"]
                if pagamento.get("status") == "approved":
                    await self._realizar_deploy(usuario)
                    return

    async def _realizar_deploy(self, usuario: discord.User):
        """Realiza o deploy da aplicação configurada."""
        gestao: Gestao | None = self.bot.get_cog("Gestao")  # type: ignore
        if not gestao or not gestao.cliente or not self.zip_url:
            return
        async with aiohttp.ClientSession() as sessao:
            async with sessao.get(self.zip_url) as resp:
                dados = await resp.read()
        arquivo = squarecloud.File(io.BytesIO(dados), filename="app.zip")
        try:
            await gestao.cliente.upload_app(arquivo)
            await usuario.send("Pagamento confirmado! Deploy iniciado.")
        except Exception as exc:
            await usuario.send(f"Erro ao fazer deploy: {exc}")

    @app_commands.command(name="pagar", description="Realiza pagamento para deploy")
    async def pagar(self, interaction: discord.Interaction):
        if not self.sdk or not self.zip_url:
            await interaction.response.send_message("Pagamento não configurado.", ephemeral=True)
            return
        dados = {
            "items": [
                {
                    "title": "Deploy de Aplicação",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": self.preco,
                }
            ]
        }
        resposta = self.sdk.preference().create(dados)
        init_point = resposta["response"].get("init_point")
        pref_id = resposta["response"].get("id")
        if not init_point or not pref_id:
            await interaction.response.send_message("Erro ao gerar link de pagamento.", ephemeral=True)
            return
        await interaction.response.send_message(f"Clique para pagar: {init_point}", ephemeral=True)
        asyncio.create_task(self._verificar_pagamento(pref_id, interaction.user))


async def setup(bot: commands.Bot):
    await bot.add_cog(Pagamentos(bot))

