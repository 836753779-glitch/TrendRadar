from langchain.tools import tool
import os
import time
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


# ==================== 普通函数（可复用的公共逻辑） ====================

def _generate_test_video_logic(
    prompt: str,
    narration_text: str,
    character_image_url: str,
    test_duration: int,
    video_model: str,
    video_ratio: str
) -> str:
    """生成测试视频的核心逻辑（普通函数，可被多个工具调用）"""
    # 步骤1：使用 LLM 优化提示词
    print("正在优化提示词...")
    from tools.video_prompt_smart import optimize_video_prompt_with_llm

    action_type = "speaking"
    if "演示" in prompt or "展示" in prompt:
        action_type = "demonstrating"
    elif "手持" in prompt or "拿" in prompt:
        action_type = "holding"

    scene_context = "坐在传统中式茶桌前，面向镜头"
    if "站立" in prompt or "站" in prompt:
        scene_context = "站立在传统中式茶室中，面向镜头"

    optimized_prompt = optimize_video_prompt_with_llm(
        scene_description=f"{scene_context}，{prompt}",
        action_type=action_type,
        character_name="香道文化传播者"
    )

    print(f"优化后的提示词：\n{optimized_prompt}\n")

    # 步骤2：生成测试视频（使用 Kling CLI）
    from tools.kling_cli_tool import kling_cli_text_to_video

    print("正在生成测试视频...")
    video_result = kling_cli_text_to_video(
        prompt=optimized_prompt,
        character_image_url=character_image_url,
        model=video_model,
        mode="pro",
        aspect_ratio=video_ratio,
        duration=test_duration,
        sound="off"  # 测试视频不生成音频
    )

    print(f"视频生成结果：\n{video_result}\n")

    # 提取视频路径
    import re
    url_match = re.search(r'/workspace/projects/assets/[^\s]+\.mp4', video_result)
    if not url_match:
        url_match = re.search(r'https?://[^\s]+\.mp4', video_result)

    if not url_match:
        return None, f"❌ 测试视频生成失败：无法提取视频URL\n{video_result}"

    test_video_path = url_match.group(0)

    # 步骤3：上传到对象存储
    print("正在上传到对象存储...")
    upload_result = upload_to_storage_logic(test_video_path)

    # 提取公开URL
    url_match = re.search(r'https?://[^\s]+', upload_result)
    if not url_match:
        return None, f"❌ 上传失败：{upload_result}"

    test_video_url = url_match.group(0)

    # 步骤4：推送到飞书
    print("正在推送到飞书...")
    feishu_result = send_feishu_card_logic(test_video_url, test_duration, video_model, video_ratio, prompt)

    return test_video_url, f"""✅ 测试视频生成完成！

📹 测试视频信息：
  - 本地路径：{test_video_path}
  - 公开URL：{test_video_url}
  - 视频时长：{test_duration}秒
  - 模型：{video_model}
  - 比例：{video_ratio}

📝 优化后的提示词：
{optimized_prompt}

📢 飞书通知：{feishu_result}

💡 提示：
  - 请点击飞书中的视频链接查看测试视频
  - 检查人物、场景、物理正确性
  - 确认无误后回复"确认"或"OK"
  - 将使用相同的参数生成长视频

---
**等待用户确认中...**
"""


def upload_to_storage_logic(local_video_path: str) -> str:
    """上传视频到对象存储的核心逻辑"""
    from tools.video_upload_tool import upload_video_to_storage

    return upload_video_to_storage(
        local_video_path=local_video_path,
        file_name=f"test_video_{int(os.path.getmtime(local_video_path))}.mp4",
        expire_hours=24
    )


def send_feishu_card_logic(video_url: str, duration: int, model: str, ratio: str, prompt: str) -> str:
    """推送飞书卡片的核心逻辑"""
    from tools.feishu_notification_tool import send_feishu_card_notification

    card_content = {
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "🎬 测试视频已生成 - 请确认"
            }
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"""**测试视频信息**：
  - 视频时长：{duration}秒
  - 视频模型：{model}
  - 视频比例：{ratio}

**提示词**：
{prompt[:100]}...

**请检查以下内容**：
  - ✅ 人物一致性（外貌、穿着、发型）
  - ✅ 物理正确性（无穿桌、穿模、悬空）
  - ✅ 口型同步（如果有配音）
  - ✅ 场景合理性
  - ✅ 整体画面质量

**测试视频链接**：
{video_url}

**下一步操作**：
  - 如果确认无误，请回复：**确认** 或 **OK**
  - 如果有问题，请回复：**需要修改** 并说明问题

收到确认后，将开始生成长视频。"""
                }
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "✅ 确认无误"
                        },
                        "type": "primary",
                        "url": video_url
                    },
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "❌ 需要修改"
                        },
                        "type": "default",
                        "url": f"{video_url}?action=reject"
                    }
                ]
            }
        ]
    }

    return send_feishu_card_notification(title="测试视频已生成", card_content=card_content)


# ==================== 工具函数（@tool 装饰） ====================

@tool
def generate_test_video(
    prompt: str,
    narration_text: str = None,
    character_image_url: str = None,
    test_duration: int = 3,
    video_model: str = "kling-v3-omni",
    video_ratio: str = "9:16"
) -> str:
    """
    生成测试短视频（3-5秒），用于验证逻辑和细节。

    这是"先验证，再生产"流程的第一步。
    生成测试视频后，会自动上传到对象存储并推送到飞书，等待用户确认。

    Args:
        prompt: 视频场景描述
        narration_text: 配音文本（测试音频）
        character_image_url: 角色参考图片URL
        test_duration: 测试视频时长（默认3秒，建议3-5秒）
        video_model: 视频模型（kling-v3-omni）
        video_ratio: 视频比例（9:16或16:9）

    Returns:
        测试视频的公开URL和状态信息
    """
    ctx = request_context.get() or new_context(method="generate_test_video")

    try:
        test_video_url, result = _generate_test_video_logic(
            prompt=prompt,
            narration_text=narration_text,
            character_image_url=character_image_url,
            test_duration=test_duration,
            video_model=video_model,
            video_ratio=video_ratio
        )

        if test_video_url is None:
            return result
        else:
            return result

    except Exception as e:
        return f"❌ 测试视频生成失败：{str(e)}"


@tool
def confirm_and_generate_long_video(
    test_video_url: str,
    long_duration: int = 60,
    prompt: str = None,
    narration_text: str = None,
    character_image_url: str = None,
    tts_speaker: str = "zh_female_xiaohe_uranus_bigtts",
    add_subtitle: bool = True,
    auto_upload: bool = True,
    auto_notify_feishu: bool = True
) -> str:
    """
    确认测试视频无误后，生成长视频。

    这是"先验证，再生产"流程的第二步。
    使用测试通过后的参数，生成长视频。

    Args:
        test_video_url: 测试视频的URL（用于确认）
        long_duration: 长视频时长（秒）
        prompt: 视频场景描述（如果为空，使用测试视频的参数）
        narration_text: 配音文本
        character_image_url: 角色参考图片URL
        tts_speaker: 配音声音
        add_subtitle: 是否添加字幕
        auto_upload: 是否自动上传到对象存储
        auto_notify_feishu: 是否自动推送到飞书

    Returns:
        长视频生成结果
    """
    ctx = request_context.get() or new_context(method="confirm_and_generate_long_video")

    try:
        print(f"✅ 用户已确认测试视频：{test_video_url}")
        print(f"开始生成长视频（{long_duration}秒）...\n")

        # 如果没有提供参数，从测试视频中提取（简化处理）
        if not prompt:
            prompt = "角色坐在茶桌前，手持线香展示"

        # 使用一键成片工具生成长视频
        from tools.complete_video_tool import generate_complete_video

        result = generate_complete_video(
            prompt=prompt,
            narration_text=narration_text,
            character_image_url=character_image_url,
            video_model="kling-v3-omni",
            tts_speaker=tts_speaker,
            add_auto_subtitle=add_subtitle,
            video_duration=long_duration,
            video_ratio="9:16",
            output_filename=f"long_video_{int(time.time())}"
        )

        return result

    except Exception as e:
        return f"❌ 长视频生成失败：{str(e)}"


@tool
def two_stage_video_production(
    prompt: str,
    narration_text: str,
    character_image_url: str = None,
    test_duration: int = 3,
    long_duration: int = 60,
    tts_speaker: str = "zh_female_xiaohe_uranus_bigtts",
    add_subtitle: bool = True
) -> str:
    """
    两阶段视频生产流程（推荐！）。

    这是一个完整的"先验证，再生产"流程。

    流程：
    1. 阶段1：生成3秒测试视频 → 推送飞书 → 等待用户确认
    2. 阶段2：用户确认后 → 生成长视频 → 自动上传并推送

    优势：
    - 避免生成长视频后发现问题的资源浪费
    - 快速验证提示词、人物、场景
    - 确保质量后再大规模生产

    Args:
        prompt: 视频场景描述
        narration_text: 配音文本
        character_image_url: 角色参考图片URL
        test_duration: 测试视频时长（默认3秒）
        long_duration: 长视频时长（默认60秒）
        tts_speaker: 配音声音
        add_subtitle: 是否添加字幕

    Returns:
        流程状态和下一步操作指引
    """
    # 步骤1：生成测试视频
    test_result = generate_test_video(
        prompt=prompt,
        narration_text=narration_text[:20] + "...",  # 测试配音只取前20字
        character_image_url=character_image_url,
        test_duration=test_duration
    )

    if "❌" in test_result:
        return f"❌ 测试视频生成失败，流程终止：\n{test_result}"

    # 提取测试视频URL
    import re
    url_match = re.search(r'公开URL：(https?://[^\s\n]+)', test_result)
    test_video_url = url_match.group(1) if url_match else ""

    # 步骤2：等待用户确认（这个步骤需要用户手动操作）
    return f"""✅ 两阶段视频生产流程 - 阶段1完成

📋 流程状态：
  ✅ 阶段1：测试视频生成完成
  ⏸️  阶段2：等待用户确认

{test_result}

📌 下一步操作：

**方案A：手动确认**
  - 请查看飞书中的测试视频
  - 确认无误后，执行以下命令：
    ```
    confirm_and_generate_long_video(
        test_video_url="{test_video_url}",
        long_duration={long_duration},
        narration_text="{narration_text}",
        character_image_url="{character_image_url}",
        tts_speaker="{tts_speaker}",
        add_subtitle={str(add_subtitle).lower()}
    )
    ```

**方案B：快速确认（推荐）**
  - 直接回复：**确认** 或 **OK**
  - 系统将自动生成长视频

💡 提示：
  - 测试视频已推送到飞书，请检查质量
  - 如有问题，请回复"需要修改"并说明
  - 确认无误后再开始长视频生成，避免资源浪费

---
**等待用户确认中...**
"""
