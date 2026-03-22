import os
import subprocess
import sys
from pathlib import Path

from qfluentwidgets import FluentIcon

from ok import Logger
from src.task.BaseWWTask import BaseWWTask
from src.task.schedule_utils import (
    DEFAULT_TASK_NAME,
    build_create_daily_task_command,
    build_delete_task_command,
    build_windows_launch_command,
    normalize_daily_time,
)

logger = Logger.get_logger(__name__)


class LazyDailyTask(BaseWWTask):

    task_options = [
        "Daily Task",
        "Tacet Suppression",
        "Forgery Challenge",
        "Simulation Challenge",
        "Nightmare Nest",
    ]
    task_name_to_class = {
        "Daily Task": "DailyTask",
        "Tacet Suppression": "TacetTask",
        "Forgery Challenge": "ForgeryTask",
        "Simulation Challenge": "SimulationTask",
        "Nightmare Nest": "NightmareNestTask",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.DATE_TIME
        self.group_name = "Daily"
        self.group_icon = FluentIcon.CALENDAR
        self.name = "Lazy Daily Auto Start"
        self.description = "Create or remove a Windows daily scheduled launch that runs one configured task and exits."
        self.default_config = {
            'Enable Daily Auto Start': True,
            'Daily Start Time': '06:00',
            'Task to Run': self.task_options[0],
            'Exit After Task': True,
        }
        self.config_description = {
            'Enable Daily Auto Start': 'Turn on to create/update the Windows scheduled task. Turn off and run once to remove it.',
            'Daily Start Time': '24-hour format, for example 06:00 or 23:30.',
            'Task to Run': 'The task that Windows should launch automatically each day.',
            'Exit After Task': 'Close ok-ww automatically after the task is finished.',
        }
        self.config_type = {
            'Task to Run': {
                'type': 'drop_down',
                'options': self.task_options,
            },
        }

    def run(self):
        if os.name != 'nt':
            self.log_error('Lazy Daily Auto Start is only supported on Windows.', notify=True)
            return

        task_name = DEFAULT_TASK_NAME
        enabled = self.config.get('Enable Daily Auto Start', True)
        daily_time = self.config.get('Daily Start Time', '06:00')

        try:
            normalized_time = normalize_daily_time(daily_time)
        except ValueError as exc:
            self.log_error(f'Invalid Daily Start Time: {exc}', notify=True)
            return

        selected_task_name = self.config.get('Task to Run', self.task_options[0])
        task_number = self.resolve_task_number(selected_task_name)
        if task_number is None:
            self.log_error(f'Unsupported task selection: {selected_task_name}', notify=True)
            return

        if enabled:
            command = self.build_launch_command(task_number)
            schedule_command = build_create_daily_task_command(task_name, normalized_time, command)
        else:
            command = None
            schedule_command = build_delete_task_command(task_name)

        result = subprocess.run(schedule_command, capture_output=True, text=True)
        output = "\n".join(filter(None, [result.stdout.strip(), result.stderr.strip()])).strip()

        if result.returncode != 0:
            if not enabled and "ERROR:" in output and "cannot find the file specified" in output.lower():
                self.log_info('Daily auto start task was already removed.', notify=True)
                return
            self.log_error(f'Windows Task Scheduler command failed: {output or result.returncode}', notify=True)
            return

        if enabled:
            self.info_set('Daily Start Time', normalized_time)
            self.info_set('Task to Run', selected_task_name)
            self.info_set('Task Number', task_number)
            self.info_set('Launch Command', command)
            self.log_info(f'Daily auto start created for {normalized_time}. It will run "{selected_task_name}" and exit automatically.', notify=True)
        else:
            self.log_info('Daily auto start removed.', notify=True)

    def resolve_task_number(self, selected_task_name):
        class_name = self.task_name_to_class.get(selected_task_name)
        if class_name is None:
            return None

        from config import config

        for index, task_spec in enumerate(config.get('onetime_tasks', []), start=1):
            if len(task_spec) >= 2 and task_spec[1] == class_name:
                return index
        return None

    def build_launch_command(self, task_number):
        is_frozen = bool(getattr(sys, 'frozen', False))
        if is_frozen:
            return build_windows_launch_command(
                task_number,
                self.config.get('Exit After Task', True),
                executable=sys.executable,
                frozen=True,
            )

        main_script = Path(__file__).resolve().parents[2] / 'main.py'
        return build_windows_launch_command(
            task_number,
            self.config.get('Exit After Task', True),
            python_executable=sys.executable,
            main_script=main_script,
            frozen=False,
        )
