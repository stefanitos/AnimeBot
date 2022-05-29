import pymongo
from time import sleep
from bs4 import BeautifulSoup
from dhooks import Webhook
import requests


MONGO_PASS = "1R2TEnOzWjgeKirU"
ANIMELIST = pymongo.MongoClient("mongodb+srv://admin:" + MONGO_PASS + "@cluster0.6m582.mongodb.net/?retryWrites=true&w=majority").get_database("root").get_collection("animelist")

def alert_bot(msg):
    Webhook("https://discord.com/api/webhooks/980545938982584350/_9uI1TfLeXGk6ElTCI4-lNFU75-g1EnPeQAcWit4X_qLNb6mVa6hVukE1q-NBj8hUOwB").send(msg)

def get_latest_episode(anime):
    URL = "https://gogoanime.gg/category/" + anime
    HEADER = ({'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
            'Accept-Language': 'en-US, en;q=0.5'})
    sleep(5)
    html = requests.get(URL, headers=HEADER).text
    ul = BeautifulSoup(html, 'html.parser').find('ul', id='episode_page').find_all("li")
    temp = []
    for item in ul:
        temp.append(item.find("a").text)
    if temp == ['0']:
        return 0
    elif temp.__len__() > 1:
        return int(temp[-1].split("-")[1])
    else:
        return int(temp[0].split("-")[1])


def job():
    while True:
        print("Checking for new episodes...")
        data = ""
        for anime in ANIMELIST.find():
            name = anime["anime"]
            latest_ep = get_latest_episode(name)
            current_ep = anime["latest"] - 1 
            if latest_ep > current_ep:
                data += " " + name
                ANIMELIST.update_one({"anime": name}, {"$set": {"latest": latest_ep}})
        if data != "":
            alert_bot("NEW_EPS" + data)
        sleep(10)
job()