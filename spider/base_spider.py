# spider/base_spider.py
import aiohttp
import asyncio
from abc import ABC, abstractmethod
from config import SPIDER_CONFIG


class BaseSpider(ABC):
    """爬虫基类，定义统一的爬虫接口"""

    def __init__(self, name=None, base_url=None):
        self.name = name or getattr(self, 'spider_name', self.__class__.__name__)
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=SPIDER_CONFIG['timeout'])
        self.headers = self._get_default_headers()

    def _get_default_headers(self):
        """获取默认请求头"""
        return {
            'User-Agent': SPIDER_CONFIG['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def fetch(self, url):
        """异步获取网页内容"""
        for retry in range(SPIDER_CONFIG['max_retries']):
            try:
                return await self._make_request(url)
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                await self._handle_request_error(url, retry, e)
            except Exception as e:
                await self._handle_unexpected_error(url, retry, e)
        return None

    async def _make_request(self, url):
        """执行HTTP请求"""
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers,
                connector=connector
        ) as session:
            async with session.get(url) as response:
                return await self._process_response(response, url)

    async def _process_response(self, response, url):
        """处理HTTP响应"""
        if response.status == 200:
            try:
                return await response.text()
            except Exception as e:
                print(f"❌ 解析响应失败 {url}: {str(e)}")
                bytes_content = await response.read()
                return bytes_content.decode('utf-8', errors='ignore')
        else:
            print(f"⚠️ 请求失败: {url}, 状态码: {response.status}")
            return None

    async def _handle_request_error(self, url, retry, error):
        """处理网络请求错误"""
        error_type = "超时" if isinstance(error, asyncio.TimeoutError) else "网络请求"
        print(f"⏰ {error_type}错误 {url} (重试 {retry + 1}/{SPIDER_CONFIG['max_retries']}): {str(error)}")
        if retry == SPIDER_CONFIG['max_retries'] - 1:
            return None
        await asyncio.sleep(1)

    async def _handle_unexpected_error(self, url, retry, error):
        """处理未知错误"""
        print(f"❌ 未知错误 {url} (重试 {retry + 1}/{SPIDER_CONFIG['max_retries']}): {str(error)}")
        if retry == SPIDER_CONFIG['max_retries'] - 1:
            return None
        await asyncio.sleep(1)

    @abstractmethod
    async def parse(self, data):
        """解析数据，返回电影信息列表"""
        pass

    @abstractmethod
    def get_url(self):
        """获取要爬取的URL"""
        pass

    async def crawl(self):
        """执行爬取任务"""
        url = self.get_url()
        if not url:
            print(f"⚠️ {self.name} 未设置爬取URL")
            return []

        print(f"🕷️ 开始爬取 {self.name}: {url}")

        try:
            data = await self.fetch(url)
            if data:
                movies = await self.parse(data)
                self._log_crawl_result(movies)
                return movies
            else:
                print(f"❌ {self.name} 爬取失败，无法获取数据")
                return []
        except Exception as e:
            print(f"❌ {self.name} 爬取过程异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _log_crawl_result(self, movies):
        """记录爬取结果"""
        if movies:
            print(f"✅ {self.name} 成功解析 {len(movies)} 部电影")
        else:
            print(f"⚠️ {self.name} 未解析到电影数据")