from langchain.tools import tool
from coze_coding_dev_sdk.video import (
    VideoGenerationClient,
    TextContent,
    ImageURLContent,
    ImageURL
)
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def text_to_video_with_character(
    prompt: str,
    character_image_url: str,
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    watermark: bool = False,
    camerafixed: bool = False,
    model: str = "doubao-seedance-1-5-pro-251215"
) -> str:
    """
    使用AI根据文本描述和角色参考图片生成视频片段。

    通过指定角色参考图片作为首帧，确保生成的视频中人物保持一致。
    适用于需要固定角色形象的短视频内容，如知识分享、产品介绍等。

    Args:
        prompt: 视频场景的文本描述，需要详细描述画面内容、风格、氛围等
        character_image_url: 角色参考图片的URL，必须是公开访问的图片链接。将作为视频的首帧，确保人物一致性
        resolution: 视频分辨率，支持 480p/720p/1080p，默认720p
        ratio: 视频比例，支持 16:9/9:16/1:1/4:3/3:4/21:9/adaptive，默认16:9（适合横屏）
        duration: 视频时长（秒），范围4-12秒，默认5秒
        watermark: 是否添加水印，默认false
        camerafixed: 是否固定镜头位置，默认false（固定镜头适合静态场景）
        model: 使用的AI视频生成模型，默认 doubao-seedance-1-5-pro-251215

    Returns:
        生成的视频URL，如果生成失败则返回错误信息

    Example:
        # 使用角色参考图片生成视频
        text_to_video_with_character(
            prompt="人物在茶室中介绍香道知识，面带微笑看向镜头，温暖治愈",
            character_image_url="https://example.com/character.jpg"
        )
    """
    ctx = request_context.get() or new_context(method="text_to_video_with_character")

    try:
        client = VideoGenerationClient(ctx=ctx)

        # 构建内容列表：角色参考图片作为首帧 + 文本描述
        content_items = [
            ImageURLContent(
                image_url=ImageURL(url=character_image_url),
                role="first_frame"  # 使用首帧模式，确保人物一致性
            ),
            TextContent(text=prompt)
        ]

        # 尝试调用视频生成
        video_url, response, last_frame_url = client.video_generation(
            content_items=content_items,
            model=model,
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            watermark=watermark,
            camerafixed=camerafixed,
            generate_audio=True,
            max_wait_time=900
        )

        if video_url:
            return f"✅ 视频生成成功！（使用角色参考图片）\n📹 模型: {model}\n🔗 视频URL: {video_url}\n⏱️ 视频时长: {duration}秒\n📐 分辨率: {resolution} ({ratio})\n📸 首帧URL: {character_image_url}"
        else:
            return f"❌ 视频生成失败，状态: {response.get('status', 'unknown')}"

    except Exception as e:
        return f"视频生成过程中出现错误: {str(e)}"
