from langchain.tools import tool


@tool
def create_simple_effective_prompt(
    scene_type: str,
    action_description: str,
    avoid_physics_errors: bool = True
) -> str:
    """
    创建简化但有效的视频生成提示词。

    基于实际测试反馈，简化提示词比复杂提示词效果更好。

    Args:
        scene_type: 场景类型（sitting:坐姿, standing:站姿, closeup:特写）
        action_description: 动作描述（简洁明了）
        avoid_physics_errors: 是否避免物理错误

    Returns:
        简化的提示词

    Example:
        create_simple_effective_prompt(
            scene_type="sitting",
            action_description="手持线香展示",
            avoid_physics_errors=True
        )
    """

    # 基础角色描述（简化版）
    base_character = """40-50岁女性，看上去只有30-40岁，温婉知性，中式风格。
外貌：鹅蛋脸，杏眼，平直眉，温和微笑。
穿着：米白色中式改良立领上衣，淡绿色盘扣，浅米色阔腿长裤。
气质：优雅从容，亲切自然。"""

    # 场景描述（简洁清晰）
    scene_descriptions = {
        "sitting": "传统中式茶室，人物坐在茶桌后方的椅子上，身体正对镜头。茶桌摆放香道器具。",
        "standing": "传统中式茶室，人物站立，身体正对镜头。背景有博古架陈列茶具。",
        "closeup": "传统中式茶室背景，人物面部特写，眼神温和看着镜头。"
    }

    # 物理约束（关键！简洁但明确）
    physics_constraints = """物理约束：
- 人物身体完全位于茶桌后方，不穿透桌子
- 手部动作在合理空间范围内
- 坐姿自然，无悬空
- 阴影和光照符合物理规律""" if avoid_physics_errors else ""

    # 组合提示词（简洁有效）
    prompt_parts = [
        f"场景：{scene_descriptions.get(scene_type, scene_descriptions['sitting'])}",
        f"",
        f"角色：{base_character}",
        f"",
        f"动作：{action_description}。动作自然流畅，符合香道文化传播者的气质。",
        f"",
        physics_constraints,
        f"",
        f"视觉效果：温暖治愈，中式美学，自然光柔和，画面稳定清晰。"
    ]

    return "\n".join(prompt_parts)


@tool
def create_physics_safe_prompt(
    action: str,
    character_position: str = "behind_table"
) -> str:
    """
    创建物理安全的提示词（重点解决穿桌问题）。

    Args:
        action: 动作描述
        character_position: 人物位置（behind_table:桌后, beside_table:桌旁, front_of_table:桌前）

    Returns:
    物理安全的提示词

    Example:
        create_physics_safe_prompt(
            action="手持线香展示",
            character_position="behind_table"
        )
    """

    # 位置描述（关键！明确位置关系）
    position_descriptions = {
        "behind_table": "人物坐在茶桌后方的椅子上，身体位于桌子后方",
        "beside_table": "人物站在茶桌旁边，身体位于桌子侧面",
        "front_of_table": "人物站在茶桌前方，身体位于桌子前方"
    }

    # 简化提示词
    prompt = f"""传统中式茶室场景。

人物位置：{position_descriptions.get(character_position, position_descriptions['behind_table'])}。

角色：40-50岁女性，温婉知性，中式风格，米白色中式上衣，浅米色长裤，优雅微笑。

动作：{action}。动作自然流畅。

重要约束：
- 人物身体保持在桌子后方，不穿透桌子
- 手部动作在合理空间范围内
- 坐姿自然，臀部与椅子完全接触
- 阴影和光照自然

视觉效果：温暖治愈，中式美学，自然光柔和。"""

    return prompt


@tool
def optimize_prompt_based_on_feedback(
    previous_prompt: str,
    feedback_issues: list,
    keep_original: bool = False
) -> str:
    """
    基于反馈优化提示词。

    Args:
        previous_prompt: 之前的提示词
        feedback_issues: 反馈的问题列表（如["穿桌", "人物不好"]）
        keep_original: 是否保留原有提示词

    Returns:
    优化后的提示词

    Example:
        optimize_prompt_based_on_feedback(
            previous_prompt="...",
            feedback_issues=["穿桌", "人物不好"],
            keep_original=False
        )
    """

    if keep_original:
        return previous_prompt

    # 基于反馈简化提示词
    simplified_prompt = """传统中式茶室场景。

角色：40-50岁女性，温婉知性，中式风格。米白色中式上衣，浅米色长裤，优雅微笑。

动作：手持线香展示。动作自然流畅，温和亲切。

位置：人物坐在茶桌后方的椅子上，身体位于桌子后方。

视觉效果：温暖治愈，中式美学，自然光柔和，画面稳定清晰。"""

    return simplified_prompt
