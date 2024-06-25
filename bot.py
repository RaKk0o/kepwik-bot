import discord
from discord.ext import commands
from pyxivapi import XIVAPIClient
import asyncio

# Ton token de bot Discord
TOKEN = 'ton_token_discord'
XIVAPI_KEY = 'ta_clé_api'

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

async def fetch_character(character_id):
    client = XIVAPIClient(api_key=XIVAPI_KEY)
    character = await client.character_by_id(character_id)
    await client.session.close()
    return character

@bot.command()
async def character(ctx, character_id: int):
    character = await fetch_character(character_id)
    if character:
        name = character['Character']['Name']
        server = character['Character']['Server']
        await ctx.send(f'Character: {name} from {server}')
    else:
        await ctx.send('Character not found.')

bot.run(TOKEN)
