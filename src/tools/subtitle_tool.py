from langchain.tools import tool
from coze_coding_dev_sdk.video_edit import VideoEditClient, SubtitleConfig, FontPosConfig, TextItem
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def add_subtitles(
    video_url: str,
    subtitles: str,
    font_size: int = 36,
    font_color: str = "#FFFFFFFF",
    position_y: str = "90%"
) -> str:
    """
    为视频添加字幕，支持自定义字体样式和位置。

    适用于口播类视频、对话视频、需要文字说明的视频内容。
    字幕格式：每行字幕格式为 "开始时间-结束时间:字幕内容"，用换行分隔多个字幕。

    Args:
        video_url: 原始视频URL
        subtitles: 字幕内容，格式为每行 "开始时间-结束时间:字幕内容"
                  例如：
                  "0.0-3.0:大家好，欢迎来到我的频道
                   3.0-6.0:今天我们要讨论的话题是人工智能"
        font_size: 字体大小（像素），默认36
        font_color: 字体颜色（十六进制格式），默认白色 #FFFFFFFF
        position_y: 字幕垂直位置（百分比），默认90%（底部）

    Returns:
        添加字幕后的视频URL，如果失败则返回错误信息

    Example:
        add_subtitles(
            video_url="https://example.com/video.mp4",
            subtitles="0.0-3.0:大家好\\n3.0-6.0:欢迎观看",
            font_size=40
        )
    """
    ctx = request_context.get() or new_context(method="add_subtitles")

    try:
        client = VideoEditClient(ctx=ctx)

        # 解析字幕内容
        text_list = []
        lines = subtitles.strip().split("\n")

        for line in lines:
            if not line.strip():
                continue

            # 解析格式: 开始时间-结束时间:字幕内容
            parts = line.split(":")
            if len(parts) >= 2:
                time_range = parts[0]
                text = ":".join(parts[1:])  # 处理字幕内容中可能包含冒号的情况

                time_parts = time_range.split("-")
                if len(time_parts) == 2:
                    try:
                        start = float(time_parts[0])
                        end = float(time_parts[1])

                        text_list.append(TextItem(
                            start_time=start,
                            end_time=end,
                            text=text.strip()
                        ))
                    except ValueError:
                        continue

        if not text_list:
            return "字幕格式错误，请使用格式: 开始时间-结束时间:字幕内容"

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
            font_type="1525745",
            background_color="#00000000",
            background_border_width=0,
            border_width=1,
            border_color="#00000088"
        )

        response = client.add_subtitles(
            video=video_url,
            subtitle_config=subtitle_config,
            text_list=text_list
        )

        return f"字幕添加成功！\n添加字幕后的视频URL: {response.url}\n共添加 {len(text_list)} 条字幕"

    except Exception as e:
        return f"添加字幕过程中出现错误: {str(e)}"
