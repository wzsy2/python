# dingtalk.py
import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from config import DINGTALK_CONFIG


class DingTalkSender:
    """钉钉消息发送器"""

    def __init__(self):
        self.webhook = DINGTALK_CONFIG['webhook']
        self.secret = DINGTALK_CONFIG['secret']

    def _get_signed_url(self):
        """生成带签名的URL"""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode('utf-8')

        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign_enc,
            digestmod=hashlib.sha256
        ).digest()

        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f"{self.webhook}&timestamp={timestamp}&sign={sign}"

    def send_message(self, movies):
        """发送钉钉消息"""
        if not self._validate_webhook():
            return False

        try:
            markdown_content = self._create_markdown_content(movies)
            success = self._send_dingtalk_request(markdown_content)
            return success
        except Exception as e:
            print(f"❌ 发送钉钉消息异常: {str(e)}")
            return False

    def _validate_webhook(self):
        """验证Webhook配置"""
        if not self.webhook or self.webhook == 'YOUR_ACCESS_TOKEN':
            print("请配置有效的钉钉Webhook")
            return False
        return True

    def _send_dingtalk_request(self, markdown_content):
        """发送钉钉请求"""
        message = {
            "msgtype": "markdown",
            "markdown": markdown_content,
            "at": {"isAtAll": False}
        }

        headers = {'Content-Type': 'application/json'}
        signed_url = self._get_signed_url()

        response = requests.post(
            signed_url,
            data=json.dumps(message),
            headers=headers,
            timeout=10
        )

        result = response.json()
        return self._handle_response_result(result)

    def _handle_response_result(self, result):
        """处理钉钉响应结果"""
        if result.get('errcode') == 0:
            print("✅ 钉钉消息发送成功")
            return True
        else:
            print(f"❌ 钉钉消息发送失败: {result.get('errmsg')}")
            return False

    def _create_markdown_content(self, movies):
        """创建Markdown格式的消息内容"""
        if not movies:
            return self._create_empty_message()

        sorted_movies = self._sort_movies_by_score(movies)
        content = self._build_message_content(sorted_movies)

        return {
            "title": f"🎬 热门电影推荐 {time.strftime('%m-%d')}",
            "text": content
        }

    def _create_empty_message(self):
        """创建空数据消息"""
        return {
            "title": "🎬 今日电影热点",
            "text": "## 🎬 今日电影热点\n\n暂无热门电影数据"
        }

    def _sort_movies_by_score(self, movies):
        """按评分排序电影"""
        return sorted(
            movies,
            key=lambda x: x.get('composite_score', x.get('score', 0)),
            reverse=True
        )

    def _build_message_content(self, sorted_movies):
        """构建消息内容"""
        content = "## 🎬 今日热门电影推荐\n\n"
        content += f"**📊 共推荐 {len(sorted_movies)} 部热门电影**\n\n"
        content += "---\n\n"

        # 添加电影列表
        content += self._build_movie_list(sorted_movies)
        content += "---\n\n"

        # 添加统计信息
        content += self._build_statistics(sorted_movies)
        content += "\n---\n\n"

        # 添加推荐说明
        content += self._build_recommendation_note()

        return content

    def _build_movie_list(self, sorted_movies):
        """构建电影列表"""
        movie_list = ""
        for i, movie in enumerate(sorted_movies, 1):
            movie_list += self._format_movie_item(movie, i)
        return movie_list

    def _format_movie_item(self, movie, rank):
        """格式化单个电影条目"""
        title = movie['title'].strip().replace('\n', ' ').replace('\r', ' ')
        score = movie.get('composite_score', movie.get('score', 0))
        source = movie.get('source', '未知')

        rank_icon = self._get_rank_icon(rank)
        stars = self._get_star_rating(score)
        source_tag = self._get_source_tag(source)

        return (
            f"{rank_icon} {title}  \n"
            f"   {stars} `{score:.1f}`  \n"
            f"   {source_tag}  \n"
            f"   🔗 [查看详情]({movie['url']})  \n\n"
        )

    def _get_rank_icon(self, rank):
        """获取排名图标"""
        icons = {1: "🥇", 2: "🥈", 3: "🥉"}
        return icons.get(rank, f"{rank}.")

    def _get_star_rating(self, score):
        """根据评分生成星星等级"""
        full_stars = int(score / 2)
        half_star = 1 if score % 2 >= 1 else 0
        empty_stars = 5 - full_stars - half_star

        stars = "⭐" * full_stars
        if half_star:
            stars += "✨"
        stars += "☆" * empty_stars

        return stars

    def _get_source_tag(self, source):
        """根据来源生成标签"""
        source_tags = {
            '豆瓣Top250': '🔸 经典',
            '豆瓣热门': '🔴 热门',
            '豆瓣最新': '🟢 最新',
            '猫眼TOP100': '🟡 榜单',
            '猫眼实时票房': '💰 票房',
            'B站电影热门': '📺 视频',
            '腾讯视频热门': '💻 平台'
        }
        return source_tags.get(source, f'📌 {source}')

    def _build_statistics(self, sorted_movies):
        """构建统计信息"""
        source_count = self._count_movies_by_source(sorted_movies)
        statistics = "### 📈 来源分布统计\n\n"

        sorted_sources = sorted(source_count.items(), key=lambda x: x[1], reverse=True)
        for source, count in sorted_sources:
            percentage = (count / len(sorted_movies)) * 100
            bar = "█" * int(percentage / 5)
            statistics += f"- **{source}**: {count}部 {bar} ({percentage:.1f}%)  \n"

        return statistics

    def _count_movies_by_source(self, movies):
        """按来源统计电影数量"""
        source_count = {}
        for movie in movies:
            source = movie.get('source', '未知')
            source_count[source] = source_count.get(source, 0) + 1
        return source_count

    def _build_recommendation_note(self):
        """构建推荐说明"""
        return (
            "### 💡 推荐说明  \n"
            "🎯 **推荐算法**: 基于多维度综合评分，综合考量影片热度、时效性和平台权重  \n"
            f"⏰ **更新时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}  \n"
            "📱 **数据来源**: 豆瓣、猫眼、B站、腾讯视频等主流影视平台  \n\n"
            "> 💝 每日精选推荐，发现好电影！"
        )