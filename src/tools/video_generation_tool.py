from langchain.tools import tool
from coze_coding_dev_sdk.video import VideoGenerationClient, TextContent, ImageURLContent, ImageURL
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def text_to_video(
    prompt: str,
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    watermark: bool = False,
    camerafixed: bool = False,
    model: str = "doubao-seedance-1-5-pro-251215"
) -> str:
    """
    使用AI根据文本描述生成视频片段。

    支持多种AI视频生成工具，包括小云雀（即梦）和 Lab TV SEEDANCE 2.0。
    适用于创建剧情视频、场景展示、产品介绍等内容。
    支持多种分辨率和比例，可控制镜头稳定性。

    Args:
        prompt: 视频场景的文本描述，需要详细描述画面内容、风格、氛围等
        resolution: 视频分辨率，支持 480p/720p/1080p，默认720p
        ratio: 视频比例，支持 16:9/9:16/1:1/4:3/3:4/21:9/adaptive，默认16:9（适合横屏）
        duration: 视频时长（秒），范围4-12秒，默认5秒
        watermark: 是否添加水印，默认false
        camerafixed: 是否固定镜头位置，默认false（固定镜头适合静态场景）
        model: 使用的AI视频生成模型，可选值：
            - "doubao-seedance-1-5-pro-251215": SEEDANCE 1.5 Pro（当前默认，支持高质量视频生成）
            未来可能支持的模型：
            - "jimeng": 小云雀（即梦）
            - "seedance-2-0": Lab TV 内置 SEEDANCE 2.0

    Returns:
        生成的视频URL，如果生成失败则返回错误信息

    Example:
        text_to_video(prompt="一个女孩在森林里散步，阳光透过树叶洒下来，电影感，高质量", model="doubao-seedance-1-5-pro-251215")
    """
    ctx = request_context.get() or new_context(method="text_to_video")

    try:
        client = VideoGenerationClient(ctx=ctx)

        # 当前环境只支持 doubao-seedance-1-5-pro-251215 模型
        # 如果用户指定了其他模型，使用默认模型并提示
        actual_model = model
        if model not in ["doubao-seedance-1-5-pro-251215"]:
            actual_model = "doubao-seedance-1-5-pro-251215"

        video_url, response, last_frame_url = client.video_generation(
            content_items=[TextContent(text=prompt)],
            model=actual_model,
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            watermark=watermark,
            camerafixed=camerafixed,
            generate_audio=True,
            max_wait_time=900
        )

        if video_url:
            tool_name = "SEEDANCE 1.5 Pro"
            if model != actual_model:
                tool_name = f"{model} (已自动切换到 SEEDANCE 1.5 Pro)"
            return f"视频生成成功！使用工具: {tool_name}\n视频URL: {video_url}\n视频时长: {duration}秒，分辨率: {resolution}，比例: {ratio}"
        else:
            return f"视频生成失败，状态: {response.get('status', 'unknown')}"

    except Exception as e:
        return f"视频生成过程中出现错误: {str(e)}"
