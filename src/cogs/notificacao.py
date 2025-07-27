import asyncio
import logging
import os
import json

import discord
from discord.ext import commands
import squarecloud


def _carregar_dados() -> dict:
    raiz = os.path.dirname(os.path.dirname(__file__))
    caminho = os.path.join(raiz, "config.json")
    if os.path.isfile(caminho):
        with open(caminho, "r", encoding="utf-8") as arq:
            return json.load(arq)
    return {}


def definir_admin(id_admin: int) -> None:
    dados = _carregar_dados()
    dados["admin_id"] = id_admin
    raiz = os.path.dirname(os.path.dirname(__file__))
    caminho = os.path.join(raiz, "config.json")
    with open(caminho, "w", encoding="utf-8") as arq:
        json.dump(dados, arq, ensure_ascii=False, indent=4)


class Notificador(commands.Cog):
    """Envia mensagens para o administrador em caso de problemas."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        dados = _carregar_dados()
        self.id_admin: int | None = dados.get("admin_id")
        self.task: asyncio.Task | None = None

    async def cog_load(self):
        self.task = asyncio.create_task(self._verificar())

    async def cog_unload(self):
        if self.task:
            self.task.cancel()

    async def _notificar(self, mensagem: str) -> None:
        if not self.id_admin:
            return
        try:
            usuario = await self.bot.fetch_user(self.id_admin)
            await usuario.send(mensagem)
        except Exception as exc:
            self.logger.error("Falha ao notificar admin: %s", exc)

    async def _verificar(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            gestao: commands.Cog | None = self.bot.get_cog("Gestao")
            if gestao and getattr(gestao, "cliente", None):
                cliente: squarecloud.Client = gestao.cliente  # type: ignore
                try:
                    apps = await cliente.all_apps()
                    for app in apps:
                        try:
                            status = await cliente.app_status(app.id)
                            if not status.running:
                                await self._notificar(f"Aplicação {app.name} parou de funcionar.")
                        except Exception as exc:
                            await self._notificar(f"Erro ao verificar {app.name}: {exc}")
                except Exception as exc:
                    await self._notificar(f"Erro ao acessar SquareCloud: {exc}")
            await asyncio.sleep(300)

async def setup(bot: commands.Bot):
    await bot.add_cog(Notificador(bot))
