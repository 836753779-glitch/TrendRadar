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
    model: str = "doubao-seedance-1-0-pro-250528"
) -> str:
    """
    使用AI根据文本描述生成视频片段。

    支持多种AI视频生成工具，包括火山方舟 Seedance、小云雀（即梦）和 LIBTV SEEDANCE 2.0。
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
            - "doubao-seedance-1-0-pro-250528": 火山方舟 Seedance 1.0 Pro（当前推荐，需要配置火山方舟API密钥）
            - "doubao-seedance-1-5-pro-251215": SEEDANCE 1.5 Pro（备选方案）
            - "doubao-seedance-2-0": SEEDANCE 2.0（LIBTV 内置，需要配置LIBTV API密钥）
            - "jimeng": 小云雀（即梦，需要配置LIBTV API密钥）

    Returns:
        生成的视频URL，如果生成失败则返回错误信息

    Example:
        # 使用火山方舟 Seedance 1.0 Pro（当前推荐）
        text_to_video(prompt="一个女孩在森林里散步，阳光透过树叶洒下来，电影感，高质量")

        # 使用 SEEDANCE 2.0（LIBTV，需配置密钥）
        text_to_video(prompt="一个女孩在森林里散步，阳光透过树叶洒下来，电影感，高质量", model="doubao-seedance-2-0")

        # 使用小云雀（即梦，需配置密钥）
        text_to_video(prompt="一个女孩在森林里散步，阳光透过树叶洒下来，电影感，高质量", model="jimeng")
    """
    ctx = request_context.get() or new_context(method="text_to_video")

    try:
        client = VideoGenerationClient(ctx=ctx)

        # 模型选择逻辑
        # 优先使用用户指定的模型，如果指定模型不可用则降级到火山方舟 Seedance 1.0 Pro
        actual_model = model

        # 验证模型是否在支持列表中
        supported_models = [
            "doubao-seedance-1-0-pro-250528",  # 火山方舟 Seedance 1.0 Pro（推荐）
            "doubao-seedance-1-5-pro-251215",  # SEEDANCE 1.5 Pro（备选）
            "doubao-seedance-2-0",            # SEEDANCE 2.0（LIBTV）
            "jimeng"                           # 小云雀（即梦）
        ]

        if model not in supported_models:
            actual_model = "doubao-seedance-1-0-pro-250528"
            print(f"⚠️ 模型 '{model}' 不在支持列表中，已自动切换到火山方舟 Seedance 1.0 Pro")

        # 尝试调用视频生成
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
            # 映射模型到工具名称
            model_to_tool = {
                "doubao-seedance-1-0-pro-250528": "火山方舟 Seedance 1.0 Pro (推荐)",
                "doubao-seedance-1-5-pro-251215": "SEEDANCE 1.5 Pro (备选)",
                "doubao-seedance-2-0": "SEEDANCE 2.0 (LIBTV)",
                "jimeng": "小云雀（即梦）"
            }
            tool_name = model_to_tool.get(actual_model, actual_model)

            if model != actual_model:
                tool_name = f"{model} (已自动切换到 {model_to_tool.get(actual_model, actual_model)})"

            return f"✅ 视频生成成功！\n📹 使用工具: {tool_name}\n🔗 视频URL: {video_url}\n⏱️ 视频时长: {duration}秒\n📐 分辨率: {resolution} ({ratio})"
        else:
            return f"❌ 视频生成失败，状态: {response.get('status', 'unknown')}"

    except Exception as e:
        # 如果当前模型调用失败，尝试降级到备选模型
        if model in ["doubao-seedance-2-0", "jimeng"]:
            try:
                print(f"⚠️ 模型 '{model}' 调用失败，尝试降级到火山方舟 Seedance 1.0 Pro...")
                client = VideoGenerationClient(ctx=ctx)
                video_url, response, last_frame_url = client.video_generation(
                    content_items=[TextContent(text=prompt)],
                    model="doubao-seedance-1-5-pro-251215",  # 降级到已验证可用的模型
                    resolution=resolution,
                    ratio=ratio,
                    duration=duration,
                    watermark=watermark,
                    camerafixed=camerafixed,
                    generate_audio=True,
                    max_wait_time=900
                )

                if video_url:
                    return f"✅ 视频生成成功！（已自动降级）\n📹 使用工具: SEEDANCE 1.5 Pro (备选)\n🔗 视频URL: {video_url}\n⏱️ 视频时长: {duration}秒\n📐 分辨率: {resolution} ({ratio})"
            except Exception as e2:
                return f"❌ 视频生成失败（尝试降级后仍失败）: {str(e)}\n降级错误: {str(e2)}"

        return f"视频生成过程中出现错误: {str(e)}"
