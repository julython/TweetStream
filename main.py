import tweetstream
import requests
import os
import hmac
import hashlib
import time
import json
from urlparse import urlparse

API_KEY = os.environ.get("API_KEY")
API_URL = os.environ.get("API_URL", 'http://www.julython.org/api/v1/')
TWITTER_APP_USER = os.environ.get("TWITTER_APP_USER")
TWITTER_APP_PASSWORD = os.environ.get("TWITTER_APP_PASSWORD")
KNOWN_REPOS = [
    'github.com',
    'bitbucket.org'
]

def make_digest(message):
    """Somewhat secure way to encode the username for tweets by the client."""
    salt = str(int(time.time()))
    key = ':'.join([salt, API_KEY])
    m = hmac.new(key, message, hashlib.sha256).hexdigest()
    return ':'.join([salt, m])

def callback(message):
    """
    Tweet Callback
    
    Parse the message and create entries on jultyhon.org
    """
    
    text = message.get('text')
    entities = message.get('entities')
    urls = entities.get('urls')
    hashtags = entities.get('hashtags')
    user = message.get('user')
    screen_name = user.get('screen_name')
    tid = message.get('id')
    key = make_digest(screen_name)
    
    # parse any urls for repositories create 
    for url in urls:
        # TODO: can this be done asynchronous?
        parse_url(url, screen_name, text, hashtags, tid, key)

    # send the message over
    message['api_key'] = key
    requests.post(API_URL + 'commits', message)

def parse_url(url, screen_name, text, hashtags, tid, key):
    """
    Parse the urls from the tweet and see if any are repositories
    that we know how to parse and create a new project for the person.
    
    Args:
        * url: URL dict from tweet
        * screen_name: screen name of the user
        * text: text of the message
        * hashtags: hashtags from the tweet, used to make forks
        * tid: id of the tweet
        * key: API_KEY for posting to julython.org
    """
    expanded = url['expanded']
    # check to see if we have a full url (not bit.ly or others)
    parsed = urlparse(expanded)
    if parsed.netloc in KNOWN_REPOS:
        return _create_project(expanded, screen_name, text, hashtags, tid, key)
    
    # we need to do a little more work here, fetch the url and see if
    # it matches a known repo
    response = requests.get(expanded)
    if response.url in KNOWN_REPOS:
        return _create_project(response.url, screen_name, text, hashtags, tid, key)

def _create_project(expanded, screen_name, text, hashtags, tid, key):
    """Actually create the project."""
    message = {
        'expanded_url': expanded,
        'screen_name': screen_name,
        'text': text,
        'api_key': key,
    }
    response = requests.post(API_URL + 'projects', message)
    if response.status_code == 201:
        # We have created a new project, tweet back the user
        msg = json.loads(response.text)
        tweet = {
            'status': '@%(screen_name)s congrats on the new project, please use the hashtag #%(project)s for updates' % msg,
            'in_reply_to_status_id': tid,
        }
        # TODO: Asynchronous tweeting??
        requests.post('https://twitter.com/statuses/update.xml', tweet, auth=(TWITTER_APP_USER, TWITTER_APP_PASSWORD))
        
    
stream = tweetstream.TweetStream()
stream.fetch("/1/statuses/filter.json?track=julython", callback=callback)

# if you aren't on a running ioloop...
from tornado.ioloop import IOLoop
IOLoop.instance().start()
