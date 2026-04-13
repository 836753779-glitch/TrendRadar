from langchain.tools import tool
from coze_coding_dev_sdk.video import VideoGenerationClient, TextContent, ImageURLContent, ImageURL
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def image_to_video(
    first_frame_url: str,
    prompt: str = "",
    last_frame_url: str = "",
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    watermark: bool = False,
    return_last_frame: bool = True
) -> str:
    """
    基于参考图像生成视频，支持首帧或首尾帧模式。

    适用于将静态素材转化为动态视频，或实现场景的平滑过渡。
    使用首尾帧模式可以精确控制场景的起始和结束状态，实现更精确的镜头控制。

    Args:
        first_frame_url: 首帧图像URL（必须），作为视频的起始画面
        prompt: 文本提示词，可选，用于指导视频生成过程
        last_frame_url: 尾帧图像URL，可选，如果提供则使用首尾帧模式
        resolution: 视频分辨率，支持 480p/720p/1080p，默认720p
        ratio: 视频比例，支持 16:9/9:16/1:1/4:3/3:4/21:9/adaptive，默认16:9
        duration: 视频时长（秒），范围4-12秒，默认5秒
        watermark: 是否添加水印，默认false
        return_last_frame: 是否返回最后一帧，默认true（用于后续场景拼接）

    Returns:
        生成的视频URL和最后一帧URL，如果生成失败则返回错误信息

    Example:
        image_to_video(
            first_frame_url="https://example.com/scene1.jpg",
            prompt="缓慢平移镜头，展示森林的宁静氛围"
        )
    """
    ctx = request_context.get() or new_context(method="image_to_video")

    try:
        client = VideoGenerationClient(ctx=ctx)

        content_items = [
            ImageURLContent(
                image_url=ImageURL(url=first_frame_url),
                role="first_frame"
            )
        ]

        if prompt:
            content_items.append(TextContent(text=prompt))

        if last_frame_url:
            content_items.append(
                ImageURLContent(
                    image_url=ImageURL(url=last_frame_url),
                    role="last_frame"
                )
            )

        video_url, response, last_frame = client.video_generation(
            content_items=content_items,
            model="doubao-seedance-1-5-pro-251215",
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            watermark=watermark,
            return_last_frame=return_last_frame,
            generate_audio=True,
            max_wait_time=900
        )

        if video_url:
            result = f"图生视频成功！\n视频URL: {video_url}\n视频时长: {duration}秒，分辨率: {resolution}"
            if return_last_frame and last_frame:
                result += f"\n最后一帧URL: {last_frame}（可用于后续场景拼接）"
            return result
        else:
            return f"图生视频失败，状态: {response.get('status', 'unknown')}"

    except Exception as e:
        return f"图生视频过程中出现错误: {str(e)}"
