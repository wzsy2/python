# spider_registry.py
class SpiderManager:
    """爬虫管理器，负责注册和运行所有爬虫"""

    def __init__(self):
        self.spiders = []

    def register(self, spider_class):
        """注册爬虫类"""
        self.spiders.append(spider_class)
        return spider_class

    async def run_all(self):
        """运行所有注册的爬虫"""
        if not self.spiders:
            print("⚠️ 没有注册任何爬虫")
            return []

        print(f"🕷️ 开始执行 {len(self.spiders)} 个爬虫...")
        all_movies = []

        for spider_class in self.spiders:
            movies = await self._run_single_spider(spider_class)
            if movies:
                all_movies.extend(movies)

        print(f"📊 总共爬取到 {len(all_movies)} 部电影")
        return all_movies

    async def _run_single_spider(self, spider_class):
        """运行单个爬虫"""
        try:
            spider_instance = spider_class()
            result = await spider_instance.crawl()

            if result:
                print(f"✅ {spider_class.__name__} 爬取到 {len(result)} 部电影")
            else:
                print(f"⚠️ {spider_class.__name__} 未获取到数据")

            return result
        except Exception as e:
            print(f"❌ 爬虫 {spider_class.__name__} 执行异常: {e}")
            return []


# 创建全局爬虫管理器实例
spider_manager = SpiderManager()


def register_spider(cls=None, *, name=None):
    """爬虫注册装饰器"""

    def decorator(clazz):
        clazz.spider_name = name or clazz.__name__
        spider_manager.register(clazz)
        return clazz

    if cls is None:
        return decorator
    return decorator(cls)