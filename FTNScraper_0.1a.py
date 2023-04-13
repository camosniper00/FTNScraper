import re
import aiohttp
import discord
from discord.ext import commands
from bs4 import BeautifulSoup

TOKEN = 'MTA5NTg3ODY1OTYzOTg2OTQ1MA.Gi_Wok.SB-S8-OsvJ9xTmK_s6WFp0oPmqZtj5XWjIvhJM'

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.guild_messages = True
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def parse_html(url):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        soup = BeautifulSoup(html, 'html5lib')
        return soup

async def scrape_pattern_data(url):
    soup = await parse_html(url)
    pattern_links = []

    link_pattern = re.compile(r"Pattern .+")
    for link in soup.find_all("a", class_="list-group-item active", string=link_pattern):
        pattern_links.append((link["href"], link.get_text(strip=True)))

    results = []
    for link, pattern_title in pattern_links:
        next_page_soup = await parse_html(link)
        pricing_plans = next_page_soup.find_all("ul", class_="pricing-plan-details")
        for plan in pricing_plans:
            items = plan.find_all("li")
            result = [pattern_title] + [item.get_text(strip=True) for item in items]
            results.append(result)

    return results

async def send_large_message(ctx, message, max_chars=1900):
    if len(message) <= max_chars + 6:
        await ctx.send(message)
        return

    message_parts = message.split("\n")
    new_message = "```\n"
    for part in message_parts:
        if len(new_message) + len(part) + 1 > max_chars:
            new_message += "```"
            await ctx.send(new_message)
            new_message = "```\n"
        new_message += part + "\n"
    new_message += "```"
    if new_message != "``````":
        await ctx.send(new_message)

@client.command()
async def hello(ctx):
    await ctx.send('Hi')

@client.command()
async def scrape(ctx, url: str):
    try:
        print("Received scrape command")
        scraped_data = await scrape_pattern_data(url)
        print("Scraped data successfully")
        table = "```\n"
        for data in scraped_data:
            row = f"{data[0]}: "
            competitors = ', '.join(data[1:])
            table += row + competitors + "\n"
            table += '-' * (len(row) + len(competitors)) + "\n"
        table += "```"
        await send_large_message(ctx, table)
        print("Sent scraped data to the channel")
    except Exception as e:
        print(f"Error occurred: {e}")
        await ctx.send(f"Error occurred: {e}")

@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")

client.run(TOKEN)