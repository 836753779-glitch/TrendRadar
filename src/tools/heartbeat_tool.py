"""
心跳机制工具
用于监控视频生成任务的运行状态，定期发送心跳通知，检测任务超时或失败
"""

import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from langchain.tools import tool

# 全局心跳状态
_heartbeat_status = {
    "running": False,
    "task_name": "",
    "start_time": None,
    "last_heartbeat": None,
    "heartbeat_count": 0,
    "thread": None,
    "interval": 60  # 默认60秒发送一次心跳
}

_heartbeat_lock = threading.Lock()


# 提取公共逻辑为普通函数（避免 @tool 函数互相调用）
def _send_heartbeat_to_feishu(message: str) -> str:
    """
    发送心跳通知到飞书（内部函数，不使用 @tool 装饰）
    """
    try:
        from tools.feishu_notification_tool import _send_feishu_text_raw
        return _send_feishu_text_raw(message)
    except Exception as e:
        return f"error: {str(e)}"


@tool
def start_heartbeat(
    task_name: str,
    interval: int = 60,
    max_duration: Optional[int] = None
) -> str:
    """
    启动心跳监控机制。

    Args:
        task_name: 任务名称（如"视频生成任务"）
        interval: 心跳间隔时间（秒），默认60秒
        max_duration: 最大监控时长（秒），超过则自动停止并报警，None表示不限制

    Returns:
        启动状态信息

    Example:
        start_heartbeat(
            task_name="视频生成任务",
            interval=60,
            max_duration=300
        )
    """
    global _heartbeat_status, _heartbeat_lock

    with _heartbeat_lock:
        if _heartbeat_status["running"]:
            return f"⚠️ 心跳机制已在运行中，任务：{_heartbeat_status['task_name']}"

        _heartbeat_status["running"] = True
        _heartbeat_status["task_name"] = task_name
        _heartbeat_status["start_time"] = datetime.now()
        _heartbeat_status["last_heartbeat"] = datetime.now()
        _heartbeat_status["heartbeat_count"] = 0
        _heartbeat_status["interval"] = interval

        # 启动心跳线程
        _heartbeat_status["thread"] = threading.Thread(
            target=_heartbeat_worker,
            args=(task_name, interval, max_duration),
            daemon=True
        )
        _heartbeat_status["thread"].start()

        return f"✅ 心跳机制已启动\n任务名称：{task_name}\n心跳间隔：{interval}秒\n最大监控时长：{max_duration or '无限制'}秒"


@tool
def send_heartbeat(
    message: Optional[str] = None,
    task_status: str = "running"
) -> str:
    """
    发送一次心跳通知到飞书。

    Args:
        message: 附加消息（可选）
        task_status: 任务状态（running/progress/completed/failed）

    Returns:
        发送结果

    Example:
        send_heartbeat(
            message="视频生成进度：50%",
            task_status="progress"
        )
    """
    global _heartbeat_status, _heartbeat_lock

    with _heartbeat_lock:
        if not _heartbeat_status["running"]:
            return "⚠️ 心跳机制未启动，请先调用 start_heartbeat"

        _heartbeat_status["last_heartbeat"] = datetime.now()
        _heartbeat_status["heartbeat_count"] += 1

    # 计算运行时间
    if _heartbeat_status["start_time"]:
        elapsed = datetime.now() - _heartbeat_status["start_time"]
        elapsed_str = str(elapsed).split('.')[0]  # 去除微秒
    else:
        elapsed_str = "未知"

    # 构建心跳消息
    status_emoji = {
        "running": "💓",
        "progress": "🔄",
        "completed": "✅",
        "failed": "❌"
    }

    heartbeat_msg = f"""{status_emoji.get(task_status, "💓")} **心跳通知**

**任务名称**：{_heartbeat_status['task_name']}
**任务状态**：{task_status}
**运行时间**：{elapsed_str}
**心跳次数**：{_heartbeat_status['heartbeat_count']}
**当前时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    if message:
        heartbeat_msg += f"\n**附加信息**：{message}"

    # 发送到飞书
    send_result = _send_heartbeat_to_feishu(heartbeat_msg)
    if send_result == "success":
        return f"✅ 心跳已发送（第{_heartbeat_status['heartbeat_count']}次）"
    else:
        return f"❌ 心跳发送失败：{send_result}"


@tool
def stop_heartbeat(
    final_status: str = "completed",
    final_message: Optional[str] = None
) -> str:
    """
    停止心跳监控机制。

    Args:
        final_status: 最终状态（completed/failed）
        final_message: 最终消息（可选）

    Returns:
        停止状态信息

    Example:
        stop_heartbeat(
            final_status="completed",
            final_message="视频生成成功"
        )
    """
    global _heartbeat_status, _heartbeat_lock

    with _heartbeat_lock:
        if not _heartbeat_status["running"]:
            return "⚠️ 心跳机制未启动"

        _heartbeat_status["running"] = False

        # 发送最后一次心跳（直接构造消息，避免调用 @tool 函数）
        if final_message:
            status_emoji = {
                "completed": "✅",
                "failed": "❌"
            }

            # 计算总运行时间
            if _heartbeat_status["start_time"]:
                total_time = datetime.now() - _heartbeat_status["start_time"]
                total_time_str = str(total_time).split('.')[0]
            else:
                total_time_str = "未知"

            final_msg = f"""{status_emoji.get(final_status, "✅")} **任务完成通知**

**任务名称**：{_heartbeat_status['task_name']}
**最终状态**：{final_status}
**总运行时间**：{total_time_str}
**总心跳次数**：{_heartbeat_status['heartbeat_count']}
**附加信息**：{final_message}
"""

            _send_heartbeat_to_feishu(final_msg)

        # 计算总运行时间
        if _heartbeat_status["start_time"]:
            total_time = datetime.now() - _heartbeat_status["start_time"]
            total_time_str = str(total_time).split('.')[0]
        else:
            total_time_str = "未知"

        result = f"""✅ 心跳机制已停止

任务名称：{_heartbeat_status['task_name']}
最终状态：{final_status}
总运行时间：{total_time_str}
总心跳次数：{_heartbeat_status['heartbeat_count']}
"""

        # 重置状态
        _heartbeat_status["task_name"] = ""
        _heartbeat_status["start_time"] = None
        _heartbeat_status["last_heartbeat"] = None
        _heartbeat_status["heartbeat_count"] = 0

        return result


@tool
def check_heartbeat_status() -> str:
    """
    检查当前心跳机制状态。

    Returns:
        当前状态信息

    Example:
        check_heartbeat_status()
    """
    global _heartbeat_status, _heartbeat_lock

    with _heartbeat_lock:
        if not _heartbeat_status["running"]:
            return "❌ 心跳机制未启动"

        if _heartbeat_status["start_time"]:
            elapsed = datetime.now() - _heartbeat_status["start_time"]
            elapsed_str = str(elapsed).split('.')[0]
        else:
            elapsed_str = "未知"

        if _heartbeat_status["last_heartbeat"]:
            last_beat = datetime.now() - _heartbeat_status["last_heartbeat"]
            last_beat_str = str(last_beat).split('.')[0]
        else:
            last_beat_str = "从未"

        status_info = f"""📊 **心跳机制状态**

**运行状态**：{'🟢 运行中' if _heartbeat_status['running'] else '🔴 已停止'}
**任务名称**：{_heartbeat_status['task_name']}
**启动时间**：{_heartbeat_status['start_time'].strftime('%Y-%m-%d %H:%M:%S') if _heartbeat_status['start_time'] else '未知'}
**运行时长**：{elapsed_str}
**心跳间隔**：{_heartbeat_status['interval']}秒
**总心跳次数**：{_heartbeat_status['heartbeat_count']}
**上次心跳**：{last_beat_str}前
"""

        return status_info


def _heartbeat_worker(
    task_name: str,
    interval: int,
    max_duration: Optional[int]
):
    """
    心跳工作线程（内部使用）
    """
    global _heartbeat_status, _heartbeat_lock

    while True:
        with _heartbeat_lock:
            if not _heartbeat_status["running"]:
                break

        # 发送心跳（直接调用普通函数，避免调用 @tool 函数）
        try:
            # 构建心跳消息
            status_emoji = {"running": "💓"}

            if _heartbeat_status["start_time"]:
                elapsed = datetime.now() - _heartbeat_status["start_time"]
                elapsed_str = str(elapsed).split('.')[0]
            else:
                elapsed_str = "未知"

            heartbeat_msg = f"""{status_emoji.get("running", "💓")} **心跳通知**

**任务名称**：{task_name}
**任务状态**：running
**运行时间**：{elapsed_str}
**心跳次数**：{_heartbeat_status['heartbeat_count']}
**当前时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            # 发送心跳
            _send_heartbeat_to_feishu(heartbeat_msg)

            # 更新心跳计数
            with _heartbeat_lock:
                _heartbeat_status["last_heartbeat"] = datetime.now()
                _heartbeat_status["heartbeat_count"] += 1

        except:
            pass  # 忽略发送失败

        # 检查是否超时
        if max_duration and _heartbeat_status["start_time"]:
            elapsed = (datetime.now() - _heartbeat_status["start_time"]).total_seconds()
            if elapsed >= max_duration:
                # 超时报警
                status_emoji = {"failed": "❌"}

                elapsed_str = f"{int(elapsed)}秒"
                timeout_msg = f"""{status_emoji.get("failed", "❌")} **任务超时报警**

**任务名称**：{task_name}
**运行时长**：{elapsed_str}
**最大监控时长**：{max_duration}秒
**总心跳次数**：{_heartbeat_status['heartbeat_count']}
**报警信息**：任务已超过最大监控时长，可能存在异常！
"""

                _send_heartbeat_to_feishu(timeout_msg)

                with _heartbeat_lock:
                    _heartbeat_status["running"] = False
                break

        # 等待下一次心跳
        time.sleep(interval)


@tool
def monitor_video_generation(
    task_name: str,
    interval: int = 60,
    max_duration: int = 600
) -> str:
    """
    监控视频生成任务（一键启动心跳监控）。

    Args:
        task_name: 任务名称
        interval: 心跳间隔（秒），默认60秒
        max_duration: 最大监控时长（秒），默认600秒（10分钟）

    Returns:
        启动信息

    Example:
        monitor_video_generation(
            task_name="沉香视频生成",
            interval=60,
            max_duration=600
        )
    """
    return start_heartbeat(
        task_name=task_name,
        interval=interval,
        max_duration=max_duration
    )
