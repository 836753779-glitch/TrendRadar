from langchain.tools import tool
import requests
import os
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk import TTSClient

OUTPUT_DIR = "/workspace/projects/assets/tts_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@tool
def text_to_speech(
    text: str,
    speaker: str = "zh_female_xiaohe_uranus_bigtts",
    output_filename: str = None,
    audio_format: str = "mp3",
    sample_rate: int = 24000,
    speech_rate: int = 0,
    loudness_rate: int = 0
) -> str:
    """
    将文本转换为语音音频（TTS 语音合成）。

    支持多种声音、音质和语速调整，适用于视频配音、音频内容生成等场景。

    Args:
        text: 要合成的文本内容
        speaker: 声音/说话人 ID（见下方可选声音列表）
        output_filename: 输出文件名（不含扩展名），默认自动生成
        audio_format: 音频格式，支持 mp3/pcm/ogg_opus
        sample_rate: 采样率（8000-48000 Hz），默认 24000
        speech_rate: 语速调整（-50 到 100），0 为正常
        loudness_rate: 音量调整（-50 到 100），0 为正常

    Returns:
        生成的音频文件路径（本地保存）和 URL

    可选声音列表：

    **通用类**：
    - zh_female_xiaohe_uranus_bigtts - 小禾（默认，通用女声）
    - zh_female_vv_uranus_bigtts - Vivi（中英文双语）
    - zh_male_m191_uranus_bigtts - 云舟（男声）
    - zh_male_taocheng_uranus_bigtts - 小天（男声）

    **有声书/阅读类**：
    - zh_female_xueayi_saturn_bigtts - 儿童有声书

    **视频配音类**：
    - zh_male_dayi_saturn_bigtts - 大意（男声）
    - zh_female_mizai_saturn_bigtts - 米哉（女声）
    - zh_female_jitangnv_saturn_bigtts - 鸡汤女声
    - zh_female_meilinvyou_saturn_bigtts - 迷人女友
    - zh_female_santongyongns_saturn_bigtts - 顺通女声
    - zh_male_ruyayichen_saturn_bigtts - 优雅男声

    **角色扮演类**：
    - saturn_zh_female_keainvsheng_tob - 可爱女生
    - saturn_zh_female_tiaopigongzhu_tob - 调皮公主
    - saturn_zh_male_shuanglangshaonian_tob - 爽朗少年
    - saturn_zh_male_tiancaitongzhuo_tob - 天才同桌
    - saturn_zh_female_cancan_tob - 知性灿灿

    Example:
        # 默认声音（小禾）
        text_to_speech("欢迎来到香道文化传播")

        # 使用不同声音（优雅男声）
        text_to_speech(
            text="今天我们来讲讲香道文化",
            speaker="zh_male_ruyayichen_saturn_bigtts"
        )

        # 调整语速和音量
        text_to_speech(
            text="快速朗读测试",
            speech_rate=30,
            loudness_rate=10
        )

        # 高质量音频
        text_to_speech(
            text="高质量音频测试",
            sample_rate=48000
        )
    """
    ctx = new_context(method="text_to_speech")

    # 生成输出文件名
    if not output_filename:
        import time
        output_filename = f"tts_{int(time.time())}"

    # 生成完整输出路径
    output_path = os.path.join(OUTPUT_DIR, f"{output_filename}.{audio_format}")

    # 初始化 TTS 客户端
    client = TTSClient(ctx=ctx)

    # 生成音频
    audio_url, audio_size = client.synthesize(
        uid="video_agent",
        text=text,
        speaker=speaker,
        audio_format=audio_format,
        sample_rate=sample_rate,
        speech_rate=speech_rate,
        loudness_rate=loudness_rate
    )

    # 下载音频文件到本地
    try:
        response = requests.get(audio_url, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        # 计算音频时长（估算）
        # 假设平均语速为每秒 3-4 个汉字（中文）或 2-3 个英文单词
        # 更精确的方法是使用音频库获取实际时长
        import wave
        if audio_format == "mp3":
            # 对于 MP3，使用简单的估算
            duration_est = len(text) / 4.0  # 估算值
        else:
            duration_est = len(text) / 4.0

        return f"""✅ 语音合成成功！

🎤 语音信息：
  - 声音：{speaker}
  - 文本：{text[:50]}{'...' if len(text) > 50 else ''}
  - 文件大小：{audio_size} 字节
  - 估算时长：{duration_est:.1f} 秒

📁 文件信息：
  - 本地路径：{output_path}
  - 在线 URL：{audio_url}
  - 格式：{audio_format}
  - 采样率：{sample_rate} Hz

🎛️ 参数设置：
  - 语速调整：{speech_rate}（0=正常）
  - 音量调整：{loudness_rate}（0=正常）

💡 提示：
  - 音频已保存到本地，可直接用于视频合成
  - 在线 URL 可用于预览和下载
"""

    except Exception as e:
        return f"❌ 音频下载失败：{str(e)}\n\n在线 URL：{audio_url}\n您可以直接使用在线 URL 进行后续操作。"


@tool
def batch_text_to_speech(
    texts: list,
    speaker: str = "zh_female_xiaohe_uranus_bigtts",
    output_prefix: str = "batch_tts",
    audio_format: str = "mp3"
) -> str:
    """
    批量将多个文本转换为语音音频。

    适用于生成多段配音（如分镜配音、分段讲解等）。

    Args:
        texts: 文本列表，每个元素将生成一个音频文件
        speaker: 声音/说话人 ID
        output_prefix: 输出文件名前缀
        audio_format: 音频格式

    Returns:
        生成的音频文件列表信息

    Example:
        batch_text_to_speech([
            "第一段文案内容",
            "第二段文案内容",
            "第三段文案内容"
        ])
    """
    ctx = new_context(method="batch_text_to_speech")

    results = []
    client = TTSClient(ctx=ctx)

    for i, text in enumerate(texts, 1):
        output_filename = f"{output_prefix}_{i}"
        output_path = os.path.join(OUTPUT_DIR, f"{output_filename}.{audio_format}")

        try:
            # 生成音频
            audio_url, audio_size = client.synthesize(
                uid="video_agent",
                text=text,
                speaker=speaker,
                audio_format=audio_format
            )

            # 下载音频文件
            response = requests.get(audio_url, timeout=60)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response.content)

            results.append({
                "index": i,
                "text": text,
                "local_path": output_path,
                "url": audio_url,
                "size": audio_size
            })

        except Exception as e:
            results.append({
                "index": i,
                "text": text,
                "error": str(e)
            })

    # 格式化输出
    output_lines = ["✅ 批量语音合成完成！\n"]
    output_lines.append(f"📊 总计：{len(texts)} 段文本\n")

    for result in results:
        if "error" in result:
            output_lines.append(f"\n❌ 第 {result['index']} 段失败：")
            output_lines.append(f"   文本：{result['text'][:30]}...")
            output_lines.append(f"   错误：{result['error']}")
        else:
            output_lines.append(f"\n✅ 第 {result['index']} 段：")
            output_lines.append(f"   文本：{result['text'][:50]}{'...' if len(result['text']) > 50 else ''}")
            output_lines.append(f"   本地：{result['local_path']}")
            output_lines.append(f"   URL：{result['url']}")

    output_lines.append(f"\n📁 输出目录：{OUTPUT_DIR}")

    return "\n".join(output_lines)
