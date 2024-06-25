import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os

# Ton token de bot Discord
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1250809808429514868  # Remplace par l'ID du canal où tu veux envoyer les news

# Spécifier les intentions
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# URL de la section des news en français sur le site Lodestone
LODSTONE_NEWS_URL = 'https://fr.finalfantasyxiv.com/lodestone/news/'

# Stockage de l'ID de la dernière news envoyée pour éviter les doublons
last_news_id = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    check_news.start()

def get_latest_news():
    try:
        response = requests.get(LODSTONE_NEWS_URL)
        response.raise_for_status()  # Vérifie si la requête a réussi
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des nouvelles: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    news_items = soup.find_all('p', class_='news__list--title')

    latest_news = []
    for item in news_items:
        try:
            tag = item.find('span', class_='news__list--tag')
            if tag:
                title = item.text.replace(tag.text, '').strip()
                link_tag = item.find_parent('a')
                if link_tag:
                    link = f"https://fr.finalfantasyxiv.com{link_tag['href']}"
                    news_id = link.split('/')[-1]
                    latest_news.append((news_id, title, link))
        except AttributeError:
            continue  # Ignore les éléments mal formés

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

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! Le bot est en ligne et fonctionne correctement.')

@bot.command()
async def news(ctx):
    latest_news = get_latest_news()
    if not latest_news:
        await ctx.send("Aucune nouvelle trouvée.")
        return
    
    news_message = "Voici les 5 dernières nouvelles sur Lodestone :\n\n"
    for news in latest_news[:5]:
        news_id, title, link = news
        news_message += f"{title}\n{link}\n\n"
    
    await ctx.send(news_message)

bot.run(TOKEN)