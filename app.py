import discord
from discord.ext import commands
from discord.ui import Button, View, Select, SelectOption
import re
import os  # Importa a biblioteca para pegar variáveis de ambiente

# Lê o token da variável de ambiente (Railway)
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

STAFF_ROLE_ID = 1303079219626250260  # ID do cargo de staff
SOLICITACAO_CHANNEL_ID = 1338708818527256617  # ID do canal de solicitações

class ApprovalView(View):
    def __init__(self, nome_canal, membro, categorias):
        super().__init__(timeout=None)
        self.nome_canal = nome_canal
        self.membro = membro
        self.categorias = categorias

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: Button):
        if STAFF_ROLE_ID not in [role.id for role in interaction.user.roles] and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você não tem permissão para aprovar solicitações.", ephemeral=True)
            return
        
        select = CategorySelect(categorias=self.categorias, nome_canal=self.nome_canal, membro=self.membro)
        await interaction.response.send_message("Escolha a categoria para o novo canal:", view=select)

    @discord.ui.button(label="Rejeitar", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        if STAFF_ROLE_ID not in [role.id for role in interaction.user.roles] and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você não tem permissão para rejeitar solicitações.", ephemeral=True)
            return
        
        await interaction.response.send_message(f"❌ Solicitação rejeitada.", ephemeral=True)
        await self.membro.send(f"❌ **Sua solicitação foi rejeitada pela staff.**")
        self.stop()

class CategorySelect(Select):
    def __init__(self, categorias, nome_canal, membro):
        options = [SelectOption(label=cat.name, value=cat.id) for cat in categorias]
        super().__init__(placeholder="Escolha uma categoria", min_values=1, max_values=1, options=options)
        self.nome_canal = nome_canal
        self.membro = membro

    async def callback(self, interaction: discord.Interaction):
        categoria_id = int(self.values[0])
        categoria = discord.utils.get(interaction.guild.categories, id=categoria_id)
        
        await interaction.guild.create_text_channel(self.nome_canal, category=categoria)
        await interaction.response.send_message(f"✅ Canal `{self.nome_canal}` criado na categoria `{categoria.name}`!", ephemeral=True)
        await self.membro.send(f"✅ **Sua solicitação foi aprovada!** O canal `{self.nome_canal}` foi criado na categoria `{categoria.name}`.")
        self.stop()

@bot.event
async def on_ready():
    print(f'{bot.user} está online!')

@bot.command()
async def criar(ctx, *, nome: str):
    nome_limpo = re.sub(r'[^a-zA-Z0-9- ]', '', nome).replace(' ', '-').lower()
    nome_formatado = f"🔞┇{nome_limpo}"

    canal_solicitacoes = bot.get_channel(SOLICITACAO_CHANNEL_ID)
    if not canal_solicitacoes:
        await ctx.send("🚫 Canal de solicitações não encontrado.")
        return

    async for message in canal_solicitacoes.history(limit=100):
        if nome_formatado in message.content:
            await ctx.send("🚫 Já existe uma solicitação pendente para este nome.")
            return

    categorias = ctx.guild.categories

    embed = discord.Embed(title="Nova Solicitação de Canal", description=f"**Nome do Canal:** {nome_formatado}\n**Solicitado por:** {ctx.author.mention}", color=0xFF5733)
    mensagem = await canal_solicitacoes.send(embed=embed, view=ApprovalView(nome_formatado, ctx.author, categorias))
    await ctx.send(f"📨 Solicitação enviada! Aguarde a aprovação da staff.")
    try:
        await ctx.author.send(f"📨 Sua solicitação para criar o canal `{nome_formatado}` foi enviada com sucesso! Aguarde a aprovação da staff.")
    except discord.Forbidden:
        await ctx.send("⚠️ Não consegui enviar uma mensagem privada para você. Verifique suas configurações de privacidade.")

bot.run(TOKEN)
