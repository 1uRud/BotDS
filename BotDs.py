import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# === Загрузка .env ===
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN отсутствует в .env")
if not GUILD_ID:
    raise ValueError("❌ GUILD_ID отсутствует в .env")
if not SPREADSHEET_ID:
    raise ValueError("❌ SPREADSHEET_ID отсутствует в .env")

GUILD_ID = int(GUILD_ID)

# === Инициализация бота (обязательно ДО команд!) ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# === Google Sheets setup ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    CREDS = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    CLIENT = gspread.authorize(CREDS)
    SHEET = CLIENT.open_by_key(SPREADSHEET_ID).sheet1
except Exception as e:
    print(f"❌ Ошибка подключения к Google Таблице: {e}")
    SHEET = None

def log_to_sheet(author: str, category: str, data: dict):
    """Записывает данные в Google Таблицу"""
    if SHEET is None:
        print("⚠️ Google Таблица не подключена — пропускаем запись.")
        return

    row = [
        author,                          # Автор (ник)
        category,                        # Категория
        data.get("name", ""),            # Название
        data.get("difficulty", ""),      # Сложность (локация)
        data.get("description", ""),     # Описание
        data.get("mobs", ""),            # Мобы
        data.get("loot", ""),            # Лут (локация или моб)
        data.get("hp", ""),              # Здоровье (моб)
        data.get("damage", ""),          # Урон (моб/оружие)
        data.get("item_type", "") or data.get("weapon_type", ""),  # Тип
        data.get("rarity", ""),          # Редкость (оружие)
        data.get("effects", ""),         # Эффекты (оружие)
        data.get("value", ""),           # Стоимость (лут)
        data.get("source", ""),          # Источник (лут)
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Дата
    ]
    try:
        SHEET.append_row(row)
    except Exception as e:
        print(f"❌ Ошибка записи в таблицу: {e}")

# =============== МОДАЛЬНЫЕ ФОРМЫ ===============

class LocationModal(ui.Modal, title="Создать локацию"):
    name = ui.TextInput(label="Название локации", placeholder="Пещера Смерти")
    difficulty = ui.TextInput(label="Сложность", placeholder="1–10")
    description = ui.TextInput(label="Описание", style=discord.TextStyle.long)
    mobs = ui.TextInput(label="Мобы на локации", placeholder="Гоблин, Огр")
    loot = ui.TextInput(label="Лут на локации", placeholder="Зелье, Ключ")

    async def on_submit(self, interaction: Interaction):
        data = {
            "name": self.name.value,
            "difficulty": self.difficulty.value,
            "description": self.description.value,
            "mobs": self.mobs.value,
            "loot": self.loot.value
        }
        log_to_sheet(str(interaction.user), "Локация", data)
        embed = discord.Embed(title=f"📍 Локация: {data['name']}", color=0x00ff00)
        embed.add_field(name="Сложность", value=data["difficulty"], inline=False)
        embed.add_field(name="Описание", value=data["description"], inline=False)
        embed.add_field(name="Мобы", value=data["mobs"], inline=False)
        embed.add_field(name="Лут", value=data["loot"], inline=False)
        await interaction.response.send_message(embed=embed)


class MobModal(ui.Modal, title="Создать моба"):
    name = ui.TextInput(label="Имя моба")
    appearance = ui.TextInput(label="Внешность", style=discord.TextStyle.long)
    hp = ui.TextInput(label="Здоровье (HP)")
    damage = ui.TextInput(label="Урон")
    drops = ui.TextInput(label="Лут с моба", placeholder="Кожа, Золото")

    async def on_submit(self, interaction: Interaction):
        data = {
            "name": self.name.value,
            "description": self.appearance.value,
            "hp": self.hp.value,
            "damage": self.damage.value,
            "loot": self.drops.value
        }
        log_to_sheet(str(interaction.user), "Моб", data)
        embed = discord.Embed(title=f"👹 Моб: {data['name']}", color=0xff5500)
        embed.add_field(name="Внешность", value=data["description"], inline=False)
        embed.add_field(name="HP", value=data["hp"], inline=True)
        embed.add_field(name="Урон", value=data["damage"], inline=True)
        embed.add_field(name="Лут", value=data["loot"], inline=False)
        await interaction.response.send_message(embed=embed)


class WeaponModal(ui.Modal, title="Создать оружие"):
    name = ui.TextInput(label="Название оружия", placeholder="Меч Пламени")
    weapon_type = ui.TextInput(label="Тип оружия", placeholder="Меч, Лук, Посох")
    damage = ui.TextInput(label="Урон")
    rarity = ui.TextInput(label="Редкость", placeholder="Обычное, Редкое, Эпик")
    effects = ui.TextInput(label="Эффекты", style=discord.TextStyle.long, placeholder="Поджигает, Отбрасывает")

    async def on_submit(self, interaction: Interaction):
        data = {
            "name": self.name.value,
            "weapon_type": self.weapon_type.value,
            "damage": self.damage.value,
            "rarity": self.rarity.value,
            "effects": self.effects.value
        }
        log_to_sheet(str(interaction.user), "Оружие", data)
        embed = discord.Embed(title=f"⚔️ Оружие: {data['name']}", color=0xffd700)
        embed.add_field(name="Тип", value=data["weapon_type"], inline=True)
        embed.add_field(name="Урон", value=data["damage"], inline=True)
        embed.add_field(name="Редкость", value=data["rarity"], inline=False)
        embed.add_field(name="Эффекты", value=data["effects"], inline=False)
        await interaction.response.send_message(embed=embed)


class LootModal(ui.Modal, title="Создать лут"):
    name = ui.TextInput(label="Название предмета")
    item_type = ui.TextInput(label="Тип", placeholder="Вещь / Расходник")
    value = ui.TextInput(label="Стоимость (в монетах)")
    source = ui.TextInput(label="С кого падает", placeholder="Гоблин, Сундук")

    async def on_submit(self, interaction: Interaction):
        data = {
            "name": self.name.value,
            "item_type": self.item_type.value,
            "value": self.value.value,
            "source": self.source.value
        }
        log_to_sheet(str(interaction.user), "Лут", data)
        embed = discord.Embed(title=f"💎 Лут: {data['name']}", color=0x00aaff)
        embed.add_field(name="Тип", value=data["item_type"], inline=True)
        embed.add_field(name="Стоимость", value=data["value"], inline=True)
        embed.add_field(name="Источник", value=data["source"], inline=False)
        await interaction.response.send_message(embed=embed)

# =============== КОМАНДЫ ===============

@bot.tree.command(name="локация", description="Создать описание локации")
async def cmd_location(interaction: Interaction):
    await interaction.response.send_modal(LocationModal())

@bot.tree.command(name="моб", description="Создать описание моба")
async def cmd_mob(interaction: Interaction):
    await interaction.response.send_modal(MobModal())

@bot.tree.command(name="оружие", description="Создать описание оружия")
async def cmd_weapon(interaction: Interaction):
    await interaction.response.send_modal(WeaponModal())

@bot.tree.command(name="лут", description="Создать описание лута")
async def cmd_loot(interaction: Interaction):
    await interaction.response.send_modal(LootModal())

# =============== ЗАПУСК ===============

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} успешно запущен!')
    guild = discord.Object(id=GUILD_ID)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f'🔁 Синхронизировано {len(synced)} команд для сервера {GUILD_ID}')
    except Exception as e:
        print(f'❌ Ошибка синхронизации: {e}')

# Запуск бота
bot.run(TOKEN)