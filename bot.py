import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os

# Ton token de bot Discord
TOKEN = os.getenv("DISCORD_TOKEN")
XIVAPI_KEY = os.getenv("XIVAPI_KEY")
CHANNEL_ID = "1250809808429514868"

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!')

# URL de la section des news en français sur le site Lodestone
LODSTONE_NEWS_URL = 'https://fr.finalfantasyxiv.com/lodestone/news/'

# Stockage de l'ID de la dernière news envoyée pour éviter les doublons
last_news_id = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    check_news.start()

def get_latest_news():
    response = requests.get(LODSTONE_NEWS_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_items = soup.find_all('li', class_='news__list--news')

    latest_news = []
    for item in news_items:
        news_id = item.find('a')['href'].split('/')[-1]
        title = item.find('p', class_='news__list--title').text.strip()
        link = f"https://fr.finalfantasyxiv.com{item.find('a')['href']}"
        latest_news.append((news_id, title, link))

    return latest_news

@tasks.loop(minutes=10)
async def check_news():
    global last_news_id
    channel = bot.get_channel(CHANNEL_ID)
    latest_news = get_latest_news()
    
    if not latest_news:
        return

    latest_news_id, title, link = latest_news[0]

    if last_news_id is None:
        last_news_id = latest_news_id
        return

    if latest_news_id != last_news_id:
        last_news_id = latest_news_id
        await channel.send(f"Nouvelle news sur Lodestone: {title}\n{link}")

bot.run(TOKEN)
