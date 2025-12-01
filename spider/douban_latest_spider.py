import aiohttp
import asyncio
import json
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="豆瓣最新电影")
class DoubanLatestSpider(BaseSpider):
    """豆瓣最新电影爬虫（修正版）"""

    def __init__(self):
        super().__init__()
        # 添加豆瓣特定的请求头
        self.headers.update({
            'Referer': 'https://movie.douban.com/',
            'Accept': 'application/json, text/plain, */*'
        })

    def get_url(self):
        # 使用更稳定的最新电影API
        return "https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=电影"

    async def parse(self, data):
        try:
            # 现在data是字符串，需要手动解析JSON
            if isinstance(data, str):
                result = json.loads(data)
            else:
                result = data

            movies = []

            movie_list = result.get('data', [])
            if not movie_list:
                print("⚠️ 豆瓣最新电影API返回数据为空")
                return movies

            for movie_data in movie_list:
                try:
                    movie_title = movie_data.get('title', '').strip()
                    # 处理评分字段，豆瓣最新API的评分字段可能是'rate'或嵌套在'rating'中
                    movie_score = '0'
                    if 'rate' in movie_data:
                        movie_score = movie_data.get('rate', '0')
                    elif 'rating' in movie_data:
                        rating_obj = movie_data.get('rating', {})
                        if isinstance(rating_obj, dict):
                            movie_score = rating_obj.get('value', '0')
                        else:
                            movie_score = str(rating_obj)

                    movie_url = movie_data.get('url', '')
                    directors = movie_data.get('directors', [])
                    director_name = directors[0] if directors else "未知"

                    if movie_title and movie_url:
                        movies.append({
                            'title': movie_title,
                            'score': float(movie_score) if movie_score and movie_score != '0' else 0.0,
                            'url': movie_url,
                            'source': '豆瓣最新'
                        })
                except (ValueError, KeyError, IndexError) as e:
                    print(f"解析最新电影单条数据失败: {e}")
                    continue

            print(f"✅ 豆瓣最新电影解析成功，共 {len(movies)} 部")
            return movies

        except json.JSONDecodeError as e:
            print(f"❌ 豆瓣最新电影API返回的不是有效JSON: {e}")
            print(f"原始返回数据: {data[:200]}...")
            return []
        except Exception as e:
            print(f"❌ 解析豆瓣最新电影数据异常: {e}")
            return []# spider/douban_latest_spider.py
import json
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="豆瓣最新电影")
class DoubanLatestSpider(BaseSpider):
    """豆瓣最新电影爬虫"""

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://movie.douban.com/',
            'Accept': 'application/json, text/plain, */*'
        })

    def get_url(self):
        return "https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=电影"

    async def parse(self, data):
        try:
            result = self._parse_json_data(data)
            return self._extract_movies(result)
        except json.JSONDecodeError as e:
            print(f"❌ 豆瓣最新电影API返回的不是有效JSON: {e}")
            print(f"原始返回数据: {data[:200]}...")
            return []
        except Exception as e:
            print(f"❌ 解析豆瓣最新电影数据异常: {e}")
            return []

    def _parse_json_data(self, data):
        """解析JSON数据"""
        if isinstance(data, str):
            return json.loads(data)
        return data

    def _extract_movies(self, result):
        """从API结果中提取电影信息"""
        movies = []
        movie_list = result.get('data', [])

        if not movie_list:
            print("⚠️ 豆瓣最新电影API返回数据为空")
            return movies

        for movie_data in movie_list:
            movie = self._parse_movie_data(movie_data)
            if movie:
                movies.append(movie)

        print(f"✅ 豆瓣最新电影解析成功，共 {len(movies)} 部")
        return movies

    def _parse_movie_data(self, movie_data):
        """解析单个电影数据"""
        try:
            title = movie_data.get('title', '').strip()
            url = movie_data.get('url', '')
            score = self._extract_score(movie_data)

            if not title or not url:
                return None

            return {
                'title': title,
                'score': float(score) if score and score != '0' else 0.0,
                'url': url,
                'source': '豆瓣最新'
            }
        except (ValueError, KeyError, IndexError) as e:
            print(f"解析最新电影单条数据失败: {e}")
            return None

    def _extract_score(self, movie_data):
        """从电影数据中提取评分"""
        if 'rate' in movie_data:
            return movie_data.get('rate', '0')
        elif 'rating' in movie_data:
            rating_obj = movie_data.get('rating', {})
            if isinstance(rating_obj, dict):
                return rating_obj.get('value', '0')
            return str(rating_obj)
        return '0'