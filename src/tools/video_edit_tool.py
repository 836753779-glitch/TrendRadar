from langchain.tools import tool
from coze_coding_dev_sdk.video_edit import VideoEditClient
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def concat_videos(
    video_urls: str,
    transitions: str = ""
) -> str:
    """
    将多个视频片段拼接成一个完整的视频，支持添加转场效果。

    适用于将多个镜头场景拼接成完整视频，可以添加转场效果使画面过渡更流畅。
    支持多种转场效果，如百叶窗、圆形打开、旋转放大等。

    Args:
        video_urls: 多个视频URL，用逗号分隔（例如："url1,url2,url3"）
        transitions: 转场效果ID列表，用逗号分隔（可选）。如果不提供则直接拼接。
                    可用转场ID：
                    - 1182356: 百叶窗
                    - 1182360: 旋转放大
                    - 1182369: 梦幻放大
                    - 1182376: 圆形打开
                    - 1182371: 对角擦除
                    - 1182373: 立方转换
                    - 1182367: 故障转换
                    等更多转场效果（详见文档）

    Returns:
        拼接后的视频URL，如果失败则返回错误信息

    Example:
        concat_videos(
            video_urls="https://example.com/scene1.mp4,https://example.com/scene2.mp4,https://example.com/scene3.mp4",
            transitions="1182356,1182376"  # 百叶窗 + 圆形打开
        )
    """
    ctx = request_context.get() or new_context(method="concat_videos")

    try:
        client = VideoEditClient(ctx=ctx)

        # 解析视频URL列表
        videos = [url.strip() for url in video_urls.split(",") if url.strip()]

        if len(videos) < 2:
            return "至少需要2个视频才能进行拼接"

        # 解析转场效果
        transition_list = []
        if transitions:
            transition_list = [t.strip() for t in transitions.split(",") if t.strip()]

            # 转场数量应该是视频数量-1
            if len(transition_list) > len(videos) - 1:
                transition_list = transition_list[:len(videos) - 1]

        response = client.concat_videos(
            videos=videos,
            transitions=transition_list if transition_list else None
        )

        return f"视频拼接成功！\n拼接后的视频URL: {response.url}\n共拼接 {len(videos)} 个视频片段"

    except Exception as e:
        return f"视频拼接过程中出现错误: {str(e)}"


@tool
def trim_video(
    video_url: str,
    start_time: float,
    end_time: float
) -> str:
    """
    裁剪视频的指定时间段，提取需要的片段。

    适用于从长视频中提取精华片段，或去除不需要的部分。

    Args:
        video_url: 原始视频URL
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）

    Returns:
        裁剪后的视频URL，如果失败则返回错误信息

    Example:
        trim_video(
            video_url="https://example.com/video.mp4",
            start_time=5.0,
            end_time=20.0
        )
    """
    ctx = request_context.get() or new_context(method="trim_video")

    try:
        client = VideoEditClient(ctx=ctx)

        response = client.video_trim(
            video=video_url,
            start_time=start_time,
            end_time=end_time
        )

        duration = response.video_meta.duration if response.video_meta else 0

        return f"视频裁剪成功！\n裁剪后的视频URL: {response.url}\n裁剪时长: {duration}秒（{start_time}秒 - {end_time}秒）"

    except Exception as e:
        return f"视频裁剪过程中出现错误: {str(e)}"
