from turtle import st
from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound
from time import sleep
from bs4 import BeautifulSoup
from dhooks import Webhook
from dotenv import dotenv_values
import asyncio
import discord
import speedtest
import pymongo
import aiohttp


intents = discord.Intents.default()
intents.members = True

envs = dotenv_values(".env")

BOT_TOKEN = envs["BOT_TOKEN"]
MONGO_PASS = envs["MONGO_PASS"]
LOG_WEBHOOK = envs["LOG_HOOK"]
bot = commands.Bot(command_prefix="'", case_insensitive=True, intents=intents)
ROOT = pymongo.MongoClient("mongodb+srv://admin:" + MONGO_PASS +
                           "@cluster0.6m582.mongodb.net/?retryWrites=true&w=majority").get_database("root").get_collection("users")
ANIMELIST = pymongo.MongoClient("mongodb+srv://admin:" + MONGO_PASS +
                                "@cluster0.6m582.mongodb.net/?retryWrites=true&w=majority").get_database("root").get_collection("animelist")
debug = True


@bot.event
async def on_command_error(error):
    if isinstance(error, CommandNotFound):
        return
    raise error


@bot.command()
async def speed(ctx):
    """Speed test"""
    msg = await ctx.send("Running speed test...")
    st = speedtest.Speedtest()
    st.get_best_server()
    st.download()
    st.upload()
    await msg.edit(content="Download: " + humansize(st.results.download) + "/s\nUpload: " + humansize(st.results.upload) + "/s\nPing: " + str(st.results.ping) + "ms")


@bot.event
async def on_ready():
    print("Bot is ready!")
    if not debug:
        await check_for_new_episodes.start()


@bot.command()
async def ping(ctx):
    await ctx.send("***" + str(bot.latency) + " seconds***")


@tasks.loop(seconds=600)
async def check_for_new_episodes():
    guild = bot.get_guild(979703279539863562)
    send_to_log("Checking for new episodes...")
    data = []
    for anime in ANIMELIST.find():
        name = anime["anime"]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://gogoanime.sk/category/" + name) as resp:
                    html = await resp.text()
            ul = BeautifulSoup(html, 'html.parser')

            items = ul.find('ul', id='episode_page').find_all("li")
            temp = []
 
            try:
                status = ul.find('a', {'title': 'Completed Anime'})
                if status.text == "Completed":
                    send_to_log("Anime " + name + " is completed!")
                    for user in anime["users"]:
                        channel = bot.fetch_channel(str(user))
                        await channel.send("Anime " + name + " is completed!\nRemoving from your list...")
                        ANIMELIST.update_one({"anime": name, "users": user}, {"$pull": {"users": user}})
                    ANIMELIST.delete_one({"anime": name})
            except:
                pass

            for item in items:
                temp.append(item.find("a").text)

            if temp == ['0']:
                break
            elif temp.__len__() > 1:
                latest_ep = int(temp[-1].split("-")[1])
            else:
                latest_ep = int(temp[0].split("-")[1])

            current_ep = anime["latest"]
            if latest_ep > current_ep:
                data.append(name)
                ANIMELIST.update_one(
                    {"anime": name}, {"$set": {"latest": latest_ep}})
        except:
            raise Exception("Error getting latest episode")
    if data != []:
        for anime in data:
            ids = ANIMELIST.find_one({"anime": anime})["users"]
            latest = ANIMELIST.find_one({"anime": anime})["latest"]
            for id in ids:
                channel = discord.utils.get(guild.text_channels, name=str(id))
                if channel != None:
                    print("Sending message to " +
                          get_user_name(id) + " about " + anime)
                    await channel.send("||<@" + str(id) + ">||\nNew episode of " + anime + "!\n" + "New episode: " + str(latest))


@bot.event
async def on_member_join(member):
    check_user(member.author)
    server = bot.get_guild(979703279539863562)
    if member.guild.id == 979703279539863562:
        print("User " + member.name + " joined the server!")
        role = discord.utils.get(server.roles, name=str(member.id))
        if role == None:
            role = await server.create_role(name=str(member.id), mentionable=True)
            new_channel = await server.create_text_channel(name=str(member.id))
            await new_channel.set_permissions(role, read_messages=True, send_messages=True, read_message_history=True)
            await new_channel.set_permissions(server.default_role, read_messages=False)
        await member.add_roles(role)
        channel = discord.utils.get(server.text_channels, name=str(member.id))
        await channel.send("Welcome to the Anime Notifier!\nTo get started, type `'help` in this channel!")


@bot.command()
async def add(ctx, *animename):
    """'add <anime name> - Adds an anime to your list"""
    check_user(ctx.author)
    if animename.__len__() == 0:
        await ctx.send("Please specify an anime name")
        return
    anime_name = " ".join(animename)
    firstmsg = await ctx.send("Searching for anime...")
    url = 'https://gogoanime.sk/search.html?keyword='
    async with aiohttp.ClientSession() as session:
        async with session.get(url + anime_name) as response:
            data = await response.text()
            session.close()
    soup = BeautifulSoup(data, 'html.parser')
    results = soup.find_all("p", {"class": "name"})
    animelist = []
    for elements in results:
        animelist.append(elements.find("a")["href"].split("/category/")[1])

    animestring = arrToNumString(animelist)

    if animestring == "":
        await firstmsg.edit(content="No anime found with title: " + anime_name)
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
            anime = animelist[int(msg.content) - 1]

            if anime in ROOT.find_one({"id": ctx.author.id})["anime_list"]:
                await secondmsg.edit(content="***Anime already in list***")
            else:
                try:
                    soup.find('a', {'title': 'Completed Anime'})
                    await secondmsg.edit(content="***Anime is not currently airing!***")
                except:
                    URL = "https://gogoanime.sk/category/" + anime
                    HEADER = ({'User-Agent':
                               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
                               'Accept-Language': 'en-US, en;q=0.5'})
                    async with aiohttp.ClientSession() as session:
                        async with session.get(URL, headers=HEADER) as response:
                            data = await response.text()
                    ul = BeautifulSoup(data, 'html.parser').find(
                        'ul', id='episode_page').find_all("li")
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
                    ROOT.update_one({"id": ctx.author.id}, {
                                    "$push": {"anime_list": anime}})
                    if ANIMELIST.find_one({"anime": anime}) == None:
                        ANIMELIST.insert_one(
                            {"anime": anime, "users": [ctx.author.id], "latest": latest})
                    else:
                        ANIMELIST.update_one({"anime": anime}, {
                                             "$push": {"users": ctx.author.id}})
                    await secondmsg.edit(content="***Anime : " + anime + " added to list!***")


@bot.command()
async def list(ctx, *args):
    """Lists all your anime or someone elses ('list <user id>)"""
    check_user(ctx.author)

    if not args.__len__() == 0:
        user_name = get_user_name(int(args[0]))
        user_id = int(args[0])
    else:
        user_name = ctx.author.name
        user_id = ctx.author.id

    anime_list = ROOT.find_one({"id": user_id})["anime_list"]

    if anime_list == []:
        await ctx.send("***No anime in list***")

    animestring = ""
    for anime in anime_list:
        animestring += anime + "\n"
    await ctx.send("***" + user_name + "'s Anime List:***\n" + animestring)


@bot.command()
async def remove(ctx):
    """'remove - Removes an anime from your list"""
    check_user(ctx.author)
    if ROOT.find_one({"id": ctx.author.id})["anime_list"] == []:
        await ctx.send("***" + ctx.author.name + "'s Anime List Is Empty!***\n*'add <anime name> to add an anime*")
    else:
        anime_list = ROOT.find_one({"id": ctx.author.id})["anime_list"]
        animestring = arrToNumString(anime_list)
        await ctx.send("***" + ctx.author.name + "'s Anime List:***\n" + animestring)
        firstmsg = await ctx.send("Please enter the number of the anime you would like to remove")

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

            ROOT.update_one({"id": ctx.author.id}, {
                            "$pull": {"anime_list": anime}})
            if ANIMELIST.find_one({"anime": anime})["users"].__len__() == 1:
                ANIMELIST.delete_one({"anime": anime})
            else:
                ANIMELIST.update_one({"anime": anime}, {
                                     "$pull": {"users": ctx.author.id}})
            await firstmsg.edit(content="***Anime : " + anime + " removed from list!***")


def check_user(user):
    if ROOT.find_one({"id": user.id}) == None:
        print("Creating user: " + user.name)
        ROOT.insert_one({"id": user.id, "anime_list": [], "name": user.name})

    if ROOT.find_one({"id": user.id})["name"] == None or ROOT.find_one({"id": user.id})["name"] != user.name:
        print("Updating name: " + user.name)
        ROOT.update_one({"id": user.id}, {"$set": {"name": user.name}})


def get_user_name(id):
    return ROOT.find_one({"id": id})["name"]


def humansize(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def arrToNumString(array):
    numlist = ""
    i = 1
    for item in array:
        numlist += str(i) + ")" + str(item)
        i += 1
    return numlist
        

def send_to_log(message):
    Webhook(LOG_WEBHOOK).send(message)


bot.run(BOT_TOKEN)
