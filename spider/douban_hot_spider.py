# spider/douban_hot_spider.py
import json
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="豆瓣热门电影")
class DoubanHotSpider(BaseSpider):
    """豆瓣热门电影爬虫"""

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://movie.douban.com/',
            'Accept': 'application/json, text/plain, */*'
        })

    def get_url(self):
        return "https://movie.douban.com/j/search_subjects?type=movie&tag=热门&sort=recommend&page_limit=20&page_start=0"

    async def parse(self, data):
        try:
            result = self._parse_json_data(data)
            return self._extract_movies(result)
        except json.JSONDecodeError as e:
            print(f"❌ 豆瓣热门电影API返回的不是有效JSON: {e}")
            print(f"原始返回数据: {data[:200]}...")
            return []
        except Exception as e:
            print(f"❌ 解析豆瓣热门电影数据异常: {e}")
            return []

    def _parse_json_data(self, data):
        """解析JSON数据"""
        if isinstance(data, str):
            return json.loads(data)
        return data

    def _extract_movies(self, result):
        """从API结果中提取电影信息"""
        movies = []
        subjects = result.get('subjects', [])

        if not subjects:
            print("⚠️ 豆瓣热门电影API返回数据为空")
            return movies

        for movie_data in subjects:
            movie = self._parse_movie_data(movie_data)
            if movie:
                movies.append(movie)

        print(f"✅ 豆瓣热门电影解析成功，共 {len(movies)} 部")
        return movies

    def _parse_movie_data(self, movie_data):
        """解析单个电影数据"""
        try:
            title = movie_data.get('title', '').strip()
            score_str = movie_data.get('rate', '0')
            url = movie_data.get('url', '')

            if not title or not url:
                return None

            score = float(score_str) if score_str and score_str != '0' else 0.0

            return {
                'title': title,
                'score': score,
                'url': url,
                'source': '豆瓣热门'
            }
        except (ValueError, KeyError) as e:
            print(f"解析热门电影单条数据失败: {e}")
            return None