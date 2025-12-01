# deduplicator.py
import redis
import hashlib
from config import REDIS_CONFIG


class Deduplicator:
    """电影去重器，基于Redis实现去重功能"""

    def __init__(self, task_id):
        self.redis_client = redis.Redis(**REDIS_CONFIG)
        self.task_id = task_id
        self.key_prefix = f"movie_tracker:{task_id}"

    def _get_movie_hash(self, movie):
        """生成电影信息的哈希值用于去重"""
        content = movie['title'].strip().lower()  # 只使用电影标题
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def is_duplicate(self, movie):
        """检查电影是否重复"""
        movie_hash = self._get_movie_hash(movie)
        key = f"{self.key_prefix}:hashes"

        if self.redis_client.sismember(key, movie_hash):
            return True

        self.redis_client.sadd(key, movie_hash)
        return False

    def deduplicate(self, movies):
        """对电影列表进行去重"""
        unique_movies = []
        duplicate_count = 0

        for movie in movies:
            if not self.is_duplicate(movie):
                unique_movies.append(movie)
            else:
                duplicate_count += 1

        if duplicate_count > 0:
            print(f"🔍 去重处理: 发现 {duplicate_count} 部重复电影")

        return unique_movies

    def cleanup(self):
        """清理本次任务的Redis数据"""
        pattern = f"{self.key_prefix}:*"
        keys = self.redis_client.keys(pattern)

        if keys:
            self.redis_client.delete(*keys)
            print(f"🧹 清理Redis数据: {len(keys)} 个键")