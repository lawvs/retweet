#!/usr/bin/env python3
'''tweet
see: https://developer.twitter.com/en/docs/tweets
see: https://github.com/ozh/ozh-tweet-archiver
'''

import os
import sys
import time
import json
import base64
import logging
import urllib3


def initHttp(proxy=None):
    if not proxy:
        try:
            import certifi
            http = urllib3.PoolManager(
                cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
            return http
        except ImportError:
            logging.warn(
                'certifi ImportError, Please install certifi. "pip install certifi"')
            http = urllib3.PoolManager()
            return http

    if proxy.startswith('http'):
        http = urllib3.ProxyManager(proxy)
    elif proxy.startswith('sock'):
        try:
            from urllib3.contrib.socks import SOCKSProxyManager
            http = SOCKSProxyManager(proxy)
            return http
        except ImportError:
            raise Exception(
                'PROXY setup failed! - ImportError! Please install urllib3[socks]. "pip install urllib3[socks]"')
    else:
        raise Exception('Unknown proxy {}'.format(proxy))
    return http


def filterTime(tweet, now, interval) -> bool:
    created_at = time.strptime(
        tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')
    diff = time.mktime(now) - time.mktime(created_at)  # second
    if diff >= interval:
        return False
    return True


def hasImage(tweet) -> bool:
    '''
    Tweet objects has photo (tweet -> extended_entities -> media -> type == 'photo')
    see: https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/entities-object
    '''
    if not 'extended_entities' in tweet or not 'media' in tweet['extended_entities']:
        return False
    return any(media['type'] == 'photo' for media in tweet['extended_entities']['media'])


def mapPhotoList(tweet) -> dict:
    '''
    return the list of images in tweet
    '''
    media = tweet.get('extended_entities', {}).get('media', {})
    media = filter(lambda media: media.get('type') == 'photo', media)
    photoList = list(map(lambda media: media.get('media_url_https'), media))
    return {
        'id': tweet.get('id'),
        'full_text': tweet.get('full_text'),
        'photoList': photoList,
    }


def getPhoto(url, proxy=None):
    http = initHttp(proxy)
    resp = http.request('GET', url)
    return resp.data


class Tweet(object):
    """Tweet"""

    def __init__(self, **kwargs):
        super(Tweet, self).__init__()
        self.apiKey = kwargs.get('apiKey')
        self.apiSecret = kwargs.get('apiSecret')
        self._bearerToken = kwargs.get('bearerToken')
        self.http = initHttp(kwargs.get('proxy'))
        self.screenName = kwargs.get('screenName')
        self.count = kwargs.get('count', 10)
        self.interval = kwargs.get('interval', 300)

    @property
    def bearerToken(self):
        if self._bearerToken:
            return self._bearerToken
        self._bearerToken = self.refreshBearerToken()
        return self._bearerToken

    def refreshBearerToken(self) -> str:
        '''
        TWITTER_API_KEY=XXXXXXXXXX
        TWITTER_API_SECRET=XXXXXXXXXXXXX
        token=`echo -n $TWITTER_API_KEY:$TWITTER_API_SECRET | base64`
        curl -x 'localhost:1080' 'https://api.twitter.com/oauth2/token' -v -d 'grant_type=client_credentials' -H "Authorization: Basic $token"
        see: https://developer.twitter.com/en/docs/basics/authentication/guides/bearer-tokens
        '''
        apiKey = self.apiKey
        apiSecret = self.apiSecret
        if not apiKey or not apiSecret:
            raise Exception('TWITTER_API_KEY or TWITTER_API_SECRET not found!')
        token = base64.b64encode(
            (apiKey + ':' + apiSecret).encode('utf-8')).decode('utf-8')
        resp = self.http.urlopen(
            'POST',
            'https://api.twitter.com/oauth2/token',
            body='grant_type=client_credentials',
            headers={
                'Authorization': 'Basic ' + token,
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
            }
        )
        data = json.loads(resp.data.decode('utf-8'))
        logging.debug('{} - {}'.format('refreshBearerToken', data))
        token = data.get('access_token')
        if not token:
            raise Exception('refreshBearerToken fail - ' + data)
        return token

    def getNewTweets(self, count=None, interval=None) -> list:
        '''
        curl -x 'localhost:1080' 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=KanColle_STAFF&count=10&tweet_mode=extended' -v  -H "Authorization: Bearer $TWITTER_BEARER_TOKEN"
        return new tweets
        see: https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline.html
        '''
        screenName = self.screenName
        count = count or self.count
        interval = interval if interval != None else self.interval
        if not screenName:
            raise Exception('screenName not found')

        resp = self.http.request(
            'GET',
            'https://api.twitter.com/1.1/statuses/user_timeline.json',
            fields={
                'screen_name': screenName,
                'count': count,
                'tweet_mode': 'extended'
            },
            headers={
                'Authorization': 'Bearer ' + self.bearerToken
            }
        )
        tweets = json.loads(resp.data.decode('utf-8'))
        status = resp.status
        if not tweets or status != 200:
            if status == 401:
                logging.error('Could not fetch tweets: unauthorized access.')
        ratelimit = int(resp.headers['x-rate-limit-limit'])
        ratelimit_r = int(resp.headers['x-rate-limit-remaining'])
        logging.debug("API status: " + str(status))
        logging.debug("API rate: " + str(ratelimit_r / ratelimit))

        now = time.gmtime()
        if interval > 0:
            newList = list(
                filter(lambda tweet: filterTime(tweet, now, interval), tweets))
        else:
            newList = tweets
        if not newList:
            return []
        newList.reverse()
        logging.debug('new tweet - ' + str(newList))
        return newList


def test():
    payload = {
        'apiKey': 'XXXXX',
        'apiSecret': 'XXXXX',
        'bearerToken': 'AAAAAAAAAAAAAAAAAAAAA',
        'proxy': 'https://localhost:1080/',
        'screenName': 'SCREEN_NAME',
        'interval': 500
    }

    tweet = Tweet(**payload)
    t = tweet.getNewTweets(interval=0)
    print(str(t))


if __name__ == '__main__':
    test()
