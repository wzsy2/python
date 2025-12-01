# spider/bilibili_movie_spider.py
import json
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="B站电影热门")
class BilibiliMovieSpider(BaseSpider):
    """B站电影热门爬虫"""

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
        })

    def get_url(self):
        return "https://api.bilibili.com/x/web-interface/ranking/v2?rid=23&type=all"

    async def parse(self, data):
        try:
            result = self._parse_json_data(data)
            return self._extract_movies(result)
        except json.JSONDecodeError as e:
            print(f"❌ B站电影热门API返回的不是有效JSON: {e}")
            print(f"原始返回数据: {data[:200]}...")
            return []
        except Exception as e:
            print(f"❌ 解析B站电影热门数据异常: {e}")
            return []

    def _parse_json_data(self, data):
        """解析JSON数据"""
        if isinstance(data, str):
            return json.loads(data)
        return data

    def _extract_movies(self, result):
        """从API结果中提取电影信息"""
        movies = []
        video_list = result.get('data', {}).get('list', [])

        if not video_list:
            print("⚠️ B站电影热门API返回数据为空")
            return movies

        for video_data in video_list:
            movie = self._parse_video_data(video_data)
            if movie:
                movies.append(movie)

        return movies

    def _parse_video_data(self, video_data):
        """解析单个视频数据"""
        try:
            title = video_data.get('title', '').strip()
            bvid = video_data.get('bvid', '')

            if not title or not bvid:
                return None

            score = self._calculate_score(video_data)

            return {
                'title': title,
                'score': max(score, 6.0),
                'url': f"https://www.bilibili.com/video/{bvid}",
                'source': 'B站电影'
            }
        except (ValueError, KeyError) as e:
            print(f"解析B站电影单条数据失败: {e}")
            return None

    def _calculate_score(self, video_data):
        """计算视频评分"""
        bilibili_score = video_data.get('pts', 0)
        return round(bilibili_score / 1000, 1)