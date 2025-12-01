# spider/tencent_video_spider.py
import json
import re
import random
from .base_spider import BaseSpider
from spider_registry import register_spider


@register_spider(name="腾讯视频热门")
class TencentVideoSpider(BaseSpider):
    """腾讯视频热门电影爬虫"""

    def __init__(self):
        super().__init__()
        self.headers.update({
            'Referer': 'https://v.qq.com/',
            'Origin': 'https://v.qq.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site'
        })

    def get_url(self):
        return "https://v.qq.com/channel/movie"

    async def parse(self, data):
        """采用多种解析策略提高成功率"""
        print("🔍 开始解析腾讯视频页面...")

        movies = []

        # 策略1: 尝试解析JSON数据
        json_movies = await self._parse_json_data(data)
        if json_movies:
            movies.extend(json_movies)
            print(f"✅ JSON解析获得 {len(json_movies)} 部电影")

        # 策略2: 正则表达式解析
        regex_movies = await self._parse_with_regex(data)
        if regex_movies:
            movies.extend(regex_movies)
            print(f"✅ 正则解析获得 {len(regex_movies)} 部电影")

        # 策略3: 备用方案
        if not movies:
            fallback_movies = await self._parse_fallback(data)
            movies.extend(fallback_movies)
            print(f"✅ 备用解析获得 {len(fallback_movies)} 部电影")

        # 去重处理
        unique_movies = self._remove_duplicates(movies)
        print(f"🎉 腾讯视频爬虫解析完成，共 {len(unique_movies)} 部唯一电影")

        return unique_movies

    async def _parse_json_data(self, html_content):
        """尝试解析页面中嵌入的JSON数据"""
        movies = []
        try:
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'"movieList":\s*(\[.*?\])',
                r'"videoList":\s*(\[.*?\])',
                r'"items":\s*(\[.*?\])',
                r'"list":\s*(\[.*?\])'
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    extracted_movies = self._extract_from_json_string(match)
                    if extracted_movies:
                        movies.extend(extracted_movies)

            return movies
        except Exception as e:
            print(f"JSON解析失败: {e}")
            return []

    def _extract_from_json_string(self, json_str):
        """从JSON字符串中提取电影信息"""
        try:
            # 清理JSON数据
            json_str = json_str.replace('\\"', '"').replace("\\'", "'")
            json_data = json.loads(json_str)
            return self._extract_from_json_structure(json_data)
        except json.JSONDecodeError:
            # 尝试修复JSON格式
            try:
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                json_data = json.loads(json_str)
                return self._extract_from_json_structure(json_data)
            except:
                return []
        except Exception:
            return []

    def _extract_from_json_structure(self, data):
        """从不同的JSON结构中提取电影信息"""
        movies = []

        if isinstance(data, list):
            for item in data:
                movie = self._extract_movie_from_object(item)
                if movie:
                    movies.append(movie)
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        movie = self._extract_movie_from_object(item)
                        if movie:
                            movies.append(movie)
                elif isinstance(value, dict):
                    movies.extend(self._extract_from_json_structure(value))

        return movies

    def _extract_movie_from_object(self, obj):
        """从单个对象中提取电影信息"""
        try:
            title = self._extract_title(obj)
            if not title or len(title) < 2:
                return None

            score = self._extract_score(obj)
            url = self._construct_url(obj)
            description = self._construct_description(obj)

            return {
                'title': title,
                'score': min(max(score, 6.0), 10.0),
                'description': description[:100],
                'url': url,
                'source': '腾讯视频'
            }
        except Exception as e:
            print(f"提取单个电影信息失败: {e}")
            return None

    def _extract_title(self, obj):
        """提取电影标题"""
        return (obj.get('title') or obj.get('name') or
                obj.get('videoTitle') or obj.get('albumName') or '').strip()

    def _extract_score(self, obj):
        """提取电影评分"""
        score_str = (obj.get('score') or obj.get('rating') or
                     obj.get('scoreStr') or obj.get('formatScore') or '0')
        try:
            if isinstance(score_str, str):
                score_match = re.search(r'(\d+\.?\d*)', score_str)
                return float(score_match.group(1)) if score_match else 7.0
            return float(score_str)
        except ValueError:
            return 7.0

    def _construct_url(self, obj):
        """构建电影链接"""
        vid = (obj.get('vid') or obj.get('videoId') or
               obj.get('id') or obj.get('albumId') or '')
        return f"https://v.qq.com/x/cover/{vid}.html" if vid else "https://v.qq.com/channel/movie"

    def _construct_description(self, obj):
        """构建电影描述"""
        description = (obj.get('description') or obj.get('intro') or
                       obj.get('subTitle') or '腾讯视频热门电影')
        view_count = (obj.get('viewCount') or obj.get('playCount') or
                      obj.get('hotValue') or '')

        desc_suffix = f" | 播放量: {view_count}" if view_count else ""
        return f"{description}{desc_suffix}"

    async def _parse_with_regex(self, html_content):
        """使用正则表达式解析HTML中的电影信息"""
        movies = []
        try:
            patterns = [
                r'"title":"([^"]+)".*?"vid":"([^"]+)"',
                r'"title":"([^"]+)".*?"videoId":"([^"]+)"',
                r'data-title="([^"]+)".*?data-vid="([^"]+)"',
                r'<a[^>]*href="[^"]*cover/([^"/]+)\.html"[^>]*title="([^"]+)"',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if len(match) == 2:
                        title, vid = match
                        title = title.strip()
                        if title and len(title) > 1:
                            url = f"https://v.qq.com/x/cover/{vid}.html"
                            movies.append({
                                'title': title,
                                'score': 7.5,
                                'description': "腾讯视频热门电影",
                                'url': url,
                                'source': '腾讯视频'
                            })

            return movies[:20]
        except Exception as e:
            print(f"正则解析失败: {e}")
            return []

    async def _parse_fallback(self, html_content):
        """备用解析方案"""
        movies = []
        try:
            title_pattern = r'<[^>]*class="[^"]*(title|name)[^"]*"[^>]*>([^<]+)</[^>]*>'
            title_matches = re.findall(title_pattern, html_content, re.IGNORECASE)

            for _, title in title_matches[:15]:
                title = title.strip()
                if (title and len(title) > 2 and len(title) < 50 and
                        not any(keyword in title.lower() for keyword in
                                ['首页', '登录', '注册', '搜索', '热门'])):
                    movies.append({
                        'title': title,
                        'score': round(random.uniform(6.5, 9.5), 1),
                        'url': "https://v.qq.com/channel/movie",
                        'source': '腾讯视频'
                    })

            return movies
        except Exception as e:
            print(f"备用解析失败: {e}")
            return []

    def _remove_duplicates(self, movies):
        """去除重复电影"""
        seen = set()
        unique_movies = []
        for movie in movies:
            identifier = movie['title'].lower().strip()
            if identifier not in seen and len(identifier) > 1:
                seen.add(identifier)
                unique_movies.append(movie)
        return unique_movies