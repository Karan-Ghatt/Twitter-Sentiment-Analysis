## Access Token: 188359243-nlVItKcmsLHtvXXEkj44IRCGYxRKJLP18z5lXHaM ##
## Access Token Secret: eVqYu637x7syOGYYgMwzDCkBuJwYn7n4tktRSWR3u8oWv ##

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
import sqlite3
from unidecode import unidecode
from textblob import TextBlob
import time



conn = sqlite3.connect('twitter.db')
c = conn.cursor()

ckey="Pd3gS1daX35hbb4J5cDT23TKF"
csecret="ZLu88Qa1AWeuiihv6reUwz6CGoatck1HYeJN1MWuduhLKYo1fN"
atoken="188359243-nlVItKcmsLHtvXXEkj44IRCGYxRKJLP18z5lXHaM"
asecret="eVqYu637x7syOGYYgMwzDCkBuJwYn7n4tktRSWR3u8oWv"

def create_table():
    try:
        c.execute("CREATE TABLE IF NOT EXISTS sentiment(unix REAL, tweet TEXT, sentiment REAL,"
                  " id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL)")
        c.execute("CREATE INDEX fast_unix ON sentiment(unix)")
        c.execute("CREATE INDEX fast_tweet ON sentiment(tweet)")
        c.execute("CREATE INDEX fast_sentiment ON sentiment(sentiment)")
        c.execute("CREATE INDEX id_unix ON sentiment (id DESC, unix DESC)")
        c.execute(
            "CREATE VIRTUAL TABLE sentiment_fts USING fts5(tweet, content=sentiment, content_rowid=id, prefix=1, prefix=2, prefix=3)")
        # that trigger will automagically update out table when row is interted
        # (requires additional triggers on update and delete)
        c.execute("""
                    CREATE TRIGGER sentiment_insert AFTER INSERT ON sentiment BEGIN
                        INSERT INTO sentiment_fts(rowid, tweet) VALUES (new.id, new.tweet);
                    END
                """)
    except Exception as e:
        print(str(e))
create_table()



class listener(StreamListener):

    def on_data(self, data):
        try:
            data = json.loads(data)
            tweet = unidecode(data['text'])
            time_ms = data['timestamp_ms']

            analysis = TextBlob(tweet)
            sentiment = analysis.sentiment.polarity

            print(time_ms, tweet, sentiment)
            c.execute("INSERT INTO sentiment (unix, tweet, sentiment) VALUES (?, ?, ?)",
                  (time_ms, tweet, sentiment))
            conn.commit()

        except KeyError as e:
            print(str(e))
        return(True)

    def on_error(self, status):
        print(status)


while True:

    try:
        auth = OAuthHandler(ckey, csecret)
        auth.set_access_token(atoken, asecret)
        twitterStream = Stream(auth, listener())
        twitterStream.filter(track=["a","e","i","o","u"])
    except Exception as e:
        print(str(e))
        time.sleep(5)