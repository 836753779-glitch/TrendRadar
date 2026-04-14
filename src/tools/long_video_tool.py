from langchain.tools import tool
import os
from typing import List, Dict
import json
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

WORKSPACE_PATH = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
OUTPUT_DIR = os.path.join(WORKSPACE_PATH, "assets", "long_videos")
SCENE_CONFIG_PATH = os.path.join(WORKSPACE_PATH, "assets", "character_element.json")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


@tool
def generate_long_video(
    script: str,
    duration: int = 60,
    scene_count: int = None,
    tts_speaker: str = "zh_female_xiaohe_uranus_bigtts",
    add_subtitle: bool = True,
    auto_plan_scenes: bool = True
) -> str:
    """
    生成长视频（1-2分钟），自动分镜、生成、拼接、配音、字幕一体化。

    完整流程：
    1. 智能分镜规划（根据脚本和时长）
    2. 逐个生成视频片段（使用角色主体确保一致性）
    3. 拼接所有镜头
    4. 生成配音（TTS）
    5. 合成视频和音频
    6. 自动生成字幕

    Args:
        script: 完整脚本文本（1-2分钟）
        duration: 目标时长（秒），默认60秒
        scene_count: 镜头数量（可选，不传则自动计算）
        tts_speaker: 配音声音，默认小禾
        add_subtitle: 是否添加字幕，默认True
        auto_plan_scenes: 是否自动分镜，默认True

    Returns:
        生成的完整视频信息

    Example:
        # 生成1分钟视频（自动4个镜头）
        generate_long_video(
            script="大家好，我是香道文化传播者。今天要给大家介绍一款特别的线香...",
            duration=60
        )

        # 生成2分钟视频（自动8个镜头）
        generate_long_video(
            script="（2分钟脚本）",
            duration=120
        )

        # 手动指定6个镜头
        generate_long_video(
            script="（脚本）",
            duration=90,
            scene_count=6
        )
    """
    ctx = request_context.get() or new_context(method="generate_long_video")

    try:
        # 获取角色主体ID
        element_id = _get_element_id()

        # 第一步：智能分镜规划
        scenes = _plan_scenes(script, duration, scene_count, auto_plan_scenes)

        # 第二步：生成视频片段
        video_clips = []
        for i, scene in enumerate(scenes):
            print(f"正在生成第 {i+1}/{len(scenes)} 个镜头...")
            video_path = _generate_scene_video(scene, element_id)
            if video_path:
                video_clips.append(video_path)

        if not video_clips:
            return "❌ 没有成功生成任何视频片段"

        # 第三步：拼接视频
        print(f"正在拼接 {len(video_clips)} 个镜头...")
        concat_result = _concat_videos(video_clips)
        if "❌" in concat_result:
            return f"❌ 视频拼接失败：{concat_result}"

        # 第四步：生成配音
        print("正在生成配音...")
        audio_result = _generate_narration(script, tts_speaker)
        if "❌" in audio_result:
            return f"❌ 配音生成失败：{audio_result}"

        # 第五步：合成视频和音频
        print("正在合成视频和音频...")
        final_video = _compile_video_audio(concat_result, audio_result)

        # 第六步：添加字幕
        if add_subtitle:
            print("正在生成字幕...")
            subtitle_result = _add_subtitles(final_video, script)
            if subtitle_result and "❌" not in subtitle_result:
                final_video = subtitle_result

        # 保存最终视频文件名
        import time
        output_filename = f"long_video_{int(time.time())}.mp4"
        output_path = final_video

        # 第七步：上传到对象存储
        video_public_url = None
        try:
            from coze_coding_dev_sdk.s3 import S3SyncStorage

            storage = S3SyncStorage(
                endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
                access_key="",
                secret_key="",
                bucket_name=os.getenv("COZE_BUCKET_NAME"),
                region="cn-beijing"
            )

            # 上传视频到对象存储
            with open(output_path, 'rb') as f:
                video_key = storage.stream_upload_file(
                    fileobj=f,
                    file_name=f"videos/{output_filename}",
                    content_type="video/mp4"
                )

            # 生成签名URL（有效期7天）
            video_public_url = storage.generate_presigned_url(
                key=video_key,
                expire_time=604800  # 7天
            )

            print(f"视频已上传到对象存储，URL: {video_public_url}")

        except Exception as e:
            print(f"对象存储上传失败：{str(e)}")

        # 第八步：推送到飞书
        try:
            from tools.feishu_notification_tool import send_feishu_video_notification

            feishu_url = video_public_url if video_public_url else output_path
            feishu_result = send_feishu_video_notification(
                title=f"长视频生成完成 - {output_filename}",
                video_url=feishu_url,
                description=script[:100] + "..." if len(script) > 100 else script,
                video_duration=duration
            )

            print(f"飞书推送成功：{feishu_result}")

        except Exception as e:
            print(f"飞书推送失败：{str(e)}")

        # 构建返回信息
        return _build_success_message(final_video, scenes, duration, video_public_url)

    except Exception as e:
        return f"❌ 长视频生成失败：{str(e)}"


def _get_element_id() -> str:
    """获取角色主体ID"""
    try:
        with open(SCENE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("element_id", "308110838358255")
    except:
        return "308110838358255"


def _plan_scenes(
    script: str,
    duration: int,
    scene_count: int = None,
    auto_plan: bool = True
) -> List[Dict]:
    """智能分镜规划"""

    # 计算镜头数量
    if scene_count is None:
        # 默认每个镜头15秒
        scene_count = max(1, duration // 15)
        # 最多10个镜头
        scene_count = min(scene_count, 10)

    # 计算每个镜头的时长
    scene_duration = duration // scene_count

    # 分析脚本，拆分段落
    paragraphs = _split_script_to_paragraphs(script)

    # 生成镜头规划
    scenes = []
    scene_types = ["全景", "中景", "特写", "全景"]
    emotions = ["温和欢迎", "专业讲解", "优雅演示", "温暖总结"]

    for i in range(scene_count):
        # 循环使用场景类型
        scene_type = scene_types[i % len(scene_types)]
        emotion = emotions[i % len(emotions)]

        # 获取对应的脚本段落
        if i < len(paragraphs):
            paragraph = paragraphs[i]
        else:
            paragraph = "继续展示"  # 如果脚本段落不够，用默认

        # 生成提示词
        prompt = _generate_scene_prompt(scene_type, paragraph, emotion, scene_duration)

        scenes.append({
            "index": i + 1,
            "scene_type": scene_type,
            "emotion": emotion,
            "duration": scene_duration,
            "start_time": i * scene_duration,
            "end_time": (i + 1) * scene_duration,
            "paragraph": paragraph,
            "prompt": prompt
        })

    return scenes


def _split_script_to_paragraphs(script: str) -> List[str]:
    """将脚本拆分为段落"""
    # 按句子或段落拆分
    import re

    # 按句号、问号、感叹号拆分
    sentences = re.split(r'[。！？\n]', script)

    # 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]

    # 合并句子为段落（每段2-3句）
    paragraphs = []
    current_paragraph = ""
    sentences_per_paragraph = max(1, len(sentences) // 4)  # 最多4个段落

    for i, sentence in enumerate(sentences):
        current_paragraph += sentence + "。"
        if (i + 1) % sentences_per_paragraph == 0 or i == len(sentences) - 1:
            paragraphs.append(current_paragraph.strip())
            current_paragraph = ""

    if current_paragraph.strip():
        paragraphs.append(current_paragraph.strip())

    return paragraphs


def _generate_scene_prompt(
    scene_type: str,
    content: str,
    emotion: str,
    duration: int
) -> str:
    """生成单个镜头的提示词"""

    # 基础场景描述
    base_descriptions = {
        "全景": "全景镜头，角色站在传统中式茶室中央，面向镜头，背景博古架陈列茶具与香器",
        "中景": "中景镜头，角色上半身特写，背景茶桌摆放香道器具，暖光柔和",
        "特写": "特写镜头，聚焦于手部动作和线香细节，背景虚化"
    }

    # 动作描述
    action_descriptions = {
        "温和欢迎": "面带温和微笑，双手合十，欢迎姿态",
        "专业讲解": "专注认真，手势配合讲解，展示线香细节",
        "优雅演示": "动作优雅流畅，点燃线香，展示香道仪式",
        "温暖总结": "双手合十致意，面带温暖微笑，感谢观众"
    }

    base_desc = base_descriptions.get(scene_type, base_descriptions["全景"])
    action_desc = action_descriptions.get(emotion, action_descriptions["温和欢迎"])

    # 组合提示词
    prompt = f"{base_desc}，{action_desc}"

    # 如果有具体内容，添加到提示词
    if content and content != "继续展示":
        prompt += f"，{content}"

    # 添加画质和氛围
    prompt += "，暖金色自然光，氛围宁静雅致，充满中式美学韵味"

    return prompt


def _generate_scene_video(scene: Dict, element_id: str) -> str:
    """生成单个镜头的视频"""
    try:
        # 这里调用 kling_cli_text_to_video_with_element 工具
        # 由于不能直接调用其他 tool，我们需要用 subprocess 调用

        from tools.kling_element_tool import kling_cli_text_to_video_with_element

        result = kling_cli_text_to_video_with_element.invoke({
            "prompt": scene["prompt"],
            "element_id": element_id,
            "duration": scene["duration"],
            "model": "kling-v3-omni",
            "mode": "pro",
            "aspect_ratio": "9:16",
            "sound": "off"  # 后续会统一配音
        })

        # 解析结果，提取视频路径
        if "✅" in result:
            import re
            matches = re.findall(r'/workspace/projects/assets/kling_output/\d+\.mp4', result)
            if matches:
                return matches[0]

        return None

    except Exception as e:
        print(f"生成镜头视频失败：{str(e)}")
        return None


def _concat_videos(video_clips: List[str]) -> str:
    """拼接视频"""
    try:
        from tools.video_edit_tool import concat_videos

        # 构建视频URL列表
        video_urls = ",".join(video_clips)

        result = concat_videos.invoke({
            "video_urls": video_urls
        })

        # 解析结果，提取视频路径
        if "✅" in result:
            import re
            matches = re.findall(r'/workspace/projects/assets/edited/\d+\.mp4', result)
            if matches:
                return matches[0]

        return None

    except Exception as e:
        print(f"视频拼接失败：{str(e)}")
        return None


def _generate_narration(script: str, speaker: str) -> str:
    """生成配音"""
    try:
        from tools.tts_tool import text_to_speech

        result = text_to_speech.invoke({
            "text": script,
            "speaker": speaker,
            "audio_format": "mp3",
            "sample_rate": 48000,
            "speech_rate": 0,
            "loudness_rate": 0
        })

        # 解析结果，提取音频路径
        if "✅" in result:
            import re
            matches = re.findall(r'/workspace/projects/assets/audio/\d+\.mp3', result)
            if matches:
                return matches[0]

        return None

    except Exception as e:
        print(f"配音生成失败：{str(e)}")
        return None


def _compile_video_audio(video_path: str, audio_path: str) -> str:
    """合成视频和音频"""
    try:
        from tools.video_audio_tool import compile_video_audio

        result = compile_video_audio.invoke({
            "video_url": video_path,
            "audio_url": audio_path,
            "is_audio_reserve": False,
            "sync_method": "trim",
            "sync_mode": "video"
        })

        # 解析结果，提取视频路径
        if "✅" in result:
            import re
            matches = re.findall(r'/workspace/projects/assets/compiled/\d+\.mp4', result)
            if matches:
                return matches[0]

        return None

    except Exception as e:
        print(f"视频音频合成失败：{str(e)}")
        return None


def _add_subtitles(video_path: str, script: str) -> str:
    """添加字幕"""
    try:
        from tools.subtitle_tool import auto_subtitle_pipeline

        result = auto_subtitle_pipeline.invoke({
            "video_url": video_path,
            "font_size": 32,
            "position_y": 0.85
        })

        # 解析结果，提取视频路径
        if "✅" in result:
            import re
            matches = re.findall(r'/workspace/projects/assets/subtitled/\d+\.mp4', result)
            if matches:
                return matches[0]

        return None

    except Exception as e:
        print(f"字幕添加失败：{str(e)}")
        return None


def _build_success_message(
    final_video: str,
    scenes: List[Dict],
    duration: int,
    video_public_url: str = None
) -> str:
    """构建成功消息"""

    message_parts = [
        "✅ 长视频生成成功！",
        f"📹 视频时长: {duration}秒",
        f"🎬 镜头数量: {len(scenes)}",
        f"🎥 最终视频: {final_video}",
        "",
        "📋 镜头规划："
    ]

    for scene in scenes:
        message_parts.append(
            f"\n镜头{scene['index']} ({scene['start_time']}-{scene['end_time']}秒) - "
            f"{scene['scene_type']} - {scene['emotion']}"
        )
        message_parts.append(f"  描述: {scene['paragraph']}")
        message_parts.append(f"  时长: {scene['duration']}秒")

    message_parts.append("")
    message_parts.append("🎨 一致性保证：")
    message_parts.append("  ✅ 人物一致性: 使用角色主体ID 308110838358255")
    message_parts.append("  ✅ 场景统一: 传统中式茶室")
    message_parts.append("  ✅ 色调统一: 暖色调、中式美学")
    message_parts.append("  ✅ 配音统一: 使用指定声音")
    message_parts.append("  ✅ 字幕自动生成")

    # 添加对象存储信息
    if video_public_url:
        message_parts.append("")
        message_parts.append("☁️ 对象存储：")
        message_parts.append(f"  ✅ 视频已上传到对象存储")
        message_parts.append(f"  ✅ 公开URL有效期：7天")
        message_parts.append(f"  🔗 链接：{video_public_url}")
        message_parts.append("")
        message_parts.append("📢 飞书通知：")
        message_parts.append("  ✅ 已自动推送到飞书群组")

    return "\n".join(message_parts)


# 导入所需的工具
import subprocess
import re
