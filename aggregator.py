# aggregator.py
from collections import defaultdict


class Aggregator:
    """电影数据聚合器，负责计算综合评分和排序"""

    def __init__(self):
        self.weights = self._get_default_weights()
        self.source_credibility = self._get_source_credibility()

    def _get_default_weights(self):
        """获取默认权重配置"""
        return {
            'base_score': 0.38,
            'source_credibility': 0.17,
            'popularity_bonus': 0.25,
            'recency_bonus': 0.2
        }

    def _get_source_credibility(self):
        """获取数据源可信度配置"""
        return {
            '豆瓣Top250': 0.8,
            '豆瓣热门': 0.9,
            '豆瓣最新': 1.0,
            '猫眼TOP100': 0.85,
            '猫眼实时票房': 1.5,
            'B站电影热门': 0.9,
            '腾讯视频热门': 0.9
        }

    def aggregate(self, movies):
        """聚合电影数据，按综合评分排序"""
        if not movies:
            return []

        # 计算综合评分
        scored_movies = self._calculate_composite_scores(movies)

        # 按来源分组并确保最小数量
        selected_movies = self._select_movies_by_source(scored_movies)

        # 最终排序
        final_movies = self._sort_final_movies(selected_movies)

        # 输出统计信息
        self._print_selection_stats(final_movies)

        return final_movies

    def _calculate_composite_scores(self, movies):
        """为所有电影计算综合评分"""
        scored_movies = []
        for movie in movies:
            composite_score = self._calculate_composite_score(movie, movies)
            movie['composite_score'] = composite_score
            scored_movies.append(movie)
        return scored_movies

    def _calculate_composite_score(self, movie, all_movies):
        """计算单部电影的综合评分"""
        base_score = movie.get('score', 0)
        source = movie.get('source', '')

        normalized_base_score = min(base_score / 10.0, 1.0)
        credibility = self.source_credibility.get(source, 0.5)
        popularity_bonus = self._calculate_popularity_bonus(movie, all_movies)
        recency_bonus = self._calculate_recency_bonus(movie)

        composite_score = (
                self.weights['base_score'] * normalized_base_score +
                self.weights['source_credibility'] * credibility +
                self.weights['popularity_bonus'] * popularity_bonus +
                self.weights['recency_bonus'] * recency_bonus
        )

        return round(composite_score * 10, 1)

    def _calculate_popularity_bonus(self, movie, all_movies):
        """计算流行度加成"""
        base_score = movie.get('score', 0)
        source = movie.get('source', '')

        # 基础流行度加成
        base_bonus = self._calculate_base_popularity_bonus(base_score, all_movies)

        # 来源额外加成
        source_bonus = self._calculate_source_popularity_bonus(source)

        return base_bonus + source_bonus

    def _calculate_base_popularity_bonus(self, base_score, all_movies):
        """计算基础流行度加成"""
        if not all_movies:
            return 0.0

        avg_score = sum(m.get('score', 0) for m in all_movies) / len(all_movies)

        if base_score > avg_score:
            excess_ratio = min((base_score - avg_score) / (10 - avg_score), 1.0)
            return excess_ratio * 0.3

        return 0.0

    def _calculate_source_popularity_bonus(self, source):
        """计算来源流行度加成"""
        bonus_map = {
            '实时': 0.95,
            '票房': 0.95,
            '最新': 0.4,
            '热门': 0.3,
            'TOP': 0.1,
            'Top': 0.1,
            '250': 0.1
        }

        for keyword, bonus in bonus_map.items():
            if keyword in source:
                return bonus

        return 0.2  # 默认加成

    def _calculate_recency_bonus(self, movie):
        """计算时效性加成"""
        source = movie.get('source', '')

        if '实时' in source or '票房' in source:
            return 0.95
        elif '最新' in source:
            return 0.4
        elif '热门' in source:
            return 0.3
        else:
            return 0.0

    def _select_movies_by_source(self, scored_movies):
        """按来源选择电影，确保每个来源至少有3部"""
        movies_by_source = self._group_movies_by_source(scored_movies)
        selected_movies = []

        # 每个来源至少选择3部
        for source_movies in movies_by_source.values():
            min_count = min(3, len(source_movies))
            selected_movies.extend(source_movies[:min_count])

        # 补充剩余电影
        remaining_movies = self._get_remaining_movies(movies_by_source, selected_movies)
        needed_count = 30 - len(selected_movies)

        if needed_count > 0 and remaining_movies:
            selected_movies.extend(remaining_movies[:needed_count])

        return selected_movies

    def _group_movies_by_source(self, scored_movies):
        """按来源分组电影"""
        movies_by_source = defaultdict(list)
        for movie in scored_movies:
            source = movie.get('source', '未知')
            movies_by_source[source].append(movie)

        # 按综合评分排序每个来源的电影
        for source in movies_by_source:
            movies_by_source[source] = sorted(
                movies_by_source[source],
                key=lambda x: x.get('composite_score', 0),
                reverse=True
            )

        return movies_by_source

    def _get_remaining_movies(self, movies_by_source, selected_movies):
        """获取剩余未选中的电影"""
        remaining_movies = []

        for source, source_movies in movies_by_source.items():
            already_selected = source_movies[:min(3, len(source_movies))]
            remaining = [m for m in source_movies if m not in already_selected]
            remaining_movies.extend(remaining)

        return sorted(
            remaining_movies,
            key=lambda x: x.get('composite_score', 0),
            reverse=True
        )

    def _sort_final_movies(self, movies):
        """对最终电影列表进行排序"""
        return sorted(
            movies,
            key=lambda x: x.get('composite_score', 0),
            reverse=True
        )

    def _print_selection_stats(self, final_movies):
        """输出选择统计信息"""
        print(f"📊 最终选择 {len(final_movies)} 部电影")

        source_count = defaultdict(int)
        for movie in final_movies:
            source = movie.get('source', '未知')
            source_count[source] += 1

        print("📋 各来源分布:")
        for source, count in source_count.items():
            print(f"  {source}: {count} 部")

    def set_weights(self, base_score=None, source_credibility=None,
                    popularity_bonus=None, recency_bonus=None):
        """动态设置权重系数"""
        weights_to_update = {
            'base_score': base_score,
            'source_credibility': source_credibility,
            'popularity_bonus': popularity_bonus,
            'recency_bonus': recency_bonus
        }

        for key, value in weights_to_update.items():
            if value is not None:
                self.weights[key] = value

        # 确保权重总和为1
        self._normalize_weights()

    def _normalize_weights(self):
        """标准化权重，确保总和为1"""
        total = sum(self.weights.values())
        if total != 1.0:
            for key in self.weights:
                self.weights[key] /= total

    def add_source_credibility(self, source, credibility):
        """添加或更新数据源可信度"""
        self.source_credibility[source] = max(0.0, min(credibility, 1.2))