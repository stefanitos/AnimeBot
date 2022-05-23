from email import header
from wsgiref.headers import Headers
from discord.ext import commands
import discord
import aiohttp
import pymongo
from bs4 import BeautifulSoup


bot = commands.Bot(command_prefix="'", case_insensitive=True)
MONGO_PASS = "1R2TEnOzWjgeKirU"
ANIM_PASS = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjE4NzIiLCJuYmYiOjE2NTMzMDA0MDgsImV4cCI6MTY1NTg5MjQwOCwiaWF0IjoxNjUzMzAwNDA4fQ.svdzbWv2s5Ju3HPJ4X0UaDcYjbD1jtNvqz5aDmJSc6I"
root = pymongo.MongoClient("mongodb+srv://admin:" + MONGO_PASS + "@cluster0.6m582.mongodb.net/?retryWrites=true&w=majority").get_database("root")
GUILDS = []


@bot.event
async def on_ready():
    for guild in bot.guilds:
        GUILDS.append(guild.id)
    print(GUILDS)


@bot.command()
async def anime(ctx, *, anime):
    if root.get_collection("users").find_one({"id": ctx.author.id}) == None:
        user = {"user_id": ctx.author.id, "anime_list": []}
        root.get_collection("users").insert_one(user)

    if anime.split(" ")[1].lower() == "add":
        url = 'https://gogoanime.sk/search.html?keyword='

        async with aiohttp.ClientSession() as session:
            async with session.get(url + anime) as response:
                data = await response.text()

        soup = BeautifulSoup(data, 'html.parser')
        results = soup.findall('div', class='last_episodes')[0]
        list = []

        for anime in results.find_all('img', src=True):
            href = anime['src'].split('https://gogocdn.net/cover/%27)[1].split(%27.%27)[0]
            list.append(href)

        # embed



bot.run('NjI1MzE5NjU4NjQ3NDUzNzE3.GfsL5h.7KgA2DfdCnrhL1BCZCHkqwn0dJzZUj5l_ZdRCg')
