# twitter -> 微博 转推脚本

自动监控指定用户的新推特，并转发到微博

## 使用说明

### 准备工作

- Get Tweet timelines. You'll need to create a Twitter application to obtain the consumer and secret keys.
- 发微博 需要微博开发者账号并在[微博开放平台](http://open.weibo.com/developers)新建一个app，完成后可以在'应用信息->基本信息'获取 App Key 和 App Secret，还需要在'应用信息->高级信息'里面设置好'授权回调页'

### 使用

- 将`config.sample.py`复制为`config.py`并配置相关参数
- `pip install -r requirements.txt`安装依赖
- `python main.py`运行

## 配置

### Twitter

- `SCREEN_NAME`Twitter要监控用户的用户名
- `PROXY`Twitter代理设置
- `INTERVAL`监控间隔
- `TWITTER_API_KEY`和`TWITTER_API_SECRET`Twitter应用的consumer和secret keys
- `TWITTER_BEARER_TOKEN`（选填）

### Weibo

- `WEIBO_APP_ID`微博应用App ID
- `WEIBO_APP_SECRET`微博应用App Secret
- `WEIBO_REDIRECT_URI`微博应用地址
- `WEIBO_ACCESS_TOKEN`微博认证时需要的access token（选填）
- `WEIBO_USERNAME`和`WEIBO_PASSWORD`使用username/password进行认证
- `WEIBO_FORMAT`发的微博格式（选填）

## 其他问题

### Twtter bearer token 获取方式

- 大部分情况下推荐使用`consumer key`和`secret key`。此时并不需要`bearer token`。
- 可以直接使用以下脚本获取bearer token. 细节请查看文档[Using bearer tokens - Twitter Developer](https://developer.twitter.com/en/docs/basics/authentication/guides/bearer-tokens)
```bash
TWITTER_API_KEY=XXXXXXXXXX
TWITTER_API_SECRET=XXXXXXXXXXXXX
token=`echo -n $TWITTER_API_KEY:$TWITTER_API_SECRET | base64`
curl 'https://api.twitter.com/oauth2/token' -v -d 'grant_type=client_credentials' -H "Authorization: Basic $token"
```

### 微博access_token获取方式

- 因为access_token存在过期时间，因此大部分情况下推荐使用username/password进行认证。此时并不需要access_token。
- 访问`https://api.weibo.com/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}`(client_id和redirect_uri换成自己的)
- 授权后会跳转到`redirect_uri`，同时链接会携带`code`参数
- 在5分钟内访问`https://api.weibo.com/oauth2/access_token?client_id={client_id}&client_secret={client_secret}&grant_type=authorization_code&code={code}&redirect_uri={redirect_uri}`获得`access_token`(参数换成自己的)获得access_token
- 也可以直接运行以下傻瓜脚本。细节请查看官方文档[授权机制 - 微博API](http://open.weibo.com/wiki/%E6%8E%88%E6%9D%83%E6%9C%BA%E5%88%B6%E8%AF%B4%E6%98%8E)
```python
#!/usr/bin/env python3

WEIBO_APP_ID = input('请输入微博 App Key: ')
WEIBO_APP_SECRET = input('请输入微博 App Sectrt: ')
WEIBO_REDIRECT_URI = input('请输入应用地址: ')
WEIBO_AUTHORIZE_URL = 'https://api.weibo.com/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}'.format(client_id=WEIBO_APP_ID, redirect_uri=WEIBO_REDIRECT_URI)
print('请登录微博后访问以下网址并同意授权 ' + WEIBO_AUTHORIZE_URL)
WEIBO_CODE = input('请输入网页授权跳转后链接的code参数: ')
WEIBO_ACCESS_TOKEN_URL = 'https://api.weibo.com/oauth2/access_token?client_id={client_id}&client_secret={client_secret}&grant_type={grant_type}&code={code}&redirect_uri={redirect_uri}'.format(client_id=WEIBO_APP_ID, client_secret=WEIBO_APP_SECRET, grant_type='authorization_code', code=WEIBO_CODE, redirect_uri=WEIBO_REDIRECT_URI)
import urllib3
http = urllib3.PoolManager()
r = http.request('POST', WEIBO_ACCESS_TOKEN_URL)
print(r.data).decode('utf-8')
```

## 参考文档

- [Twitter Developer Platform - Docs](https://developer.twitter.com/en/docs)
- [微博开放平台 - 开发文档](http://open.weibo.com/wiki)
- 微博SDK使用[lxyu/weibo](https://github.com/lxyu/weibo)并有少量改动
- [ozh/ozh-tweet-archiver](https://github.com/ozh/ozh-tweet-archiver)
- 微博H5SDK使用[KoushiHime - koushihime/utils/weibo.py](https://github.com/ethe/KoushiHime/blob/0822b97588d9607143d3e5a40d5afda9f356d199/koushihime/utils/weibo.py)
