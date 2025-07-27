import os
import io
import json
import logging
import aiohttp
import discord
import pydantic
from discord import app_commands
from discord.ext import commands
import squarecloud


async def obter_status(app: squarecloud.Application, cliente: squarecloud.Client) -> squarecloud.StatusData:
    """Retorna o StatusData da aplicação lidando com possíveis mudanças na API."""
    try:
        return await cliente.app_status(app.id)
    except pydantic.ValidationError:
        resposta = await cliente._http.fetch_app_status(app.id)
        dados = resposta.response
        dados.setdefault("requests", 0)
        return squarecloud.StatusData(**dados)


def _carregar_token() -> str | None:
    """Retorna o token salvo em config.json se existir."""
    caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.isfile(caminho):
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados.get("token")
    return None


class DeployModal(discord.ui.Modal):
    """Modal para envio do link de um arquivo zip."""

    link = discord.ui.TextInput(label="Link para o ZIP", placeholder="https://.../app.zip")

    def __init__(self, cog: commands.Cog):
        super().__init__(title="Deploy")
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = str(self.link)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise RuntimeError("Falha ao baixar o arquivo")
                    dados = await resp.read()
        except Exception as exc:
            await interaction.followup.send(f"Erro ao baixar o arquivo: {exc}", ephemeral=True)
            return
        arquivo = squarecloud.File(io.BytesIO(dados), filename="app.zip")
        try:
            await self.cog.cliente.upload_app(arquivo)
            await interaction.followup.send("Deploy iniciado com sucesso!", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"Erro ao fazer deploy: {exc}", ephemeral=True)


class ConfirmarExclusao(discord.ui.View):
    """View para múltiplas confirmações de exclusão."""

    def __init__(self, app: squarecloud.Application):
        super().__init__(timeout=30)
        self.app = app
        self._confirmacoes = 0

    @discord.ui.button(label="✅", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._confirmacoes += 1
        if self._confirmacoes < 2:
            await interaction.response.edit_message(content="Pressione novamente para confirmar a exclusão.", view=self)
            return
        await interaction.response.edit_message(content="Excluindo aplicação...", view=None)
        try:
            await self.app.delete()
            await interaction.followup.send("Aplicação excluída com sucesso.", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"Erro ao excluir: {exc}", ephemeral=True)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Exclusão cancelada.", view=None)


class ControlesAplicacao(discord.ui.View):
    """View com botões para controle da aplicação."""

    def __init__(self, app: squarecloud.Application, cog: commands.Cog):
        super().__init__(timeout=1000)
        self.app = app
        self.cog = cog

    async def atualizar_mensagem(self, interaction: discord.Interaction):
        status = await obter_status(self.app, self.cog.cliente)
        embed = criar_embed(self.app, status)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="🔷", style=discord.ButtonStyle.secondary)
    async def atualizar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.atualizar_mensagem(interaction)

    @discord.ui.button(emoji="🟩", style=discord.ButtonStyle.secondary)
    async def iniciar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.app.start()
        except Exception as exc:
            await interaction.followup.send(f"Erro ao iniciar: {exc}", ephemeral=True)
            return
        await self.atualizar_mensagem(interaction)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary)
    async def reiniciar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.app.restart()
        except Exception as exc:
            await interaction.followup.send(f"Erro ao reiniciar: {exc}", ephemeral=True)
            return
        await self.atualizar_mensagem(interaction)

    @discord.ui.button(emoji="🟥", style=discord.ButtonStyle.secondary)
    async def parar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.app.stop()
        except Exception as exc:
            await interaction.followup.send(f"Erro ao parar: {exc}", ephemeral=True)
            return
        await self.atualizar_mensagem(interaction)

    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, row=1)
    async def excluir(self, interaction: discord.Interaction, _: discord.ui.Button):
        view = ConfirmarExclusao(self.app)
        await interaction.response.send_message("Tem certeza que deseja excluir?", view=view, ephemeral=True)


class MenuAplicacoes(discord.ui.View):
    """View principal com a seleção de aplicações."""

    def __init__(self, apps: list[squarecloud.Application], cog: commands.Cog):
        super().__init__(timeout=60)
        opcoes = [discord.SelectOption(label=app.name, value=app.id) for app in apps]
        opcoes.append(discord.SelectOption(label="Deploy via ZIP", value="deploy"))
        self.select = discord.ui.Select(placeholder="Escolha uma aplicação", options=opcoes)
        self.select.callback = self.callback
        self.add_item(self.select)
        self.apps = {app.id: app for app in apps}
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        escolha = self.select.values[0]
        if escolha == "deploy":
            await interaction.response.send_modal(DeployModal(self.cog))
            return
        app = self.apps.get(escolha)
        status = await obter_status(app, self.cog.cliente)
        embed = criar_embed(app, status)
        view = ControlesAplicacao(app, self.cog)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


def criar_embed(app: squarecloud.Application, status: squarecloud.StatusData) -> discord.Embed:
    """Cria um embed organizado e de fácil leitura com as informações da aplicação."""

    def formatar_duracao(ms: int | None) -> str:
        if not ms:
            return "0"
        from datetime import timedelta

        duracao = timedelta(milliseconds=ms)
        dias = duracao.days
        if dias:
            return f"{dias} dias"
        horas, resto = divmod(duracao.seconds, 3600)
        minutos, segundos = divmod(resto, 60)
        return f"{horas:02}:{minutos:02}:{segundos:02}"

    cor = discord.Color.green() if status.running else discord.Color.red()
    embed = discord.Embed(
        title=app.name,
        description="Aplicação hospedada via SquareCloud",
        colour=cor,
    )

    emoji_status = "🟢" if status.running else "🔴"
    embed.add_field(name="📊 Status", value=f"{emoji_status} **{status.status}**", inline=True)
    embed.add_field(name="⚙️ CPU", value=status.cpu, inline=True)
    embed.add_field(name="🧠 RAM", value=status.ram, inline=True)
    embed.add_field(name="💽 Armazenamento", value=status.storage, inline=True)
    embed.add_field(name="📡 Requests", value=str(status.requests), inline=True)
    embed.add_field(name="🔄 Uptime", value=formatar_duracao(status.uptime), inline=True)
    embed.add_field(name="⏳ Tempo", value=formatar_duracao(status.time), inline=True)
    embed.add_field(
        name="📍 Dashboard",
        value=f"[Acessar painel](https://dash.squarecloud.app/dashboard/app/{app.id})",
        inline=False,
    )

    from datetime import datetime

    embed.set_footer(text=datetime.utcnow().strftime("Dados gerados em %d/%m/%Y %H:%M:%S"))
    return embed


class Gestao(commands.Cog):
    """Cog principal de gestão das aplicações."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        token = _carregar_token()
        self.cliente = squarecloud.Client(token) if token else None

    @app_commands.command(name="dashboard", description="Gerencia suas aplicações")
    async def dashboard(self, interaction: discord.Interaction):
        if not self.cliente:
            await interaction.response.send_message("Token não configurado.", ephemeral=True)
            return
        try:
            apps = await self.cliente.all_apps()
        except Exception as exc:
            await interaction.response.send_message(f"Erro ao obter aplicações: {exc}", ephemeral=True)
            return
        view = MenuAplicacoes(apps, self)
        await interaction.response.send_message("Selecione uma aplicação:", view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gestao(bot))