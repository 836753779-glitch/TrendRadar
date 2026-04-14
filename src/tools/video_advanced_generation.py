from langchain.tools import tool
from coze_coding_dev_sdk.video import VideoGenerationClient, TextContent, ImageURLContent, ImageURL
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def generate_video_with_both_frames(
    scene_description: str,
    first_frame_url: str,
    last_frame_url: str = None,
    narration_text: str = "角色正在讲解",
    model: str = "doubao-seedance-1-5-pro-251215",
    duration: int = 5,
    resolution: str = "720p",
    ratio: str = "9:16"
) -> str:
    """
    使用首帧和尾帧生成视频（推荐！确保动作连贯性）。

    这是解决物理错误和动作不连贯的最佳方案之一。

    优势：
    1. 人物从第一帧到最后一帧的动作自然过渡
    2. 减少穿模、穿桌等物理错误
    3. 确保人物位置和姿态的正确性

    Args:
        scene_description: 场景描述
        first_frame_url: 首帧图片URL（角色起始状态）
        last_frame_url: 尾帧图片URL（角色结束状态，可选）
        narration_text: 配音文本
        model: 视频模型（doubao-seedance-1-5-pro-251215 或 doubao-seedance-2-0-260128）
        duration: 视频时长（秒）
        resolution: 分辨率（480p/720p/1080p）
        ratio: 视频比例（9:16/16:9/1:1）

    Returns:
        生成的视频URL

    Example:
        generate_video_with_both_frames(
            scene_description="角色坐在茶桌前，从左侧转向右侧，手持线香展示",
            first_frame_url="https://.../character_start.jpg",
            last_frame_url="https://.../character_end.jpg",
            narration_text="这款线香..."
        )
    """
    ctx = new_context(method="generate_video_with_both_frames")

    # 初始化视频生成客户端
    client = VideoGenerationClient(ctx=ctx)

    # 构建内容项
    content_items = [
        TextContent(text=scene_description),
        ImageURLContent(
            image_url=ImageURL(url=first_frame_url),
            role="first_frame"
        )
    ]

    # 如果有尾帧，添加尾帧
    if last_frame_url:
        content_items.append(
            ImageURLContent(
                image_url=ImageURL(url=last_frame_url),
                role="last_frame"
            )
        )

    # 生成视频
    video_url, response, _ = client.video_generation(
        content_items=content_items,
        model=model,
        resolution=resolution,
        ratio=ratio,
        duration=duration,
        watermark=False
    )

    if video_url:
        return f"""✅ 视频生成成功（首帧+尾帧模式）

📹 视频信息：
  - 视频URL：{video_url}
  - 模型：{model}
  - 分辨率：{resolution}
  - 比例：{ratio}
  - 时长：{duration}秒

💡 优势：
  - 使用首帧和尾帧，确保动作自然过渡
  - 减少穿模、穿桌等物理错误
  - 人物位置和姿态保持正确
"""
    else:
        return f"❌ 视频生成失败：{response}"


@tool
def generate_video_fixed_camera(
    scene_description: str,
    character_image_url: str = None,
    model: str = "doubao-seedance-1-5-pro-251215",
    duration: int = 5,
    resolution: str = "720p",
    ratio: str = "9:16"
) -> str:
    """
    使用固定镜头生成视频（减少画面诡异）。

    固定镜头可以避免画面晃动、视角突变等问题。

    Args:
        scene_description: 场景描述
        character_image_url: 角色参考图片URL
        model: 视频模型
        duration: 视频时长（秒）
        resolution: 分辨率
        ratio: 视频比例

    Returns:
        生成的视频URL

    Example:
        generate_video_fixed_camera(
            scene_description="角色坐在茶桌前讲解线香，镜头固定",
            character_image_url="https://.../character.jpg"
        )
    """
    ctx = new_context(method="generate_video_fixed_camera")

    # 初始化视频生成客户端
    client = VideoGenerationClient(ctx=ctx)

    # 构建内容项
    content_items = [
        TextContent(text=f"{scene_description}。固定镜头，无剧烈晃动，画面稳定清晰。")
    ]

    # 如果有角色参考图片，添加首帧
    if character_image_url:
        content_items.append(
            ImageURLContent(
                image_url=ImageURL(url=character_image_url),
                role="first_frame"
            )
        )

    # 生成视频（固定镜头）
    video_url, response, _ = client.video_generation(
        content_items=content_items,
        model=model,
        resolution=resolution,
        ratio=ratio,
        duration=duration,
        watermark=False,
        camerafixed=True  # 固定镜头！
    )

    if video_url:
        return f"""✅ 视频生成成功（固定镜头模式）

📹 视频信息：
  - 视频URL：{video_url}
  - 模型：{model}
  - 分辨率：{resolution}
  - 比例：{ratio}
  - 时长：{duration}秒

💡 优势：
  - 固定镜头，画面稳定
  - 避免剧烈晃动和视角突变
  - 减少画面诡异、扭曲等问题
"""
    else:
        return f"❌ 视频生成失败：{response}"
