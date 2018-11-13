import os
import json
import logging
import urllib3
import traceback
import certifi


def initHttp(proxy=None):
    if not proxy:
        # http = urllib3.PoolManager()
        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
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
                'PROXY setup failed! - ImportError! Please install urllib3[socks]:"pip install urllib3[socks]"')
    else:
        raise Exception('Unknown proxy {}'.format(proxy))
    return http


class TelegramHanlder(logging.Handler):

    def __init__(self, token, chatId, proxy=None, name=None):
        super(TelegramHanlder, self).__init__()
        if not token or not chatId:
            raise Exception('token or chatid not found!')
        self.token = token
        self.api = 'https://api.telegram.org/bot{token}/'.format(
            token=self.token)
        self.chatId = chatId
        self.http = initHttp(proxy)
        self.name = name or 'TgLogger'
        self.checkService()
        # self.sendMessage('[{}] INIT: starting...'.format(self.name))

    def emit(self, record):
        # text = self.format(record)
        tb = ''.join(traceback.format_exception(
            *record.exc_info)) if record.exc_info else ''
        text = '[{}] {}: {} {}'.format(
            self.name, record.levelname, record.msg, tb)
        try:
            self.sendMessage(text)
        except Exception as e:
            print(str(e))

    def checkService(self):
        url = self.api + 'getMe'
        resp = self.http.request('GET', url, timeout=5)
        if resp.status != 200:
            logging.warn('TG api status error! status: {}'.format(resp.status))
            return
        data = json.loads(resp.data.decode('utf-8'))
        logging.info('TG api status: {ok} botname: {username}'.format(
            ok=data.get('ok', False), username=data.get('result', {}).get('username')))

    def sendMessage(self, text):
        url = self.api + 'sendMessage'
        resp = self.http.request(
            'GET',
            url,
            fields={
                'chat_id': self.chatId,
                'text': text
            }
        )
        return resp


def test():
    # config
    token = 'XXXXXX'
    chatId = 11111
    proxy = 'https://localhost:1080/'
    # init
    tgHandler = TelegramHanlder(token, chatId, proxy=proxy, name='test app')
    tgHandler.setLevel(logging.WARN)
    logging.getLogger().addHandler(tgHandler)

    logging.info('info log')
    logging.warn('warn log')
    tgHandler.sendMessage('manual log')


if __name__ == '__main__':
    test()
