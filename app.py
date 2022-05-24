from discord.ext import commands
import aiohttp
import pymongo
from bs4 import BeautifulSoup
import asyncio


bot = commands.Bot(command_prefix="'", case_insensitive=True)
MONGO_PASS = "1R2TEnOzWjgeKirU"
ANIM_PASS = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjE4NzIiLCJuYmYiOjE2NTMzMDA0MDgsImV4cCI6MTY1NTg5MjQwOCwiaWF0IjoxNjUzMzAwNDA4fQ.svdzbWv2s5Ju3HPJ4X0UaDcYjbD1jtNvqz5aDmJSc6I"
GUILDS = []


@bot.event
async def on_ready():
    print("Bot is ready")


@bot.command()
async def anime(ctx,command,*anime_title):
    animename = list(anime_title)
    animename = ' '.join(animename)

    root = pymongo.MongoClient("mongodb+srv://admin:" + MONGO_PASS + "@cluster0.6m582.mongodb.net/?retryWrites=true&w=majority").get_database("root")

    if root.get_collection("users").find_one({"id": ctx.author.id}) == None:
        user = {"id": ctx.author.id, "anime_list": []}
        root.get_collection("users").insert_one(user)

    if command == "add":
        if animename == "":
            await ctx.send("Please enter an anime name")
        else:
            firstmsg = await ctx.send("Searching for anime...")
            url = 'https://gogoanime.sk/search.html?keyword='

            async with aiohttp.ClientSession() as session:
                async with session.get(url + animename) as response:
                    data = await response.text()

            soup = BeautifulSoup(data, 'html.parser')
            results = soup.find_all("p",{"class": "name"})
            animelist = []
            animestring = ""
            counter = 1

            for i in results:
                animelist.append(i.find("a")["href"].split("/category/")[1])
            
            for anime in animelist:
                animestring += str(counter) + ") " + anime + "\n"
                counter += 1
            
            if animestring == "":
                await firstmsg.edit(content="No anime found with title: " + animename)
            else:
                await firstmsg.edit(content="***Found the following anime:***\n" + animestring)
            
            secondmsg = await ctx.send("Please enter the number of the anime you would like to add")

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

            try:
                msg = await bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await secondmsg.edit(content="Timed out")
                return
            else:
                num = int(msg.content) - 1
                if num < 1 or num > len(animelist):
                    await secondmsg.edit(content="Please enter a valid number")
                    return
                else:
                    anime = animelist[num]
                    if anime in root.get_collection("users").find_one({"id": ctx.author.id})["anime_list"]:
                        await secondmsg.edit(content="***Anime already in list***")
                        return
                    else:
                        root.get_collection("users").update_one({"id": ctx.author.id}, {"$push": {"anime_list": anime}})
                        await secondmsg.edit(content="***Anime added!***")
                        return

                


bot.run('NjI1MzE5NjU4NjQ3NDUzNzE3.GfsL5h.7KgA2DfdCnrhL1BCZCHkqwn0dJzZUj5l_ZdRCg')
