import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

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
    news_items = soup.find_all('div', class_='news__list--banner')

    latest_news = []
    for item in news_items:
        try:
            link_tag = item.find('a', class_='news__list--img')
            title_tag = item.find('p', class_='news__list--title')
            if link_tag and title_tag:
                link = f"https://fr.finalfantasyxiv.com{link_tag['href']}"
                image = link_tag.find('img')['src'] if link_tag.find('img') else None
                title = title_tag.text.strip()
                summary = item.find('p', class_='mdl-text__xs-m16').text.strip() if item.find('p', class_='mdl-text__xs-m16') else "Pas de résumé disponible."
                date_tag = item.find('time')
                date = date_tag.find('span').text if date_tag and date_tag.find('span') else None
                latest_news.append((link, title, summary, image, date))
        except AttributeError:
            continue  # Ignore les éléments mal formés

    return latest_news

async def send_news_embed(channel, news):
    for link, title, summary, image, date in news:
        embed = discord.Embed(title=title, description=summary, url=link)
        if image:
            embed.set_image(url=image)
        if date and date != '-':
            try:
                date_obj = datetime.strptime(date, '%d.%m.%Y')
                embed.timestamp = date_obj
                embed.set_footer(text=f"Publié le {date_obj.strftime('%d %b %Y %H:%M')}")
            except ValueError:
                embed.set_footer(text=f"Date : {date}")
        else:
            embed.set_footer(text="Date non disponible")
        await channel.send(embed=embed)

@tasks.loop(minutes=10)
async def check_news():
    global last_news_id
    channel = bot.get_channel(CHANNEL_ID)
    latest_news = get_latest_news()
    
    if not latest_news:
        return

    if last_news_id is None:
        last_news_id = latest_news[0][0]
        return

    new_news = []
    for news in latest_news:
        if news[0] == last_news_id:
            break
        new_news.append(news)

    if new_news:
        last_news_id = new_news[0][0]
        await send_news_embed(channel, new_news)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! Le bot est en ligne et fonctionne correctement.')

@bot.command()
async def news(ctx):
    latest_news = get_latest_news()
    if not latest_news:
        await ctx.send("Aucune nouvelle trouvée.")
        return
    
    await send_news_embed(ctx.channel, latest_news[:5])

bot.run(TOKEN)