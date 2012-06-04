import tweetstream
import requests
import os
import hmac
import hashlib
import time

API_KEY = os.environ.get("API_KEY")
API_URL = os.environ.get("API_URL", 'http://www.julython.org/api/v1/commits')

def make_digest(message):
    """Somewhat secure way to encode the username for tweets by the client."""
    salt = str(int(time.time()))
    key = ':'.join([salt, API_KEY])
    m = hmac.new(key, message, hashlib.sha256).hexdigest()
    return ':'.join([salt, m])

def callback(message):
    # this will be called every message
    text = message.get('text')
    user = message.get('user')
    screen_name = user.get('screen_name')
    
    #print "%s says: %s" % (screen_name, text)
    message['api_key'] = make_digest(screen_name)
    requests.post(API_URL, message)

stream = tweetstream.TweetStream()
stream.fetch("/1/statuses/filter.json?track=julython", callback=callback)

# if you aren't on a running ioloop...
from tornado.ioloop import IOLoop
IOLoop.instance().start()
