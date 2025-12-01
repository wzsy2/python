# spider/douban_top250_spider.py
from lxml import html
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="豆瓣电影Top250")
class DoubanTop250Spider(BaseSpider):
    """豆瓣电影Top250爬虫"""

    def get_url(self):
        return "https://movie.douban.com/top250"

    async def parse(self, data):
        try:
            tree = html.fromstring(data)
            return self._extract_movies(tree)
        except Exception as e:
            print(f"解析豆瓣Top250数据异常: {e}")
            return []

    def _extract_movies(self, tree):
        """从HTML中提取电影信息"""
        movies = []
        movie_items = tree.xpath('//div[@class="item"]')

        for item in movie_items:
            movie = self._parse_movie_item(item)
            if movie:
                movies.append(movie)

        return movies

    def _parse_movie_item(self, item):
        """解析单个电影条目"""
        try:
            title = self._extract_title(item)
            score = self._extract_score(item)
            url = self._extract_url(item)

            if not title or not url:
                return None

            return {
                'title': title,
                'score': score,
                'url': url,
                'source': '豆瓣Top250'
            }
        except Exception as e:
            print(f"解析单部电影信息失败: {e}")
            return None

    def _extract_title(self, item):
        """提取电影标题"""
        title_element = item.xpath('.//span[@class="title"][1]/text()')
        return title_element[0].strip() if title_element else None

    def _extract_score(self, item):
        """提取电影评分"""
        rating_element = item.xpath('.//span[@class="rating_num"]/text()')
        return float(rating_element[0]) if rating_element else 0.0

    def _extract_url(self, item):
        """提取电影链接"""
        link_element = item.xpath('.//div[@class="hd"]/a/@href')
        return link_element[0] if link_element else ""