import time
import psutil
from datetime import datetime
from qfluentwidgets import FluentIcon
from ok import Logger, TriggerTask
from src.task.DailyTask import DailyTask
from src.task.FarmEchoTask import FarmEchoTask
from src.task.AutoRogueTask import AutoRogueTask
from src.task.ForgeryTask import ForgeryTask
from src.task.NightmareNestTask import NightmareNestTask
from src.task.SimulationTask import SimulationTask
from src.task.TacetTask import TacetTask
from src.task.EnhanceEchoTask import EnhanceEchoTask
from src.task.ChangeEchoTask import ChangeEchoTask
from src.task.DiagnosisTask import DiagnosisTask
from src.task.BaseWWTask import BaseWWTask

logger = Logger.get_logger(__name__)

class ScheduleTask(BaseWWTask, TriggerTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Schedule Task"
        self.description = "后台静默定时任务监控"
        self.icon = FluentIcon.HISTORY
        
        # TriggerTask 必须设置触发间隔（秒）
        # 设置为 30 秒，确保在设定的那一分钟内能被检测到
        self.trigger_interval = 30
        
        # 获取全局配置
        self.schedule_config = self.get_global_config('Schedule Config')
        
        self.task_map = {
            "Daily Task": DailyTask,
            "Farm Echo Task": FarmEchoTask,
            "Auto Rogue Task": AutoRogueTask,
            "Forgery Task": ForgeryTask,
            "Nightmare Nest Task": NightmareNestTask,
            "Simulation Task": SimulationTask,
            "Tacet Task": TacetTask,
            "Enhance Echo Task": EnhanceEchoTask,
            "Change Echo Task": ChangeEchoTask,
            "Diagnosis Task": DiagnosisTask
        }
        
        self.last_run_date = None

    def is_game_running(self):
        """检查游戏进程是否已经在运行"""
        game_exes = ["Client-Win64-Shipping.exe", "Wuthering Waves.exe"]
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in game_exes:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def run(self):
        # 实时读取全局配置
        enabled = self.schedule_config.get('Enabled', False)
        if not enabled:
            return

        scheduled_time_str = self.schedule_config.get('Scheduled Time (HH:MM)', '04:00')
        task_name = self.schedule_config.get('Task to Run', 'Daily Task')
        auto_start = self.schedule_config.get('Auto Start Game', True)
        
        try:
            scheduled_time = datetime.strptime(scheduled_time_str, '%H:%M').time()
        except ValueError:
            self.log_error(f"时间格式错误: {scheduled_time_str}")
            return

        now = datetime.now()
        current_time = now.time()
        current_date = now.date()
        
        # 到达设定时间，且今天还未运行过
        if (current_time.hour == scheduled_time.hour and 
            current_time.minute == scheduled_time.minute and 
            self.last_run_date != current_date):
            
            # 标记今天已运行，防止在同一分钟内的下一次轮询触发
            self.last_run_date = current_date
            self.log_info(f"--- 定时任务触发: {task_name} ---")
            
            # 1. 自动启动检查
            if auto_start:
                if not self.is_game_running():
                    self.log_info("检测到游戏未运行，等待框架底层自动唤起...")
                    # 注意：我们这里【绝不】手动调用 start_device()
                    # 只要框架检测到没有窗口，底层的 StartController 会自动触发单例启动逻辑
                    # 我们只需要在这里稍微等待一下，或者直接进入任务队列
                    time.sleep(10)
                else:
                    self.log_info("游戏已在运行。")
            
            # 2. 执行目标任务
            task_class = self.task_map.get(task_name)
            if task_class:
                try:
                    self.log_info(f"开始执行任务内容: {task_name}")
                    # 使用框架提供的 run_task_by_class 同步执行
                    # 这会将任务加入框架的执行队列
                    self.run_task_by_class(task_class)
                    self.log_info(f"任务 {task_name} 已加入队列并开始执行。")
                except Exception as e:
                    self.log_error(f"任务执行出错: {e}")
