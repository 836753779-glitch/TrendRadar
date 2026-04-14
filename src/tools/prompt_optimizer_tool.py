from langchain.tools import tool
from typing import Dict, List


def _build_speaking_prompt(
    base_prompt: str,
    speaking_style: str = "natural",
    add_gestures: bool = True,
    emphasize_facial_expressions: bool = True
) -> str:
    """
    内部函数：构建说话提示词。
    """
    # 说话风格定义
    speaking_styles = {
        "natural": {
            "mouth": "嘴巴有自然的说话动作",
            "face": "面带温和微笑，表情自然生动",
            "voice": "语气亲切自然"
        },
        "professional": {
            "mouth": "嘴巴清晰有力地说话",
            "face": "面部表情专业专注",
            "voice": "语气专业严谨"
        },
        "enthusiastic": {
            "mouth": "嘴巴活泼地说话，充满感染力",
            "face": "面部表情热情洋溢",
            "voice": "语气热情饱满"
        }
    }

    style = speaking_styles.get(speaking_style, speaking_styles["natural"])

    # 构建优化后的提示词
    optimized_parts = [
        base_prompt,
        "",
        "【重要：角色说话动作】",
        f"- {style['mouth']}",
        f"- {style['face']}",
        f"- {style['voice']}",
    ]

    # 添加手势动作
    if add_gestures:
        optimized_parts.extend([
            "",
            "【自然手势】",
            "- 配合说话内容有自然的手势动作",
            "- 手势流畅自然，不僵硬",
            "- 手部动作与语言节奏协调"
        ])

    # 强调面部表情
    if emphasize_facial_expressions:
        optimized_parts.extend([
            "",
            "【面部表情】",
            "- 眼神专注，有交流感",
            "- 眉毛随说话内容自然变化",
            "- 表情丰富，有感染力"
        ])

    # 添加整体要求
    optimized_parts.extend([
        "",
        "【整体要求】",
        "- 整体姿态自然流畅",
        "- 身体语言与说话内容协调",
        "- 气质符合角色设定",
        "- 严格按照提供的角色参考图片生成，确保人物外貌、发型、穿着完全一致，保持人物一致性"
    ])

    return "\n".join(optimized_parts)


@tool
def optimize_prompt_for_speaking(
    base_prompt: str,
    speaking_style: str = "natural",
    add_gestures: bool = True,
    emphasize_facial_expressions: bool = True
) -> str:
    """
    优化视频生成提示词，确保角色有自然的说话动作和口型。

    解决配音和口型不一致的问题，让视频中的角色有真实的说话姿态。

    Args:
        base_prompt: 基础提示词（场景描述）
        speaking_style: 说话风格（natural:自然, professional:专业, enthusiastic:热情）
        add_gestures: 是否添加手势动作（默认True）
        emphasize_facial_expressions: 是否强调面部表情（默认True）

    Returns:
        优化后的提示词

    Example:
        # 基础用法
        optimize_prompt_for_speaking("手持线香，优雅展示")

        # 专业讲解风格
        optimize_prompt_for_speaking(
            "手持线香，优雅展示",
            speaking_style="professional"
        )
    """
    return _build_speaking_prompt(
        base_prompt,
        speaking_style,
        add_gestures,
        emphasize_facial_expressions
    )


@tool
def create_narration_prompt(
    script: str,
    character_action: str = "speaking"
) -> str:
    """
    为口播脚本创建视频生成提示词。

    根据脚本内容，自动生成包含说话动作的提示词。

    Args:
        script: 口播脚本
        character_action: 角色动作（speaking:说话, demonstrating:演示, presenting:展示）

    Returns:
        生成的提示词

    Example:
        create_narration_prompt(
            script="大家好，我是香道文化传播者。今天要给大家介绍一款特别的线香。",
            character_action="speaking"
        )
    """
    # 根据脚本长度判断场景
    script_length = len(script)

    # 分析脚本内容
    action_keywords = {
        "介绍": "双手展示产品",
        "讲解": "配合手势讲解",
        "展示": "优雅展示",
        "演示": "亲自演示",
        "点燃": "手持香具点燃",
        "点燃后": "放下香具，面向镜头"
    }

    # 提取动作关键词
    action = ""
    for keyword, action_desc in action_keywords.items():
        if keyword in script:
            action = action_desc
            break

    if not action:
        action = "配合手势讲解"

    # 构建提示词
    if script_length < 50:
        # 短脚本：特写镜头
        prompt = f"""近景镜头，角色面带温和微笑，正在口播内容，嘴巴有自然的说话动作。
角色：{action}
场景：传统中式茶室，背景博古架陈列茶具与香器
光线：暖金色自然光，氛围宁静雅致
面部表情：眼神专注，表情自然生动，有交流感
整体姿态：自然流畅，符合香道文化传播者的气质"""
    else:
        # 长脚本：中景镜头
        prompt = f"""中景镜头，角色坐在传统中式茶室茶桌前，正在口播内容，嘴巴有自然的说话动作。
角色：{action}，配合自然的手势动作
场景：茶室场景，茶桌摆放香道器具
光线：暖金色自然光，氛围宁静雅致
面部表情：眼神专注，表情自然生动，有交流感
手势动作：手势流畅自然，与说话节奏协调
整体姿态：自然流畅，符合香道文化传播者的气质"""

    # 使用内部函数优化提示词
    return _build_speaking_prompt(prompt)


@tool
def analyze_script_for_actions(script: str) -> Dict:
    """
    分析脚本，提取关键动作和场景。

    用于为视频生成提供动作指导。

    Args:
        script: 脚本文本

    Returns:
        包含动作和场景分析的字典

    Example:
        analyze_script_for_actions("大家好，我是香道文化传播者。今天要给大家介绍一款特别的线香。")
    """
    # 动作关键词映射
    action_map = {
        "介绍": {"action": "双手展示产品", "scene": "展示场景"},
        "讲解": {"action": "配合手势讲解", "scene": "讲解场景"},
        "展示": {"action": "优雅展示", "scene": "展示场景"},
        "演示": {"action": "亲自演示", "scene": "演示场景"},
        "点燃": {"action": "手持香具点燃", "scene": "点燃场景"},
        "点燃后": {"action": "放下香具，面向镜头", "scene": "讲解场景"},
        "适合": {"action": "双手合十，面带微笑", "scene": "总结场景"},
        "推荐": {"action": "点头肯定", "scene": "推荐场景"},
        "欢迎": {"action": "双手合十，欢迎姿态", "scene": "欢迎场景"},
        "大家好": {"action": "挥手致意，面带微笑", "scene": "欢迎场景"},
        "谢谢": {"action": "双手合十，致谢", "scene": "结束场景"},
    }

    # 分析脚本
    found_actions = []
    found_scenes = []

    for keyword, action_info in action_map.items():
        if keyword in script:
            found_actions.append(action_info["action"])
            found_scenes.append(action_info["scene"])

    # 去重
    found_actions = list(set(found_actions))
    found_scenes = list(set(found_scenes))

    # 判断脚本类型
    script_type = "讲解"
    if "介绍" in script or "展示" in script:
        script_type = "介绍"
    elif "演示" in script or "点燃" in script:
        script_type = "演示"
    elif "适合" in script or "推荐" in script:
        script_type = "推荐"
    elif "谢谢" in script or "结束" in script:
        script_type = "结束"

    # 生成建议提示词
    suggested_prompt = _build_speaking_prompt(
        f"中景镜头，角色正在口播内容，嘴巴有自然的说话动作。角色：{found_actions[0] if found_actions else '配合手势讲解'}。场景：传统中式茶室。光线：暖金色自然光。面部表情：眼神专注，表情自然生动。整体姿态：自然流畅"
    )

    return {
        "script": script,
        "script_type": script_type,
        "actions": found_actions,
        "scenes": found_scenes,
        "suggested_prompt": suggested_prompt
    }
