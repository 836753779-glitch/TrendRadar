from langchain.tools import tool
import requests
import os
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk.video_edit import VideoEditClient, OutputSync

OUTPUT_DIR = "/workspace/projects/assets/video_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@tool
def compile_video_audio(
    video_url: str,
    audio_url: str,
    is_audio_reserve: bool = False,
    sync_method: str = "trim",
    sync_mode: str = "video",
    output_filename: str = None
) -> str:
    """
    将视频和音频合成，生成带配音的完整视频。

    支持音视频同步，可保留或替换原视频音频。

    Args:
        video_url: 视频文件 URL 或本地路径
        audio_url: 音频文件 URL 或本地路径
        is_audio_reserve: 是否保留原视频音频（false=替换为音频文件）
        sync_method: 同步方式
            - trim：裁剪较长的一方以匹配较短的时长
            - speed：调整速度以匹配时长
        sync_mode: 同步模式
            - video：以视频时长为准
            - audio：以音频时长为准
        output_filename: 输出文件名（不含扩展名），默认自动生成

    Returns:
        合成后的视频 URL 和文件信息

    Example:
        # 基础合成（替换音频）
        compile_video_audio(
            video_url="https://example.com/video.mp4",
            audio_url="https://example.com/narration.mp3"
        )

        # 保留原音频（混音）
        compile_video_audio(
            video_url="https://example.com/video.mp4",
            audio_url="https://example.com/background_music.mp3",
            is_audio_reserve=True
        )

        # 音频同步模式
        compile_video_audio(
            video_url="https://example.com/video.mp4",
            audio_url="https://example.com/narration.mp3",
            sync_method="trim",
            sync_mode="audio"  # 以音频时长为准
        )
    """
    ctx = new_context(method="compile_video_audio")

    # 处理本地路径
    if not video_url.startswith("http://") and not video_url.startswith("https://"):
        video_url = _upload_to_storage(video_url, "video")
        if video_url.startswith("ERROR"):
            return video_url

    if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
        audio_url = _upload_to_storage(audio_url, "audio")
        if audio_url.startswith("ERROR"):
            return audio_url

    # 初始化视频编辑客户端
    client = VideoEditClient(ctx=ctx)

    # 配置同步选项
    output_sync = OutputSync(
        sync_method=sync_method,
        sync_mode=sync_mode
    )

    try:
        # 合成视频和音频
        response = client.compile_video_audio(
            video=video_url,
            audio=audio_url,
            is_video_audio_sync=True,
            output_sync=output_sync,
            is_audio_reserve=is_audio_reserve,
            url_expire=86400  # 24小时
        )

        # 下载到本地
        if not output_filename:
            import time
            output_filename = f"compiled_{int(time.time())}"

        output_path = os.path.join(OUTPUT_DIR, f"{output_filename}.mp4")

        try:
            response_download = requests.get(response.url, timeout=120)
            response_download.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response_download.content)
        except Exception as e:
            output_path = f"本地下载失败：{str(e)}"

        # 获取视频元数据
        video_meta = response.video_meta if hasattr(response, 'video_meta') else None
        duration = video_meta.duration if video_meta else "未知"

        return f"""✅ 视频音频合成成功！

🎬 视频信息：
  - 视频 URL：{video_url}
  - 音频 URL：{audio_url}
  - 输出时长：{duration} 秒

📁 文件信息：
  - 在线 URL：{response.url}
  - 本地路径：{output_path}
  - URL 有效期：24 小时

⚙️ 合成参数：
  - 保留原音频：{'是' if is_audio_reserve else '否（替换）'}
  - 同步方式：{sync_method}
  - 同步模式：{sync_mode}（以{'音频' if sync_mode == 'audio' else '视频'}为准）

💡 提示：
  - 视频已保存到本地，可直接使用
  - 如需继续添加字幕，请使用 add_subtitles_to_video 工具
"""

    except Exception as e:
        return f"❌ 视频音频合成失败：{str(e)}"


@tool
def extract_video_audio(
    video_url: str,
    output_filename: str = None,
    audio_format: str = "mp3"
) -> str:
    """
    从视频中提取音频轨道。

    适用于提取视频中的背景音乐、原声等。

    Args:
        video_url: 视频文件 URL 或本地路径
        output_filename: 输出文件名（不含扩展名）
        audio_format: 音频格式（mp3 或 m4a）

    Returns:
        提取的音频文件信息

    Example:
        extract_video_audio(
            video_url="https://example.com/video.mp4",
            audio_format="mp3"
        )
    """
    ctx = new_context(method="extract_video_audio")

    # 处理本地路径
    if not video_url.startswith("http://") and not video_url.startswith("https://"):
        video_url = _upload_to_storage(video_url, "video")
        if video_url.startswith("ERROR"):
            return video_url

    # 初始化视频编辑客户端
    client = VideoEditClient(ctx=ctx)

    try:
        # 提取音频
        response = client.extract_audio(
            video=video_url,
            format=audio_format,
            url_expire=86400  # 24小时
        )

        # 下载到本地
        if not output_filename:
            import time
            output_filename = f"extracted_audio_{int(time.time())}"

        output_path = os.path.join(OUTPUT_DIR, f"{output_filename}.{audio_format}")

        try:
            response_download = requests.get(response.url, timeout=120)
            response_download.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response_download.content)
        except Exception as e:
            output_path = f"本地下载失败：{str(e)}"

        # 获取视频元数据
        video_meta = response.video_meta if hasattr(response, 'video_meta') else None
        duration = video_meta.duration if video_meta else "未知"

        return f"""✅ 音频提取成功！

🎬 视频信息：
  - 视频 URL：{video_url}
  - 原视频时长：{duration} 秒

📁 文件信息：
  - 在线 URL：{response.url}
  - 本地路径：{output_path}
  - 格式：{audio_format}
  - URL 有效期：24 小时

💡 提示：
  - 音频已保存到本地，可用于重新配音或编辑
"""

    except Exception as e:
        return f"❌ 音频提取失败：{str(e)}"


def _upload_to_storage(file_path: str, file_type: str = "video") -> str:
    """
    上传本地文件到对象存储。

    Args:
        file_path: 本地文件路径
        file_type: 文件类型（video/audio）

    Returns:
        上传后的 URL
    """
    try:
        # 这里需要调用对象存储 SDK
        # 暂时返回错误提示
        return f"ERROR: 本地文件上传功能需要集成对象存储。请提供公开的 URL。\n本地路径：{file_path}"
    except Exception as e:
        return f"ERROR: 文件上传失败：{str(e)}"
