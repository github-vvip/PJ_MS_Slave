import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

_scheduler_thread = None
_stop_event = threading.Event()

SAVE_HOURS = [11, 23]


def auto_save_snapshots():
    try:
        from api.models import TaskModule, TaskItem, HistorySnapshot
        modules = TaskModule.objects.all()
        saved_count = 0
        skipped_count = 0

        for mod in modules:
            today_tasks = TaskItem.objects.filter(
                module=mod, task_type='today'
            ).order_by('order', '-created_at')

            if not today_tasks.exists():
                continue

            lines = ['=== 今日任务 ===']
            for idx, item in enumerate(today_tasks, 1):
                line = f'{idx}. {item.content}'
                if item.remarks:
                    line += f'（{item.remarks}）'
                if item.is_completed:
                    line += ' [已完成]'
                lines.append(line)

            content = '\n'.join(lines)
            content_hash = hash(content)

            last = HistorySnapshot.objects.filter(module_name=mod.name).order_by('-saved_at').first()
            if last and last.content_hash == content_hash:
                skipped_count += 1
                continue

            HistorySnapshot.objects.create(
                module_name=mod.name,
                content=content,
                content_hash=content_hash,
            )
            saved_count += 1

        logger.info(f'定时自动保存完成: 保存{saved_count}条, 跳过{skipped_count}条')
    except Exception as e:
        logger.error(f'定时自动保存失败: {e}')


def _scheduler_loop():
    while not _stop_event.is_set():
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        if current_hour in SAVE_HOURS and current_minute == 0:
            auto_save_snapshots()
            time.sleep(65)
            continue

        _stop_event.wait(timeout=30)


def start_scheduler():
    global _scheduler_thread
    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        return

    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()
    logger.info('定时调度器已启动: 自动保存任务将在每天 11:00 和 23:00 执行')
