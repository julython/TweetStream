import tweetstream
import requests
import os
import json
import pprint

API_KEY = os.environ.get("API_KEY")
API_URL = 'http://www.julython.org/api/v1/commits'

def callback(message):
    # this will be called every message
    text = message.get('text')
    user = message.get('user')
    screen_name = user.get('screen_name')
    
    print "%s says: %s" % (screen_name, text)

stream = tweetstream.TweetStream()
stream.fetch("/1/statuses/filter.json?track=python", callback=callback)

# if you aren't on a running ioloop...
from tornado.ioloop import IOLoop
IOLoop.instance().start()