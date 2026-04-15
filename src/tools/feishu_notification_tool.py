from langchain.tools import tool
import requests
import json
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

# 飞书 Webhook URL
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/7d8ff2cf-295a-453c-8da2-e1d45c53caa5"


# 提取公共逻辑为普通函数（可被其他函数调用）
def _send_feishu_text_raw(text: str) -> str:
    """
    发送文本消息到飞书（内部函数，不使用 @tool 装饰）

    Args:
        text: 消息文本内容

    Returns:
        发送结果
    """
    try:
        payload = {
            "msg_type": "text",
            "content": {"text": text}
        }

        response = requests.post(FEISHU_WEBHOOK_URL, json=payload)
        result = response.json()

        if result.get("StatusCode") == 0 or result.get("code") == 0:
            return f"✅ 消息发送成功"
        else:
            return f"❌ 消息发送失败：{result}"

    except Exception as e:
        return f"❌ 发送异常：{str(e)}"


@tool
def send_feishu_text_message(text: str) -> str:
    """
    发送文本消息到飞书。

    Args:
        text: 消息文本内容

    Returns:
        发送结果

    Example:
        send_feishu_text_message("视频生成完成！")
    """
    ctx = request_context.get() or new_context(method="send_feishu_text_message")

    # 调用普通函数完成实际发送
    return _send_feishu_text_raw(text)


@tool
def send_feishu_video_notification(
    title: str,
    video_url: str,
    description: str = None,
    video_duration: int = None,
    thumbnail_url: str = None
) -> str:
    """
    发送视频通知到飞书（富文本格式）。

    Args:
        title: 视频标题
        video_url: 视频URL
        description: 视频描述（可选）
        video_duration: 视频时长（秒，可选）
        thumbnail_url: 视频缩略图URL（可选）

    Returns:
        发送结果

    Example:
        send_feishu_video_notification(
            title="线香产品介绍视频",
            video_url="https://example.com/video.mp4",
            description="这是关于'静谧禅心'线香的介绍视频",
            video_duration=60
        )
    """
    ctx = request_context.get() or new_context(method="send_feishu_video_notification")

    try:
        # 构建富文本内容
        content_text = f"🎬 {title}\n\n"

        if description:
            content_text += f"📝 {description}\n\n"

        if video_duration:
            minutes = video_duration // 60
            seconds = video_duration % 60
            content_text += f"⏱️ 时长：{minutes}分{seconds}秒\n\n"

        content_text += f"🔗 视频链接：{video_url}\n\n"
        content_text += "点击链接下载或观看视频"

        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"📹 {title}",
                        "content": [
                            [
                                {"tag": "text", "text": content_text},
                                {"tag": "a", "text": "观看视频", "href": video_url}
                            ]
                        ]
                    }
                }
            }
        }

        response = requests.post(FEISHU_WEBHOOK_URL, json=payload)
        result = response.json()

        if result.get("StatusCode") == 0 or result.get("code") == 0:
            return f"""✅ 视频通知发送成功！

📹 标题：{title}
🔗 链接：{video_url}
⏱️ 时长：{video_duration}秒
"""
        else:
            return f"❌ 消息发送失败：{result}"

    except Exception as e:
        return f"❌ 发送异常：{str(e)}"


@tool
def send_feishu_card_notification(
    title: str,
    content: str,
    video_url: str = None,
    button_text: str = "查看视频"
) -> str:
    """
    发送交互式卡片通知到飞书。

    Args:
        title: 卡片标题
        content: 卡片内容（支持Markdown）
        video_url: 视频URL（可选，如果有则显示按钮）
        button_text: 按钮文本（默认"查看视频"）

    Returns:
        发送结果

    Example:
        send_feishu_card_notification(
            title="视频生成完成",
            content="**线香产品介绍视频**已生成完成\n\n时长：60秒",
            video_url="https://example.com/video.mp4"
        )
    """
    ctx = request_context.get() or new_context(method="send_feishu_card_notification")

    try:
        # 构建卡片元素
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": content
                }
            }
        ]

        # 如果有视频URL，添加按钮
        if video_url:
            actions = [
                {
                    "tag": "button",
                    "text": {
                        "content": button_text,
                        "tag": "plain_text"
                    },
                    "type": "primary",
                    "url": video_url
                }
            ]
            elements.append({"tag": "action", "actions": actions})

        # 构建卡片
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    }
                },
                "elements": elements
            }
        }

        response = requests.post(FEISHU_WEBHOOK_URL, json=payload)
        result = response.json()

        if result.get("StatusCode") == 0 or result.get("code") == 0:
            return f"""✅ 卡片通知发送成功！

📋 标题：{title}
📝 内容：{content[:100]}...
"""
        else:
            return f"❌ 消息发送失败：{result}"

    except Exception as e:
        return f"❌ 发送异常：{str(e)}"


@tool
def send_feishu_batch_notification(
    videos: list
) -> str:
    """
    批量发送视频通知到飞书。

    Args:
        videos: 视频列表，每个元素包含 title, url, description, duration

    Example:
        send_feishu_batch_notification([
            {"title": "视频1", "url": "https://...", "description": "描述1", "duration": 60},
            {"title": "视频2", "url": "https://...", "description": "描述2", "duration": 45}
        ])
    """
    ctx = request_context.get() or new_context(method="send_feishu_batch_notification")

    try:
        # 构建批量通知内容
        content_text = f"📦 批量视频生成完成！共 {len(videos)} 个视频\n\n"

        for i, video in enumerate(videos, 1):
            title = video.get("title", f"视频{i}")
            url = video.get("url", "")
            duration = video.get("duration", 0)
            description = video.get("description", "")

            minutes = duration // 60
            seconds = duration % 60

            content_text += f"**{i}. {title}**\n"
            if description:
                content_text += f"   📝 {description}\n"
            content_text += f"   ⏱️ {minutes}分{seconds}秒\n"
            content_text += f"   🔗 {url}\n\n"

        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"📹 批量视频通知（{len(videos)}个）",
                        "content": [
                            [
                                {"tag": "text", "text": content_text}
                            ]
                        ]
                    }
                }
            }
        }

        response = requests.post(FEISHU_WEBHOOK_URL, json=payload)
        result = response.json()

        if result.get("StatusCode") == 0 or result.get("code") == 0:
            return f"✅ 批量通知发送成功！共发送 {len(videos)} 个视频通知"
        else:
            return f"❌ 消息发送失败：{result}"

    except Exception as e:
        return f"❌ 发送异常：{str(e)}"
