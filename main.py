#!/usr/bin/env python3

import os
import sys
import time
import logging
from config import config
from weibo import Client as WeiboClient
import tweet
import atexit

logging.basicConfig(
    format="%(asctime)s - %(name)s - [%(levelname)s] %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if sys.version_info[0] < 3:
    logger.warn("NOTICE: You python version is lower than 3!")

if config.DEBUG:
    logging.getLogger('root').setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
logger.info('Loaded config: {}'.format(str(config)))


weiboClient = None
tweetClient = None


def exit_handler():
    logger.warn('Application is ending!')


def getWeiboClient(config):
    if config.WEIBO_ACCESS_TOKEN:
        weiboClient = WeiboClient(config.WEIBO_APP_ID, config.WEIBO_APP_SECRET, config.WEIBO_REDIRECT_URI, token={
                                  'access_token': config.WEIBO_ACCESS_TOKEN})
    elif config.WEIBO_USERNAME and config.WEIBO_PASSWORD:
        weiboClient = WeiboClient(config.WEIBO_APP_ID, config.WEIBO_APP_SECRET, config.WEIBO_REDIRECT_URI,
                                  username=config.WEIBO_USERNAME, password=config.WEIBO_PASSWORD)
    else:
        raise('Get weiboClient fail - WEIBO_ACCESS_TOKEN not found OR (WEIBO_USERNAME and config.WEIBO_PASSWORD) not found')
    return weiboClient


def getTweetClient(config):
    payload = {
        'apiKey': config.TWITTER_API_KEY,
        'apiSecret': config.TWITTER_API_SECRET,
        'bearerToken': config.TWITTER_BEARER_TOKEN,
        'proxy': config.PROXY,
        'screenName': config.SCREEN_NAME,
        'interval': config.INTERVAL
    }
    tweetClient = tweet.Tweet(**payload)
    return tweetClient


def init():
    global weiboClient, tweetClient, config
    weiboClient = getWeiboClient(config)
    tweetClient = getTweetClient(config)
    logger.info('Monitoring {}'.format(tweetClient.screenName))


def postWeibo(text, pic=None):
    status = '{prefix}{text}{redirect}'.format(
        prefix=config.WEIBO_PREFIX, text=text, redirect=config.WEIBO_REDIRECT_URI)  # duplicate
    if len(status) > 140:
        logger.debug('input text more than 140 characters ' + str(len(text)))
        text = text[0:(140 - len(status) - 3)] + '...'
        status = '{prefix}{text}{redirect}'.format(
            prefix=config.WEIBO_PREFIX, text=text, redirect=config.WEIBO_REDIRECT_URI)  # duplicate
    logger.info('share weibo... - {}'.format(status))
    resp = weiboClient.shareWeibo(status, pic)
    logger.debug('shareWeibo resp - ' + str(resp))


def filterTweet(l):
    # filter photo
    # l = filter(tweet.hasImage, l)  # tweet contains photo
    l = list(l)
    return l


def loop():
    l = tweetClient.getNewTweets()
    if len(l) <= 0:
        return

    for t in l:
        url = 'https://twitter.com/{}/status/{}'.format(
            tweetClient.screenName, t.get('id'))
        logger.info('new tweet - {}'.format(url))

    l = filterTweet(l)
    l = map(tweet.mapPhotoList, l)  # simplify obj
    l = list(l)
    if len(l) <= 0:
        return

    for d in l:
        text = d.get('full_text')
        photoList = d.get('photoList')
        if len(photoList) <= 0:
            return

        url = 'https://twitter.com/{}/status/{}'.format(
            tweetClient.screenName, d.get('id'))
        # logger.info('photo tweet -> {}'.format(url))
        if len(photoList) > 1:
            logging.warn('tweet 图片数量超过一张 -> {}'.format(url))
        pic = tweet.getPhoto(photoList[0], proxy=config.PROXY)
        postWeibo(text, pic)


def main():
    init()

    if '-f' in sys.argv:  # debug argv
        loop()
    if config.INTERVAL < 30:
        logger.warn('sleep time is too short! sleepTime: {}s. Forced to change to 30s'.format(
            config.INTERVAL))
        config.INTERVAL = 30

    while True:
        logger.debug('sleep {}s...'.format(config.INTERVAL))
        time.sleep(config.INTERVAL)
        loop()


if __name__ == '__main__':
    atexit.register(exit_handler)
    main()
