# coding=utf-8
import re
import sys
import time
import json
from contextlib import closing
from threading import Thread
import requests

class WeiboVideoDownloader(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }

    def hello(self):
        print('*' * 60)
        print('\t\t微博视频下载')
        print('\t作者:fenghuang(https://github.com/imfenghuang)')
        print('*' * 60)
        self.run()

    def run(self):
        self.share_url = input('请输入分享链接：')

        if not self.share_url:
            return self.run()

        self.preProcess(self.share_url)

    def preProcess(self, url):
        response = requests.get(url, headers=self.headers)
        ret = re.search(
            r"(?<=mix_media_ids\": )\[[^\]]+\]", response.text, re.M)
        if ret and ret.group():
            medias = json.loads(ret.group())
            threads = []
            for item in medias:
                t = Thread(
                    target=self.getMixMedias,
                    args=(item,),
                )
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
        else:
            self.getFid(response)

    def getMixMedias(self, url):
        response = requests.get(url, headers=self.headers)
        self.getFid(response)

    def getFid(self, response):
        fid = ""
        ret = re.search(r"(?<=1034:)\d+", response.text, re.M)
        if ret and ret.group():
            fid = ret.group()
        else:
            ret = re.search(r"(?<=1034%3A)\d+", response.text, re.M)
            if ret and ret.group():
                fid = ret.group()

        if not fid:
            print("视频不存在")
            exit()
        else:
            self.getVideo(fid)

    def getVideo(self, fid):
        url = "https://weibo.com/tv/api/component"
        params = {
            "page": "/tv/show/1034:{}".format(fid)
        }
        data = {
            "data": '{"Component_Play_Playinfo": {"oid": "1034:%s"}}' % fid
        }

        headers = self.headers
        headers['referer'] = 'https://weibo.com/tv/show/1034:%s?from=old_pc_videoshow' % fid
        headers['cookie'] = 'SUB=%s' % str(time.time())
        response = requests.post(
            url, params=params, data=data, headers=headers)
        try:
            urls = response.json()["data"]["Component_Play_Playinfo"]["urls"]
        except:
            print("获取视频链接出错")
        key = self.findKey(urls.keys())
        video_url = 'http:'+urls[key]
        self.downloader(video_url, fid, key)

    def downloader(self, video_url, video_name, video_type):
        size = 0
        with closing(requests.get(video_url, headers=self.headers, stream=True, verify=False)) as response:
            response = requests.get(
                video_url, headers=self.headers, stream=True, verify=False)
            chunk_size = 1024
            content_size = int(response.headers['content-length'])

            if response.status_code == 200:
                file_size = content_size / chunk_size / 1024
                sys.stdout.write(' [文件大小]: %s %0.2fMB %s \n' % (
                    video_type, file_size, video_name + '.mp4'))

                with open(video_name + ".mp4", "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        size += len(data)
                        file.flush()

                        if float(size / content_size * 100) == 100.00:
                            sys.stdout.write(' [下载完成]: %.2f%% %s' % (
                                float(size / content_size * 100), video_name + '.mp4 \n'))
                        else:
                            sys.stdout.write(' [下载进度]: %.2f%% %s' % (
                                float(size / content_size * 100), video_name + '.mp4 \r'))
                        sys.stdout.flush()

    def findKey(self, keys):
        ret = ''
        list = ['超清 4K60', '超清 4K', '超清 2K60', '超清 2K',
                '高清 1080P', '高清 720P', '标清 480P', '流畅 360P']
        for index in range(len(list)):
            key = list[index]
            if key in keys:
                ret = key
                break
        return ret


if __name__ == '__main__':
    wb = WeiboVideoDownloader()
    wb.hello()
