import sqlite3
con = sqlite3.connect("appDb.db")
cur = con.cursor()

for res in cur.execute('PRAGMA foreign_keys;'):
    if res != 1:
        cur.execute('PRAGMA foreign_keys = ON;')
for row in cur.execute('PRAGMA foreign_keys;'):
    print(row)

try:
    cur.execute('''
        CREATE TABLE sources(
            sourceName TEXT NOT NULL, 
            rssUrl TEXT NOT NULL
        )'''
    )
    cur.execute('''
        CREATE TABLE summaries(
            summaryEng TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            publishDate INTEGER NOT NULL,
            sources_ID INTEGER NOT NULL,
            FOREIGN KEY (sources_ID) REFERENCES sources (ROWID)
        )'''
    )
    

except:
    print('Table Already Exists')
res = cur.execute("SELECT name FROM sqlite_master")
print(res.fetchone())

try:
    datas=[
        ('ITpro','https://www.itpro.com/feeds/articletype/news'),
        ('The Verge','https://www.theverge.com/rss/index.xml'),
        ('Ars Technica','https://feeds.arstechnica.com/arstechnica/technology-lab'),
        ('GeekWire','https://www.geekwire.com/feed/')
    ]
    #for data in datas:
    cur.executemany("INSERT INTO Sources VALUES(?, ?)", datas)
    con.commit()

except:
    print ('something happend')

for row in cur.execute("SELECT sourceName, rssUrl FROM sources ORDER BY sourceName"):

    print(row)