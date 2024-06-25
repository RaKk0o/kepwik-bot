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
                    # Extrait le résumé et l'image ici, si disponible
                    summary = item.find_next('div', class_='news__list--content').text.strip() if item.find_next('div', class_='news__list--content') else "Pas de résumé disponible."
                    image = item.find_next('img')['src'] if item.find_next('img') else None
                    time_tag = item.find_next('time')
                    date = time_tag.find('span').text if time_tag and time_tag.find('span') else None
                    latest_news.append((news_id, tag.text.strip('[]'), title, summary, link, image, date))
        except AttributeError:
            continue  # Ignore les éléments mal formés

    return latest_news

async def send_news_embed(channel, news):
    for news_id, tag, title, summary, link, image, date in news:
        embed = discord.Embed(title=title, description=summary, url=link)
        embed.set_author(name=tag)
        if image:
            embed.set_image(url=image)
        if date and date != '-':
            date_obj = datetime.strptime(date, '%d.%m.%Y')
            embed.timestamp = date_obj
            embed.set_footer(text=f"Publié le {date_obj.strftime('%d %b %Y %H:%M')}")
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