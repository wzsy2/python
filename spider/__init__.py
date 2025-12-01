# spider/__init__.py
from .base_spider import BaseSpider
from .bilibili_movie_spider import BilibiliMovieSpider
from .douban_top250_spider import DoubanTop250Spider
from .douban_hot_spider import DoubanHotSpider
from .douban_latest_spider import DoubanLatestSpider
from .maoyan_top100_spider import MaoyanTop100Spider
from .maoyan_realtime_spider import MaoyanRealtimeSpider
from .tencent_video_spider import TencentVideoSpider

__all__ = [
    'BaseSpider',
    'DoubanTop250Spider',
    'DoubanHotSpider',
    'DoubanLatestSpider',
    'MaoyanTop100Spider',
    'MaoyanRealtimeSpider',
    'BilibiliMovieSpider',
    'TencentVideoSpider',
]

print("✅ Spider包已加载，爬虫注册完成")