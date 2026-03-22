import subprocess
from pathlib import Path


DEFAULT_TASK_NAME = "OK-WW Daily Auto Start"


def normalize_daily_time(value):
    value = (value or "").strip()
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Time must use HH:MM format")

    hour_text, minute_text = parts
    if not hour_text.isdigit() or not minute_text.isdigit():
        raise ValueError("Time must use HH:MM format")

    hour = int(hour_text)
    minute = int(minute_text)
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("Time must be between 00:00 and 23:59")

    return f"{hour:02d}:{minute:02d}"


def build_windows_launch_command(task_number, exit_after_completion=True, *, executable=None, main_script=None,
                                 python_executable=None, frozen=False):
    if task_number < 1:
        raise ValueError("task_number must be greater than 0")

    args = ["-t", str(task_number)]
    if exit_after_completion:
        args.append("-e")

    if frozen:
        if not executable:
            raise ValueError("executable is required when frozen=True")
        command = [str(Path(executable))]
    else:
        if not python_executable or not main_script:
            raise ValueError("python_executable and main_script are required when frozen=False")
        command = [str(Path(python_executable)), str(Path(main_script))]

    command.extend(args)
    return subprocess.list2cmdline(command)


def build_create_daily_task_command(task_name, start_time, launch_command):
    return [
        "schtasks",
        "/Create",
        "/SC",
        "DAILY",
        "/TN",
        task_name,
        "/TR",
        launch_command,
        "/ST",
        normalize_daily_time(start_time),
        "/RL",
        "HIGHEST",
        "/F",
    ]


def build_delete_task_command(task_name):
    return [
        "schtasks",
        "/Delete",
        "/TN",
        task_name,
        "/F",
    ]
