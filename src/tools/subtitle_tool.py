from langchain.tools import tool
import requests
import os
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk.video_edit import (
    VideoEditClient,
    SubtitleConfig,
    FontPosConfig,
    TextItem
)

OUTPUT_DIR = "/workspace/projects/assets/subtitle_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@tool
def generate_subtitle_from_audio(
    audio_url: str,
    subtitle_type: str = "srt",
    output_filename: str = None
) -> str:
    """
    从音频/视频中自动生成字幕文件。

    使用语音识别技术将音频转换为带时间戳的字幕文件。

    Args:
        audio_url: 音频或视频文件 URL
        subtitle_type: 字幕格式（srt 或 webvtt）
        output_filename: 输出文件名（不含扩展名）

    Returns:
        生成的字幕文件信息

    Example:
        generate_subtitle_from_audio(
            audio_url="https://example.com/narration.mp3",
            subtitle_type="srt"
        )
    """
    ctx = new_context(method="generate_subtitle_from_audio")

    # 处理本地路径
    if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
        # 尝试上传到对象存储
        return f"ERROR: 本地文件暂不支持，请提供公开 URL。\n本地路径：{audio_url}"

    # 初始化视频编辑客户端
    client = VideoEditClient(ctx=ctx)

    try:
        # 生成字幕
        response = client.audio_to_subtitle(
            source=audio_url,
            subtitle_type=subtitle_type,
            url_expire=86400  # 24小时
        )

        # 下载到本地
        if not output_filename:
            import time
            output_filename = f"subtitle_{int(time.time())}"

        output_path = os.path.join(OUTPUT_DIR, f"{output_filename}.{subtitle_type}")

        try:
            response_download = requests.get(response.url, timeout=120)
            response_download.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response_download.content)

            # 读取字幕内容预览
            with open(output_path, 'r', encoding='utf-8') as f:
                subtitle_preview = f.read()[:500]

            return f"""✅ 字幕生成成功！

📝 字幕信息：
  - 音频 URL：{audio_url}
  - 格式：{subtitle_type}
  - 在线 URL：{response.url}
  - URL 有效期：24 小时

📁 文件信息：
  - 本地路径：{output_path}
  - 已下载：是

📄 字幕内容预览：
{subtitle_preview}...

💡 提示：
  - 字幕已保存到本地，可直接使用
  - 如需将字幕添加到视频，请使用 add_subtitles_to_video 工具
"""

        except Exception as e:
            return f"""✅ 字幕生成成功！（本地下载失败）

📝 字幕信息：
  - 音频 URL：{audio_url}
  - 格式：{subtitle_type}
  - 在线 URL：{response.url}
  - URL 有效期：24 小时

❌ 本地下载失败：{str(e)}

💡 提示：
  - 您可以直接使用在线 URL 进行后续操作
"""

    except Exception as e:
        return f"❌ 字幕生成失败：{str(e)}"


@tool
def add_subtitles_to_video(
    video_url: str,
    text_list: list = None,
    subtitle_url: str = None,
    font_size: int = 36,
    font_color: str = "#FFFFFFFF",
    background_color: str = "#00000000",
    border_width: int = 1,
    border_color: str = "#00000088",
    position_y: str = "90%",
    output_filename: str = None
) -> str:
    """
    为视频添加字幕。

    支持两种方式：
    1. 直接传入文本列表（带时间戳）
    2. 使用字幕文件（SRT/VTT/ASS）

    Args:
        video_url: 视频文件 URL
        text_list: 文本列表（每个元素包含 start_time, end_time, text）
            例如：[{"start_time": 0.0, "end_time": 3.0, "text": "第一句"}]
        subtitle_url: 字幕文件 URL（SRT/VTT/ASS）
        font_size: 字体大小（像素），默认 36
        font_color: 字体颜色（十六进制），默认白色
        background_color: 背景颜色，默认透明
        border_width: 边框宽度（像素），默认 1
        border_color: 边框颜色，默认半透明黑色
        position_y: 字幕位置（Y轴百分比），默认 90%
        output_filename: 输出文件名（不含扩展名）

    Returns:
        添加字幕后的视频 URL 和文件信息

    Example:
        # 方式1：使用文本列表
        add_subtitles_to_video(
            video_url="https://example.com/video.mp4",
            text_list=[
                {"start_time": 0.0, "end_time": 3.0, "text": "欢迎来到香道文化"},
                {"start_time": 3.0, "end_time": 6.0, "text": "今天我们来讲讲线香"}
            ]
        )

        # 方式2：使用字幕文件
        add_subtitles_to_video(
            video_url="https://example.com/video.mp4",
            subtitle_url="https://example.com/subtitles.srt"
        )

        # 自定义样式
        add_subtitles_to_video(
            video_url="https://example.com/video.mp4",
            text_list=[{"start_time": 0.0, "end_time": 5.0, "text": "测试字幕"}],
            font_size=40,
            font_color="#FFFF00FF",  # 黄色
            border_width=2,
            position_y="85%"
        )
    """
    ctx = new_context(method="add_subtitles_to_video")

    # 处理本地路径
    if not video_url.startswith("http://") and not video_url.startswith("https://"):
        return f"ERROR: 视频暂不支持本地路径，请提供公开 URL。\n本地路径：{video_url}"

    if subtitle_url and not subtitle_url.startswith("http://") and not subtitle_url.startswith("https://"):
        return f"ERROR: 字幕文件暂不支持本地路径，请提供公开 URL。\n本地路径：{subtitle_url}"

    # 初始化视频编辑客户端
    client = VideoEditClient(ctx=ctx)

    # 配置字幕样式
    subtitle_config = SubtitleConfig(
        font_pos_config=FontPosConfig(
            pos_x="0",
            pos_y=position_y,
            width="100%",
            height="10%"
        ),
        font_size=font_size,
        font_color=font_color,
        font_type="1525745",  # 默认字体
        background_color=background_color,
        background_border_width=0,
        border_width=border_width,
        border_color=border_color
    )

    # 准备文本项
    text_items = None
    if text_list:
        text_items = [
            TextItem(
                start_time=item["start_time"],
                end_time=item["end_time"],
                text=item["text"]
            )
            for item in text_list
        ]

    try:
        # 添加字幕
        response = client.add_subtitles(
            video=video_url,
            subtitle_config=subtitle_config,
            subtitle_url=subtitle_url,
            text_list=text_items,
            url_expire=86400  # 24小时
        )

        # 下载到本地
        if not output_filename:
            import time
            output_filename = f"video_with_subtitles_{int(time.time())}"

        output_path = os.path.join(OUTPUT_DIR, f"{output_filename}.mp4")

        try:
            response_download = requests.get(response.url, timeout=120)
            response_download.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response_download.content)
        except Exception as e:
            output_path = f"本地下载失败：{str(e)}"

        return f"""✅ 字幕添加成功！

🎬 视频信息：
  - 视频 URL：{video_url}
  - 输出时长：{response.video_meta.duration if hasattr(response, 'video_meta') and response.video_meta else '未知'} 秒

📝 字幕信息：
  - 方式：{'字幕文件' if subtitle_url else '文本列表'}
  - 字幕数量：{len(text_list) if text_list else '未知'}
  - 字体大小：{font_size}px
  - 字幕位置：{position_y}

🎨 样式设置：
  - 字体颜色：{font_color}
  - 背景颜色：{background_color}
  - 边框宽度：{border_width}px
  - 边框颜色：{border_color}

📁 文件信息：
  - 在线 URL：{response.url}
  - 本地路径：{output_path}
  - URL 有效期：24 小时

💡 提示：
  - 视频已保存到本地，可直接使用
  - 这是最终成片，无需进一步处理
"""

    except Exception as e:
        return f"❌ 字幕添加失败：{str(e)}"


@tool
def auto_subtitle_pipeline(
    video_url: str,
    font_size: int = 36,
    position_y: str = "90%",
    output_filename: str = None
) -> str:
    """
    一键自动为视频添加字幕（从音频生成字幕并添加到视频）。

    完整流程：
    1. 从视频中提取音频
    2. 识别音频内容，生成字幕
    3. 将字幕添加到视频

    Args:
        video_url: 视频文件 URL
        font_size: 字体大小（像素），默认 36
        position_y: 字幕位置（Y轴百分比），默认 90%
        output_filename: 输出文件名（不含扩展名）

    Returns:
        添加字幕后的视频 URL 和文件信息

    Example:
        auto_subtitle_pipeline(
            video_url="https://example.com/video.mp4"
        )
    """
    ctx = new_context(method="auto_subtitle_pipeline")

    try:
        # 步骤1：生成字幕
        subtitle_result = generate_subtitle_from_audio(
            audio_url=video_url,
            subtitle_type="srt"
        )

        if "ERROR" in subtitle_result or "❌" in subtitle_result:
            return f"❌ 步骤1（生成字幕）失败：\n{subtitle_result}"

        # 提取字幕 URL
        import re
        url_match = re.search(r'在线 URL：(https?://[^\s]+)', subtitle_result)
        if not url_match:
            return f"❌ 无法提取字幕 URL：{subtitle_result}"

        subtitle_url = url_match.group(1)

        # 步骤2：添加字幕到视频
        video_result = add_subtitles_to_video(
            video_url=video_url,
            subtitle_url=subtitle_url,
            font_size=font_size,
            position_y=position_y,
            output_filename=output_filename
        )

        if "ERROR" in video_result or "❌" in video_result:
            return f"❌ 步骤2（添加字幕）失败：\n{video_result}"

        return f"""✅ 自动字幕添加完成！（完整流程）

🎬 流程摘要：
  步骤1：从音频生成字幕 ✅
  步骤2：将字幕添加到视频 ✅

{video_result}
"""

    except Exception as e:
        return f"❌ 自动字幕流程失败：{str(e)}"
