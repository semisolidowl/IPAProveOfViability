import os
from flask import Flask, send_from_directory
import threading
import subprocess
import time
from html.parser import HTMLParser
import re
from aiCaller import getAiSummary, getAiQualityFilter
import feedparser
import random
import segno
import datetime
import sqlite3

app = Flask(__name__, static_folder='public', static_url_path='')


class DataEvent(threading.Event):
    def __init__(self):
        super().__init__()
        self.data = None
        self._lock = threading.Lock()

    def set_data(self, data):
        with self._lock:
            self.data = data
            self.set()

    def sleep(self):
        self.wait()
        with self._lock:
            data = self.data
            self.data = None
            self.clear()
        return data


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/getLatestArticle')
def getroute():
    return currentArticle


def open_browser():
    url = 'http://localhost:3000/'
    time.sleep(10)  # Wait for the server to start

    try:
        # Set DISPLAY to :0 explicitly for Linux
        os.environ["DISPLAY"] = ":0"
        subprocess.Popen([
            'chromium-browser', '--kiosk', '--disable-infobars',
            '--no-sandbox', '--disable-session-crashed-bubble', url
        ])
    except Exception as e:
        print(f"Failed to open browser: {e}")


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
    
    def handle_data(self, data):
        self.result.append(data)
    
    def getText(self):
        return ''.join(self.result)


def extractClearText(html_content):
    # Remove scripts, styles, and comments
    # Remove script and style content
    html_content = re.sub(r'(?s)<(script|style).*?>.*?</\1>', '', html_content)
    html_content = re.sub(r'<!--.*?-->', '', html_content)  # Remove comments

    # Use the HTML parser to extract text
    parser = HTMLTextExtractor()
    parser.feed(html_content)
    return parser.getText()


def altArticle(eventReceiver, eventSender):
    eventSender.set_data(
        "SELECT summaries.summaryEng, summaries.title, summaries.url, summaries.publishDate, sources.sourceName FROM summaries INNER JOIN sources on summaries.sources_ID = sources.ROWID ORDER BY summaries.publishDate DESC LIMIT 1;"
    )
    results = eventReceiver.sleep()
    for result in results:
        sumText = result[0]
        clearTitle = result[1]
        url = result[2]
        sourceName = result[4]
        pubDate = datetime.datetime.fromtimestamp(result[3])
        return (sumText, clearTitle, url, pubDate, sourceName)


def aiMainLoop(eventReceiver, eventSender):
    eventSender.set_data("SELECT ROWID, sourceName, rssURL FROM sources")
    rssUrl = eventReceiver.sleep()
    global currentArticle
    # make so that if no artikle found get newest from here and on launch
    storedArticle = altArticle(eventReceiver, eventSender)
    print(storedArticle)
    qrCode = segno.make_qr(storedArticle[2]).svg_data_uri()
    currentArticle = [storedArticle[0],storedArticle[4], storedArticle[1], qrCode]
    oldPublishedTime = storedArticle[3]
    while True:
        articlemade = False
        random.shuffle(rssUrl)

        for randurl in rssUrl:
            rssFeed = feedparser.parse(randurl[2])
            source = randurl[1]
            sourceId = randurl[0]
            print(source)
            print("status_code == 200")
            articleLink = "no article selected"

            for entry in rssFeed.entries:
                try:
                    publishedTime = datetime.datetime(
                        *entry.published_parsed[:6])
                except (AttributeError, TypeError):
                    publishedTime = oldPublishedTime
                    print('not got time')
                    print('Time parsing error: AttributeError',AttributeError, ' TypeError: ', TypeError)
                if publishedTime < oldPublishedTime:
                    continue

                if hasattr(entry, 'content'):
                    print('got content')
                    for content in entry.content:
                        print('one per content')
                        article = content.get('value', '')
                elif hasattr(entry, 'dc_content'):
                    print('got dc_content')
                    article = entry.get('dc_content', '')
                elif 'summary' in entry:
                    print('got summary')
                    article = entry.summary
                else:
                    print('RSS of {source} is not supported')
                    continue
                title = entry.get('title', 'no title found')
                if entry.links:
                    articleLink = entry.links[0].href

                print(len(article))
                if article is not None:
                    print('article is not None')
                    clearTitle = extractClearText(title)
                    clearText = extractClearText(article)

                    if ("true" in getAiQualityFilter(clearText).lower()):
                        print('"true" in getAiQualityFilter(clearText)')
                        oldPublishedTime = publishedTime
                        saveTime = publishedTime.timestamp()
                        sumText = getAiSummary(clearText)
                        eventSender.set_data(('INSERT INTO summaries VALUES(?,?,?,?,?)', (
                            sumText, clearTitle, articleLink, saveTime, sourceId)))
                        qrCode = segno.make_qr(articleLink).svg_data_uri()
                        currentArticle = [sumText, source, clearTitle, qrCode]
                        print(qrCode)
                        articlemade = True
                        input("press key to regenerate") #For Testing
                        #time.sleep(3600)  # Wait for next loop
        if articlemade == False:
            # make so that if no artikle found get newest from here and on launch
            storedArticle = altArticle(eventReceiver, eventSender)
        print(storedArticle)
        qrCode = segno.make_qr(storedArticle[2]).svg_data_uri()
        currentArticle = [storedArticle[0],storedArticle[4], storedArticle[1], qrCode]
        oldPublishedTime = storedArticle[3]


def databaseLoop(eventReceiver, eventSender):
    con = sqlite3.connect('./appDb.db', isolation_level=None)
    cur = con.cursor()

    # Database query processor
    while True:
        data = eventSender.sleep()
        print('this is data: ', data)
        if type(data) == tuple:
            repsonse = cur.execute(data[0], data[1]).fetchall()
        else:
            repsonse = cur.execute(data).fetchall()
        eventReceiver.set_data(repsonse)


if __name__ == '__main__':
    global currentArticle
    eventReceiver = DataEvent()
    eventSender = DataEvent()
    currentArticle = ['No article generated yet.', 'N/A']

    threading.Thread(target=databaseLoop, args=(
        eventReceiver, eventSender)).start()
    threading.Thread(target=open_browser).start()
    threading.Thread(target=aiMainLoop, args=(
        eventReceiver, eventSender)).start()  # todo add argu here
    app.run(port=3000)
