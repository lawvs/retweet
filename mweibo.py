#!/usr/bin/env python3

import requests
import mimetypes


class WeiboAPI(object):

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': ', deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6,en;q=0.4',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Host': 'm.weibo.cn',
        'Origin': 'https://m.weibo.cn',
        'Referer': 'https://m.weibo.cn/compose'
    }
    upload_path = 'https://m.weibo.cn/api/statuses/uploadPic'
    post_path = 'https://m.weibo.cn/api/statuses/update'

    def __init__(self, cookie):
        self.headers['Cookie'] = cookie

    def upload_image(self, image):
        # {'name': ('filename', 'data', 'text/plain')}
        filename = getattr(image, 'name', 'img')
        pauload = {
            'type': (None, 'json'),
            'pic': (filename, image, self.guess_content_type(filename)),
            'st': (None, self.st)
        }
        resp = requests.post(
            self.upload_path, headers=self.headers, files=pauload)
        # success
        # {
        #   "pic_id":"PIC_ID",
        #   "thumbnail_pic":"http:\/\/wx2.sinaimg.cn\/thumbnail\/PIC_ID.jpg",
        #   "bmiddle_pic":"http:\/\/wx2.sinaimg.cn\/bmiddle\/PIC_ID.jpg",
        #   "original_pic":"http:\/\/wx2.sinaimg.cn\/large\/PIC_ID.jpg"
        # }

        # fail
        # {'ok': 0, 'msg': 'token校验失败', 'errno': '100006'}
        # {
        #   'ok': 0,
        #   'msg': '上传失败，请稍后重试'
        # }
        js = resp.json()
        if js.get('ok', 1) != 1:
            raise WeiboPostError(resp.text)
        return js

    def post(self, content, pic=None):
        data = {'content': content, 'st': self.st}
        if pic:
            if not isinstance(pic, list):
                pic = [pic]
            pic = list(map(lambda p: self.upload_image(p).get('pic_id') if hasattr(
                p, 'read') or isinstance(p, bytes) else p, pic))
            pic = ','.join(pic)
            data['picId'] = pic
        resp = requests.post(self.post_path, headers=self.headers, data=data)
        try:
            return resp.json()
        except:
            raise WeiboPostError(resp.text)

    @property
    def st(self):
        return requests.get(
            "https://m.weibo.cn/api/config", headers=self.headers).json()['data']['st']

    @staticmethod
    def guess_content_type(url):
        n = url.rfind('.')
        if n == (-1):
            return 'application/octet-stream'
        ext = url[n:]
        return mimetypes.types_map.get(ext, 'application/octet-stream')


class WeiboPostError(Exception):
    pass