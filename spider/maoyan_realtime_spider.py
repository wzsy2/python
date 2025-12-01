# spider/maoyan_realtime_spider.py
import json
import base64
import hashlib
import random
import math
import time
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="猫眼实时票房")
class MaoyanRealtimeSpider(BaseSpider):
    """猫眼实时票房爬虫"""

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://piaofang.maoyan.com/dashboard/movie',
            'Accept': 'application/json, text/plain, */*',
            'Cookie': '_lxsdk_cuid=19734bbe29ec8-0363fa7e5db86a-7e433c49-16a7f0-19734bbe29ec8; _lxsdk=FE36D070404D11F08A28BDFC6D5346FD2FA34386CFC24FFB949EC1BB9BE626FD'
        })

    def get_url(self):
        signature = self._generate_signature()
        params = f"?timeStamp={signature['timeStamp']}&User-Agent={signature['User-Agent']}&index={signature['index']}&signKey={signature['signKey']}&channelId=40009&sVersion=2"
        return f"https://piaofang.maoyan.com/dashboard-ajax/movie{params}"

    async def parse(self, data):
        try:
            result = self._parse_json_data(data)
            return self._extract_movies(result)
        except json.JSONDecodeError as e:
            print(f"❌ 猫眼实时票房API返回的不是有效JSON: {e}")
            return []
        except Exception as e:
            print(f"❌ 解析猫眼实时票房数据异常: {e}")
            return []

    def _parse_json_data(self, data):
        """解析JSON数据"""
        if isinstance(data, str):
            return json.loads(data)
        return data

    def _extract_movies(self, result):
        """从API结果中提取电影信息"""
        movies = []
        movie_list = result.get('movieList', {}).get('list', [])

        if not movie_list:
            print("⚠️ 猫眼实时票房API返回数据为空")
            return movies

        for movie_data in movie_list:
            movie = self._parse_movie_data(movie_data)
            if movie:
                movies.append(movie)

        print(f"✅ 猫眼实时票房解析成功，共 {len(movies)} 部电影")
        return movies

    def _parse_movie_data(self, movie_data):
        """解析单个电影数据"""
        try:
            movie_name = movie_data.get('movieInfo', {}).get('movieName', '').strip()

            if not movie_name:
                return None

            return {
                'title': movie_name,
                'score': 0.0,  # 票房数据没有评分
                'url': "https://piaofang.maoyan.com/dashboard/movie",
                'source': '猫眼实时票房'
            }
        except (ValueError, KeyError) as e:
            print(f"解析实时票房单条数据失败: {e}")
            return None

    def _generate_signature(self):
        """生成请求签名"""
        user_agent = self.headers['User-Agent']
        encoded_ua = str(base64.b64encode(user_agent.encode('utf-8')), 'utf-8')
        index = str(round(random.random() * 1000))
        times = str(math.ceil(time.time() * 1000))

        content = "method=GET&timeStamp={}&User-Agent={}&index={}&channelId=40009&sVersion=2&key=A013F70DB97834C0A5492378BD76C53A".format(
            times, encoded_ua, index)

        md5 = hashlib.md5()
        md5.update(content.encode('utf-8'))
        sign = md5.hexdigest()

        return {
            'timeStamp': times,
            'User-Agent': encoded_ua,
            'index': index,
            'signKey': sign
        }