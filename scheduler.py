# scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading
from config import SCHEDULER_CONFIG
from main import run_once


class MovieScheduler:
    """电影数据定时调度器"""

    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.is_running = False
        self.current_thread = None

    def scheduled_task(self):
        """定时执行的任务"""
        if self.is_running:
            print("上次任务仍在执行，跳过本次执行")
            return

        def run_task():
            self.is_running = True
            try:
                run_once()
            except Exception as e:
                print(f"任务执行异常: {str(e)}")
            finally:
                self.is_running = False

        self.current_thread = threading.Thread(target=run_task)
        self.current_thread.start()

    def start(self):
        """启动定时任务"""
        interval_seconds = SCHEDULER_CONFIG['interval_seconds']

        trigger = IntervalTrigger(seconds=interval_seconds)
        self.scheduler.add_job(
            self.scheduled_task,
            trigger,
            id='movie_tracking_job'
        )

        print(f"电影热点追踪系统已启动，每{interval_seconds}秒执行一次")
        self._start_scheduler()

    def _start_scheduler(self):
        """启动调度器"""
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("定时任务已停止")

    def stop(self):
        """停止定时任务"""
        self.scheduler.shutdown()