# main.py
import asyncio
import time
import uuid
import sys
from deduplicator import Deduplicator
from aggregator import Aggregator
from dingtalk import DingTalkSender
from spider_registry import spider_manager
import spider


class MovieTracker:
    """电影追踪主程序"""

    def __init__(self):
        self.task_id = str(uuid.uuid4())[:8]

    async def run_spiders(self):
        """运行所有爬虫"""
        return await spider_manager.run_all()

    def run_once(self):
        """执行一次完整流程"""
        print(f"\n=== 开始执行任务: {self.task_id} ===")
        print(f"🕐 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        start_time = time.time()

        try:
            self._execute_pipeline()
        except Exception as e:
            self._handle_error(e)
        finally:
            self._log_completion(start_time)

    def _execute_pipeline(self):
        """执行数据处理流水线"""
        # 1. 爬取数据
        all_movies = asyncio.run(self.run_spiders())
        if not all_movies:
            print("❌ 未获取到电影数据，任务结束")
            return

        print(f"📥 共爬取到 {len(all_movies)} 部原始电影数据")

        # 2. 去重
        unique_movies = self._deduplicate_movies(all_movies)

        # 3. 聚合排序
        final_movies = self._aggregate_movies(unique_movies)

        # 4. 钉钉推送
        self._send_dingtalk_message(final_movies)

        # 5. 资源清理
        self._cleanup_resources()

    def _deduplicate_movies(self, all_movies):
        """去重处理"""
        print("🔍 步骤2: 开始去重处理...")
        deduplicator = Deduplicator(self.task_id)
        unique_movies = deduplicator.deduplicate(all_movies)

        duplicate_rate = (1 - len(unique_movies) / len(all_movies)) * 100
        print(f"✅ 去重后剩余 {len(unique_movies)} 部电影 (去重率: {duplicate_rate:.1f}%)")

        return unique_movies

    def _aggregate_movies(self, unique_movies):
        """聚合排序处理"""
        print("📊 步骤3: 开始聚合排序...")
        aggregator = Aggregator()
        return aggregator.aggregate(unique_movies)

    def _send_dingtalk_message(self, final_movies):
        """发送钉钉消息"""
        print("📨 步骤4: 开始钉钉推送...")
        dingtalk_sender = DingTalkSender()
        success = dingtalk_sender.send_message(final_movies)

        if success:
            print("✅ 钉钉推送成功")
        else:
            print("❌ 钉钉推送失败")

    def _cleanup_resources(self):
        """清理资源"""
        print("🧹 步骤5: 清理资源...")
        # 这里可以添加其他资源清理逻辑
        print("✅ 资源清理完成")

    def _handle_error(self, error):
        """处理错误"""
        print(f"❌ 任务执行异常: {str(error)}")
        import traceback
        traceback.print_exc()

    def _log_completion(self, start_time):
        """记录任务完成信息"""
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"🎉 === 任务完成: {self.task_id}, 耗时: {execution_time:.2f}秒 ===")
        print(f"🕐 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


def display_registered_spiders():
    """显示已注册的爬虫"""
    print("📋 已注册的爬虫列表:")
    for i, spider_class in enumerate(spider_manager.spiders, 1):
        spider_name = getattr(spider_class, 'spider_name', spider_class.__name__)
        print(f"  {i}. {spider_name}")


def main():
    """主函数"""
    display_registered_spiders()

    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        print("\n🔧 执行单次任务模式")
        tracker = MovieTracker()
        tracker.run_once()
    else:
        from scheduler import MovieScheduler
        print("\n🔄 启动定时任务模式")
        scheduler = MovieScheduler()
        scheduler.start()


if __name__ == "__main__":
    main()
