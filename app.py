from discord.ext import commands
from time import sleep
import aiohttp
import pymongo
from bs4 import BeautifulSoup
import asyncio


bot = commands.Bot(command_prefix="'", case_insensitive=True)
MONGO_PASS = "1R2TEnOzWjgeKirU"
ANIM_PASS = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjE4NzIiLCJuYmYiOjE2NTMzMDA0MDgsImV4cCI6MTY1NTg5MjQwOCwiaWF0IjoxNjUzMzAwNDA4fQ.svdzbWv2s5Ju3HPJ4X0UaDcYjbD1jtNvqz5aDmJSc6I"
ROOT = pymongo.MongoClient("mongodb+srv://admin:" + MONGO_PASS + "@cluster0.6m582.mongodb.net/?retryWrites=true&w=majority").get_database("root").get_collection("users")


@bot.event
async def on_ready():
    print("Bot is ready")


@bot.command()
async def add(ctx,*,animename):
    """Adds an anime to your anime list"""
    check_user(ctx.author)

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
        for elements in results:
            animelist.append(elements.find("a")["href"].split("/category/")[1])
        
        for anime in animelist:
            animestring += str(counter) + ") " + anime + "\n"
            counter += 1
        
        if animestring == "":
            await firstmsg.edit(content="No anime found with title: " + animename)
        else:
            await firstmsg.edit(content="***Found the following anime:***\n" + animestring)
        
            secondmsg = await ctx.send("\nPlease enter the number of the anime you would like to add")
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
            try:
                msg = await bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await secondmsg.edit(content="Timed out")
                return
            else:
                num = int(msg.content) - 1
                anime = animelist[num]

                if anime in ROOT.find_one({"id": ctx.author.id})["anime_list"]:
                    await secondmsg.edit(content="***Anime already in list***")
                    return
                else:
                    URL = "https://gogoanime.gg/category/" + anime
                    HEADER = ({'User-Agent':
                            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
                            'Accept-Language': 'en-US, en;q=0.5'})
                    async with aiohttp.ClientSession() as session:
                        async with session.get(URL, headers=HEADER) as response:
                            data = await response.text()
                    ul = BeautifulSoup(data, 'html.parser').find('ul', id='episode_page').find_all("li")
                    temp = []
                    latest = 0
                    for item in ul:
                        temp.append(item.find("a").text)
                    if temp == ['0']:
                        return
                    elif temp.__len__() > 1:
                        latest = int(temp[-1].split("-")[1])
                    else:
                        latest = int(temp[0].split("-")[1])
                    
                    ROOT.update_one({"id": ctx.author.id}, {"$push": {"anime_list": [anime,latest]}})
                    await secondmsg.edit(content="***Anime : " + anime + " added to list!***")

@bot.command()
async def list(ctx,*args):
    """Lists all your anime or someone elses by passing their userid as an argument"""
    check_user(ctx.author)
    user_name = ctx.author.name
    user_id = ctx.author.id

    if not args.__len__() == 0:
        user_name = get_user_name(int(args[0]))
        user_id = int(args[0])

    if ROOT.find_one({"id": user_id})["anime_list"] == []:
        await ctx.send("***" + user_name + "'s Anime List Is Empty!***\n*'add <anime name> to add an anime*")
    else:
        anime_list = ROOT.find_one({"id": user_id})["anime_list"]
        animestring = ""
        for anime in anime_list:
            animestring += anime[0] + "\n"
        await ctx.send("***" + user_name + "'s Anime List:***\n" + animestring)


@bot.command()
async def remove(ctx):
    """Removes an anime from your anime list"""
    check_user(ctx.author)
    if ROOT.find_one({"id": ctx.author.id})["anime_list"] == []:
        await ctx.send("***" + ctx.author.name + "'s Anime List Is Empty!***\n*'add <anime name> to add an anime*")
    else:
        anime_list = ROOT.find_one({"id": ctx.author.id})["anime_list"]
        animestring = ""
        for anime in anime_list:
            animestring += anime[0] + "\n"
        await ctx.send("***" + ctx.author.name + "'s Anime List:***\n" + animestring)
        await ctx.send("Please enter the number of the anime you would like to remove")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Timed out")
            return
        else:
            num = int(msg.content) - 1
            anime = anime_list[num]

            anime_list = ROOT.find_one({"id": ctx.author.id})["anime_list"]

            ROOT.update_one({"id": ctx.author.id}, {"$pull": {"anime_list": anime}})
            await ctx.send("***Anime : " + anime[0] + " removed from list!***")


def check_user(user):
    if ROOT.find_one({"id": user.id}) == None:
        print("Creating user: " + user.name)
        ROOT.insert_one({"id": user.id, "anime_list": [],"name" : user.name})

    if ROOT.find_one({"id": user.id})["name"] == None or ROOT.find_one({"id": user.id})["name"] != user.name:
        print("Updating name: " + user.name)
        ROOT.update_one({"id": user.id}, {"$set": {"name" : user.name}})

def get_user_name(id):
    return ROOT.find_one({"id": id})["name"]

bot.run('NjI1MzE5NjU4NjQ3NDUzNzE3.GfsL5h.7KgA2DfdCnrhL1BCZCHkqwn0dJzZUj5l_ZdRCg')
