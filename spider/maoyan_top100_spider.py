# spider/maoyan_top100_spider.py
import re
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="猫眼电影TOP100")
class MaoyanTop100Spider(BaseSpider):
    """猫眼电影TOP100爬虫"""

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://maoyan.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    def get_url(self):
        return "https://www.maoyan.com/board/4"

    async def parse(self, data):
        try:
            return self._extract_movies_with_regex(data)
        except Exception as e:
            print(f"❌ 解析猫眼TOP100数据异常: {e}")
            return []

    def _extract_movies_with_regex(self, data):
        """使用正则表达式提取电影信息"""
        movies = []
        pattern = re.compile(
            '<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
            + '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>',
            re.S
        )

        items = re.findall(pattern, data)
        for item in items:
            movie = self._parse_movie_item(item)
            if movie:
                movies.append(movie)

        print(f"✅ 猫眼TOP100解析成功，共 {len(movies)} 部电影")
        return movies

    def _parse_movie_item(self, item):
        """解析单个电影条目"""
        try:
            index = item[0]
            title = item[2].strip()
            score_str = item[5] + item[6]  # 拼接整数和小数部分

            if not title:
                return None

            movie_url = f"https://maoyan.com/films/{index}"
            score = float(score_str) if score_str and score_str != '00' else 0.0

            return {
                'title': title,
                'score': score,
                'url': movie_url,
                'source': '猫眼TOP100'
            }
        except (ValueError, IndexError) as e:
            print(f"解析猫眼TOP100单条数据失败: {e}")
            return None