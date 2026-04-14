from langchain.tools import tool
import os
import json
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

OUTPUT_DIR = "/workspace/projects/assets/final_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@tool
def generate_complete_video(
    prompt: str,
    narration_text: str,
    character_image_url: str = None,
    video_model: str = "kling-v3-omni",
    tts_speaker: str = "zh_female_xiaohe_uranus_bigtts",
    add_auto_subtitle: bool = True,
    video_duration: int = 5,
    video_ratio: str = "9:16",
    video_mode: str = "pro",
    output_filename: str = None
) -> str:
    """
    一键生成完整视频（包含视频生成、配音、字幕）。

    完整流程：
    1. 生成视频（使用角色参考图片）
    2. 生成配音（TTS语音合成）
    3. 合成视频和音频
    4. 自动生成并添加字幕（可选）

    Args:
        prompt: 视频场景描述
        narration_text: 配音文案文本
        character_image_url: 角色参考图片URL（可选，用于确保人物一致性）
        video_model: 视频生成模型（kling-v3-omni 或 doubao-seedance-1-5-pro-251215）
        tts_speaker: 配音声音（默认小禾）
        add_auto_subtitle: 是否自动生成字幕
        video_duration: 视频时长（秒）
        video_ratio: 视频比例（9:16 或 16:9）
        video_mode: 视频质量（pro 或 std）
        output_filename: 输出文件名（不含扩展名）

    Returns:
        完整视频的 URL 和文件信息

    Example:
        generate_complete_video(
            prompt="一位温婉的女性手持线香，面带微笑，传统中式茶室场景",
            narration_text="欢迎来到香道文化，今天我们来讲讲线香的魅力",
            character_image_url="https://example.com/character.jpg"
        )
    """
    ctx = request_context.get() or new_context(method="generate_complete_video")

    steps_result = []
    step = 1

    # 步骤1：生成视频
    steps_result.append(f"\n{'='*60}")
    steps_result.append(f"🎬 步骤 {step}/4：生成视频")
    steps_result.append(f"{'='*60}")

    try:
        # 优先使用 Kling CLI（对角色参考图片支持最好）
        from tools.kling_cli_tool import kling_cli_text_to_video

        # 优化提示词：强调说话动作和自然手势
        optimized_prompt = f"""{prompt}。

重要动作要求：
- 角色正在讲解/说话，嘴巴有自然的说话动作
- 配合自然的手势动作，表达清晰
- 面部表情生动，眼神专注
- 整体姿态自然流畅
- 严格按照提供的角色参考图片生成，确保人物外貌、发型、穿着完全一致，保持人物一致性。"""

        video_result = kling_cli_text_to_video(
            prompt=optimized_prompt,
            character_image_url=character_image_url,
            model="kling-v3-omni",  # 强制使用 kling-v3-omni（对角色一致性支持最好）
            mode=video_mode,
            aspect_ratio=video_ratio,
            duration=video_duration,
            sound="off"  # 不生成原声音频
        )

        steps_result.append(video_result)

        # 提取视频URL
        import re
        url_match = re.search(r'/workspace/projects/assets/[^\s]+\.mp4', video_result)
        if not url_match:
            url_match = re.search(r'https?://[^\s]+\.mp4', video_result)

        if not url_match:
            return f"❌ 步骤{step}失败：无法提取视频URL\n{video_result}"

        video_path = url_match.group(0)
        video_url = f"file://{video_path}" if video_path.startswith("/") else video_path

        steps_result.append(f"\n✅ 视频生成成功：{video_path}")

    except Exception as e:
        return f"❌ 步骤{step}失败：{str(e)}\n\n详细结果：{video_result if 'video_result' in locals() else ''}"

    step += 1

    # 步骤2：生成配音
    steps_result.append(f"\n{'='*60}")
    steps_result.append(f"🎤 步骤 {step}/4：生成配音（TTS）")
    steps_result.append(f"{'='*60}")

    try:
        from tools.tts_tool import text_to_speech

        audio_result = text_to_speech(
            text=narration_text,
            speaker=tts_speaker,
            audio_format="mp3",
            sample_rate=24000
        )

        steps_result.append(audio_result)

        # 提取音频路径
        url_match = re.search(r'/workspace/projects/assets/[^\s]+\.mp3', audio_result)
        if not url_match:
            return f"❌ 步骤{step}失败：无法提取音频路径\n{audio_result}"

        audio_path = url_match.group(0)

        steps_result.append(f"\n✅ 配音生成成功：{audio_path}")

    except Exception as e:
        return f"❌ 步骤{step}失败：{str(e)}\n\n详细结果：{audio_result if 'audio_result' in locals() else ''}"

    step += 1

    # 步骤3：合成视频和音频
    steps_result.append(f"\n{'='*60}")
    steps_result.append(f"🔗 步骤 {step}/4：合成视频和音频")
    steps_result.append(f"{'='*60}")

    try:
        from tools.video_audio_tool import compile_video_audio

        compile_result = compile_video_audio(
            video_url=video_url,
            audio_url=audio_path,
            is_audio_reserve=False,  # 替换原音频
            sync_method="trim",
            sync_mode="audio",  # 以音频时长为准
            output_filename=f"temp_{output_filename}" if output_filename else None
        )

        steps_result.append(compile_result)

        # 提取合成后的视频路径
        url_match = re.search(r'/workspace/projects/assets/[^\s]+\.mp4', compile_result)
        if not url_match:
            return f"❌ 步骤{step}失败：无法提取合成视频路径\n{compile_result}"

        compiled_video_path = url_match.group(0)

        steps_result.append(f"\n✅ 视频音频合成成功：{compiled_video_path}")

    except Exception as e:
        return f"❌ 步骤{step}失败：{str(e)}\n\n详细结果：{compile_result if 'compile_result' in locals() else ''}"

    # 步骤4：生成并添加字幕（可选）
    if add_auto_subtitle:
        step += 1
        steps_result.append(f"\n{'='*60}")
        steps_result.append(f"📝 步骤 {step}/4：生成并添加字幕")
        steps_result.append(f"{'='*60}")

        try:
            from tools.subtitle_tool import auto_subtitle_pipeline

            subtitle_result = auto_subtitle_pipeline(
                video_url=compiled_video_path,
                font_size=36,
                position_y="90%",
                output_filename=output_filename
            )

            steps_result.append(subtitle_result)

            # 提取最终视频路径
            url_match = re.search(r'/workspace/projects/assets/[^\s]+\.mp4', subtitle_result)
            if not url_match:
                return f"❌ 步骤{step}失败：无法提取最终视频路径\n{subtitle_result}"

            final_video_path = url_match.group(0)

            steps_result.append(f"\n✅ 最终视频生成成功：{final_video_path}")

        except Exception as e:
            return f"❌ 步骤{step}失败：{str(e)}\n\n详细结果：{subtitle_result if 'subtitle_result' in locals() else ''}"
    else:
        # 不添加字幕，直接使用合成后的视频
        import shutil
        if output_filename:
            final_video_path = os.path.join(OUTPUT_DIR, f"{output_filename}.mp4")
            shutil.copy(compiled_video_path, final_video_path)
        else:
            final_video_path = compiled_video_path

    # 生成最终报告
    final_report = f"""
{'='*60}
🎉 完整视频生成成功！
{'='*60}

📋 视频信息：
  - 视频描述：{prompt[:100]}{'...' if len(prompt) > 100 else ''}
  - 配音文案：{narration_text[:100]}{'...' if len(narration_text) > 100 else ''}
  - 视频模型：{video_model}
  - 配音声音：{tts_speaker}
  - 视频时长：{video_duration} 秒
  - 视频比例：{video_ratio}
  - 字幕：{'✅ 已添加' if add_auto_subtitle else '❌ 未添加'}

📁 最终文件：
  - 本地路径：{final_video_path}
  - 文件大小：{os.path.getsize(final_video_path) / (1024*1024):.2f} MB

🔄 处理流程：
{chr(10).join(steps_result)}

💡 提示：
  - 这是完整的最终成片，可直接使用
  - 视频包含：画面 + 配音 + 字幕
  - 无需任何后续处理
"""

    # 自动推送到飞书
    try:
        from tools.feishu_notification_tool import send_feishu_video_notification

        # 提取视频信息
        import re
        video_title = f"视频生成完成 - {output_filename if output_filename else '未命名'}"

        # 推送飞书通知
        feishu_result = send_feishu_video_notification(
            title=video_title,
            video_url=f"file://{final_video_path}",
            description=f"{prompt[:100]}{'...' if len(prompt) > 100 else ''}",
            video_duration=video_duration
        )

        final_report += f"\n\n📢 飞书通知：\n{feishu_result}"

    except Exception as e:
        final_report += f"\n\n⚠️ 飞书推送失败：{str(e)}"

    return final_report


@tool
def batch_generate_videos(
    tasks: list,
    default_video_model: str = "kling-v3-omni",
    default_tts_speaker: str = "zh_female_xiaohe_uranus_bigtts",
    add_auto_subtitle: bool = True
) -> str:
    """
    批量生成完整视频（一键成片）。

    适用于为多个产品或场景批量生成视频。

    Args:
        tasks: 任务列表，每个任务包含：
            - prompt: 视频描述
            - narration: 配音文案
            - character_image_url: 角色参考图片URL（可选）
            - output_filename: 输出文件名（可选）
        default_video_model: 默认视频模型
        default_tts_speaker: 默认配音声音
        add_auto_subtitle: 是否自动添加字幕

    Returns:
        批量生成结果汇总

    Example:
        batch_generate_videos([
            {
                "prompt": "手持线香A，优雅展示",
                "narration": "这是我们的第一款线香",
                "output_filename": "product_1"
            },
            {
                "prompt": "手持线香B，优雅展示",
                "narration": "这是我们的第二款线香",
                "output_filename": "product_2"
            }
        ])
    """
    results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*60}")
        print(f"🎬 正在处理第 {i}/{len(tasks)} 个视频")
        print(f"{'='*60}\n")

        try:
            result = generate_complete_video(
                prompt=task.get("prompt"),
                narration_text=task.get("narration"),
                character_image_url=task.get("character_image_url"),
                video_model=task.get("video_model", default_video_model),
                tts_speaker=task.get("tts_speaker", default_tts_speaker),
                add_auto_subtitle=add_auto_subtitle,
                output_filename=task.get("output_filename")
            )

            results.append({
                "index": i,
                "status": "success",
                "task": task,
                "result": result
            })

            print(f"✅ 第 {i} 个视频生成成功\n")

        except Exception as e:
            results.append({
                "index": i,
                "status": "failed",
                "task": task,
                "error": str(e)
            })

            print(f"❌ 第 {i} 个视频生成失败：{str(e)}\n")

    # 生成汇总报告
    report_lines = [
        "="*60,
        f"🎊 批量视频生成完成！",
        "="*60,
        f"\n📊 统计信息：",
        f"  - 总计：{len(tasks)} 个视频",
        f"  - 成功：{sum(1 for r in results if r['status'] == 'success')} 个",
        f"  - 失败：{sum(1 for r in results if r['status'] == 'failed')} 个",
    ]

    for result in results:
        if result["status"] == "success":
            report_lines.append(f"\n✅ 第 {result['index']} 个：成功")
            # 提取最终视频路径
            import re
            url_match = re.search(r'/workspace/projects/assets/[^\s]+\.mp4', result['result'])
            if url_match:
                report_lines.append(f"   文件：{url_match.group(0)}")
        else:
            report_lines.append(f"\n❌ 第 {result['index']} 个：失败")
            report_lines.append(f"   错误：{result['error']}")

    report_lines.append(f"\n{'='*60}")
    report_lines.append(f"📁 输出目录：{OUTPUT_DIR}")
    report_lines.append(f"{'='*60}")

    return "\n".join(report_lines)
