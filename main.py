#!/usr/bin/env python3

import os
import sys
import time
import datetime
import logging
from config import config
import weibo
import mweibo
import tweet

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


def getWeiboClient(config):
    if config.WEIBO_COOKIE:
        logger.debug('weiboClient use WEIBO_COOKIE')
        # weibo H5
        weiboClient = mweibo.WeiboAPI(config.WEIBO_COOKIE)
    elif config.WEIBO_ACCESS_TOKEN:
        # weibo API
        logger.debug('weiboClient use WEIBO_ACCESS_TOKEN')
        weiboClient = weibo.Client(config.WEIBO_APP_ID, config.WEIBO_APP_SECRET, config.WEIBO_REDIRECT_URI, token={
            'access_token': config.WEIBO_ACCESS_TOKEN})
    elif config.WEIBO_USERNAME and config.WEIBO_PASSWORD:
        # weibo API + username/password
        logger.debug('weiboClient use WEIBO_USERNAME ans WEIBO_PASSWORD')
        weiboClient = weibo.Client(config.WEIBO_APP_ID, config.WEIBO_APP_SECRET, config.WEIBO_REDIRECT_URI,
                                   username=config.WEIBO_USERNAME, password=config.WEIBO_PASSWORD)
    else:
        raise Exception(
            'Get weiboClient fail - WEIBO_COOKIE not found OR WEIBO_ACCESS_TOKEN not found OR (WEIBO_USERNAME and config.WEIBO_PASSWORD) not found')
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


def filterTweet(l) -> list:
    # filter photo
    # l = filter(tweet.hasImage, l)  # tweet contains photo
    l = list(l)
    return l


def formatTweet(t) -> (str, list):
    '''
    return: tweet.full_text, extended_entities.photo
    '''
    text = t.get('full_text')
    media = t.get('extended_entities', {}).get('media', {})
    media = filter(lambda media: media.get('type') == 'photo', media)
    photoList = map(lambda media: media.get('media_url_https'), media)
    pics = list(map(lambda link: tweet.getPhoto(
        link, proxy=config.PROXY), photoList))

    tz_utc_8 = datetime.timezone(datetime.timedelta(hours=8))
    tweetTime = datetime.datetime.strptime(
        t.get('created_at'), '%a %b %d %H:%M:%S %z %Y')
    tweetTime = tweetTime.astimezone(tz_utc_8)  # change timezone
    timeStr = tweetTime.strftime('%Y.%m.%d %H:%M:%S')

    def formatter(str):
        # format weibo
        return config.WEIBO_FORMAT.format(text=str, time=timeStr)
    status = formatter(text)

    # word count limit
    if len(status) > 140:
        logger.debug('input text more than 140 characters ' + str(len(text)))
        text = text[0:(140 - len(status) - 3)] + '...'
        status = formatter(text)
    return status, pics


def postWeibo(text, pics):
    '''
    param
    text: str
    pics: list
    '''
    if isinstance(weiboClient, weibo.Client):
        # weibo API
        if not len(pics):
            resp = weiboClient.shareWeibo(text, redirect_uri=config.WEIBO_REDIRECT_URI)
            return resp
        if len(pics) > 1:
            logging.warn('tweet 图片数量超过一张，已自动过滤为一张')
        pic = pics[0]
        resp = weiboClient.shareWeibo(
            text, pic=pic, redirect_uri=config.WEIBO_REDIRECT_URI)
        return resp
    if isinstance(weiboClient, mweibo.WeiboAPI):
        # weibo H5
        resp = weiboClient.post(text, pic=pics)
        return resp
    raise Exception('unknown weiboClient!')


def loop():
    l = tweetClient.getNewTweets()

    for t in l:
        url = 'https://twitter.com/{}/status/{}'.format(
            tweetClient.screenName, t.get('id'))
        logger.info('new tweet - {}'.format(url))

    l = filterTweet(l)
    if len(l) <= 0:
        return

    for t in l:
        text, pics = formatTweet(t)
        logger.info('post weibo... - {}'.format(text))
        resp = postWeibo(text, pics)
        logger.debug('postWeibo resp - ' + str(resp))


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
    try:
        main()
    except Exception as e:
        logger.exception(e)
