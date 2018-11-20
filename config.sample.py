
class Config(object):
    DEBUG = False
    TESTING = False
    # 监控账号 Twitter screen name  *Required
    SCREEN_NAME = 'KanColle_STAFF'
    # Twitter proxy
    PROXY = None
    # 监控间隔  *Required
    INTERVAL = 300  # second

    # Twitter
    # https://developer.twitter.com/en/docs/basics/authentication/overview/oauth
    # OPTIONAL - (TWITTER_API_KEY + TWITTER_API_SECRET) or TWITTER_BEARER_TOKEN
    # Consumer Key
    TWITTER_API_KEY = None
    # Consumer Secret
    TWITTER_API_SECRET = None
    TWITTER_BEARER_TOKEN = None

    # Weibo
    # Weibo H5 cookie  https://m.weibo.cn
    WEIBO_COOKIE = ''
    # http://open.weibo.com/wiki/
    # App ID  *Required
    WEIBO_APP_ID = '11111'
    # App Secret  *Required
    WEIBO_APP_SECRET = 'qwerty'
    # 应用地址  *Required
    WEIBO_REDIRECT_URI = 'https://www.example.com'
    # OPTIONAL - WEIBO_ACCESS_TOKEN or (WEIBO_USERNAME + WEIBO_PASSWORD)
    WEIBO_ACCESS_TOKEN = None  # access token
    WEIBO_USERNAME = None
    WEIBO_PASSWORD = None
    WEIBO_FORMAT = '{text}' # 转发微博的格式 *Optional

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    '''
    生产环境配置
    '''
    DEBUG = False


class DevelopmentConfig(Config):
    '''
    开发环境配置
    '''
    DEBUG = True
    PROXY = 'https://localhost:1080/'


class TestingConfig(Config):
    TESTING = True


def loadEnv():
    import os
    env = os.environ.get('ENV')
    if env:
        return env
    if '.prod' in os.listdir():
        env = 'prod'
    else:
        env = 'default'
    return env


configDict = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}

env = loadEnv()
config = configDict[env]
