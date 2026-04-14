from langchain.tools import tool
from typing import Dict, List


@tool
def optimize_video_prompt_professional(
    base_prompt: str,
    action_type: str = "speaking",
    scene_description: str = None,
    enforce_physics: bool = True,
    fix_camera: bool = True
) -> str:
    """
    专业级视频生成提示词优化器。

    解决以下核心问题：
    1. 物理错误（人物穿模、穿桌）
    2. 口型与配音不同步
    3. 画面诡异、不稳定
    4. 人物与环境不协调

    Args:
        base_prompt: 基础场景描述（越简洁越好）
        action_type: 动作类型（speaking:说话, demonstrating:演示, holding:手持）
        scene_description: 场景描述（如"坐在茶桌前"、"站立讲解"）
        enforce_physics: 是否强制物理合理性（默认True）
        fix_camera: 是否固定镜头（默认True）

    Returns:
        优化后的专业提示词

    Example:
        # 基础用法
        optimize_video_prompt_professional(
            base_prompt="手持线香",
            action_type="holding",
            scene_description="坐在茶桌前"
        )

        # 说话场景
        optimize_video_prompt_professional(
            base_prompt="讲解线香",
            action_type="speaking",
            scene_description="坐在茶桌前，面向镜头"
        )
    """
    # 物理合理性约束（核心！）
    physics_constraints = [
        "【物理合理性约束】",
        "人物与场景中的物体（桌子、椅子、茶具等）必须保持正确的物理关系",
        "人物身体不能穿过任何固体物体（不能穿桌、穿椅、穿墙）",
        "手部动作必须在合理空间范围内，不能穿透物体",
        "站立时双脚必须着地，不能悬空或嵌入地面",
        "坐下时必须与椅子保持接触，不能穿过椅面",
        "手持物体时，手指必须真实地握住物体，不能穿透"
    ] if enforce_physics else []

    # 口型同步约束（核心！）
    lip_sync_constraints = [
        "【口型同步约束】",
        "角色必须根据语音内容产生对应的嘴型变化",
        "嘴唇开合必须与说话节奏完全同步",
        "张嘴幅度与说话音量匹配（大声则张大嘴，小声则微张）",
        "说话时舌头有自然的内部运动（不露出来）",
        "发音要有细微的咬合动作（如发p/b/t/d/k/g音）",
        "面部肌肉随说话内容自然收缩和舒张"
    ]

    # 镜头稳定性约束
    camera_constraints = [
        "【镜头稳定性】",
        "使用固定镜头，避免剧烈晃动",
        "镜头焦点稳定地保持在角色面部",
        "画面构图稳定，避免突然的视角切换",
        "背景清晰稳定，不会出现扭曲或变形"
    ] if fix_camera else []

    # 人物与环境一致性约束
    environment_constraints = [
        "【环境一致性】",
        "人物必须与场景中的物体保持正确的空间关系",
        "如果坐在桌前，身体必须位于桌子前方，不能穿过桌子",
        "如果手持物品，手部必须在合理位置，不能反关节或异常弯曲",
        "阴影和光照必须符合物理规律，不能出现错误的投影",
        "人物与背景的透视关系必须正确"
    ]

    # 角色描述（香道文化传播者）
    character_description = """【固定角色】
40-50岁女性，看上去只有30-40岁，偏圆润的鹅蛋脸，面部线条柔和。
深褐色杏眼，眼尾微微上扬，双眼皮自然清晰，眼神温和清澈。
平直眉，深棕色，眉形规整温婉。
鼻梁适中，鼻头圆润，鼻型柔和。
饱满的嘴唇，粉豆沙色，嘴角微微上扬。
白皙细腻的皮肤，脸颊有自然红晕。

发型：乌黑亮泽，向后梳理成低发髻，额前无刘海，两侧碎发自然垂落。

穿着：米白色中式改良立领上衣，淡绿色一字盘扣，带有水墨风格印花，搭配浅米色阔腿长裤。
不佩戴任何首饰配饰。

气质：中式温婉知性，端庄优雅，目光温和沉静，面带浅浅的微笑，从容友善，亲切自然。"""

    # 动作描述
    action_descriptions = {
        "speaking": """【动作描述】
角色正在说话，面向镜头。
嘴巴有自然的说话动作，口型与语音完全同步。
双手自然放在身前或桌面上，配合说话有轻微的手势。
头部保持稳定，眼神专注地看着镜头，有交流感。
面部表情生动，眉毛和眼睛随说话内容自然变化。""",
        "demonstrating": """【动作描述】
角色正在演示香道操作。
双手动作精准而优雅，展示线香或香具。
手指灵活地操作，动作流畅自然。
头部微微低头专注于手中的物品，然后抬起看向镜头。
表情认真而专注，体现专业性。""",
        "holding": """【动作描述】
角色手持线香，优雅展示。
一只手轻轻握住线香，另一只手自然放在身侧或桌面上。
手腕稳定，展示动作缓慢而优雅。
头部微微偏向一侧，面带温和的微笑。
眼神专注于手中的线香，然后看向镜头，引导观众注意。""",
        "sitting": """【动作描述】
角色坐在茶桌前，身体姿态端正。
上半身微微前倾，面向镜头。
双手自然放在桌面或膝盖上。
头部保持稳定，眼神温和地看着镜头。
整体姿态放松而优雅。""",
        "standing": """【动作描述】
角色站立在茶室中，身体姿态挺拔。
双脚自然分开与肩同宽，重心稳定。
双手自然垂在身侧或轻轻交握。
头部端正，面向镜头。
整体姿态自信而优雅。"""
    }

    # 获取动作描述
    action_desc = action_descriptions.get(action_type, action_descriptions["speaking"])

    # 场景描述
    if scene_description:
        scene_desc = f"""【场景】
{scene_description}
传统中式茶室，暖色调氛围。
背景有博古架陈列茶具与香器。
自然光线柔和均匀，营造宁静雅致的氛围。"""
    else:
        scene_desc = """【场景】
传统中式茶室，暖色调氛围。
背景有博古架陈列茶具与香器。
自然光线柔和均匀，营造宁静雅致的氛围。"""

    # 构建完整的优化提示词
    optimized_parts = [
        base_prompt.strip(),
        "",
        character_description,
        "",
        action_desc,
        "",
        scene_desc,
        "",
    ]

    # 添加约束条件
    if physics_constraints:
        optimized_parts.extend(physics_constraints)
        optimized_parts.append("")

    optimized_parts.extend(lip_sync_constraints)
    optimized_parts.append("")

    if camera_constraints:
        optimized_parts.extend(camera_constraints)
        optimized_parts.append("")

    optimized_parts.extend(environment_constraints)

    # 最终强调
    optimized_parts.extend([
        "",
        "【最终要求】",
        "严格按照提供的角色参考图片生成，确保人物外貌、发型、穿着完全一致",
        "人物与场景保持正确的物理关系，不能穿模、穿桌",
        "口型与配音完全同步，说话动作自然流畅",
        "画面稳定清晰，不出现诡异变形",
        "整体风格温暖治愈，符合香道文化传播者的气质"
    ])

    return "\n".join(optimized_parts)


@tool
def generate_scene_based_prompt(
    script_text: str,
    scene_type: str = "indoor_sitting",
    character_pose: str = "speaking"
) -> str:
    """
    基于脚本内容生成场景化提示词。

    根据脚本内容自动选择合适的场景和动作，生成高质量的视频生成提示词。

    Args:
        script_text: 脚本文本内容
        scene_type: 场景类型（indoor_sitting:室内坐姿, indoor_standing:室内站姿, outdoor:室外）
        character_pose: 角色姿态（speaking:说话, demonstrating:演示, holding:手持）

    Returns:
        生成的场景化提示词

    Example:
        generate_scene_based_prompt(
            script_text="大家好，今天我来介绍这款线香",
            scene_type="indoor_sitting",
            character_pose="speaking"
        )
    """
    # 分析脚本内容，提取关键信息
    script_lower = script_text.lower()

    # 判断动作类型
    if "介绍" in script_text or "讲解" in script_text:
        action_type = "speaking"
    elif "演示" in script_text or "点燃" in script_text or "展示" in script_text:
        action_type = "demonstrating"
    elif "手持" in script_text or "拿" in script_text:
        action_type = "holding"
    else:
        action_type = "speaking"

    # 判断场景
    if scene_type == "indoor_sitting":
        scene_desc = "角色坐在传统中式茶桌前，面向镜头。身体姿态端正，上半身微微前倾。"
    elif scene_type == "indoor_standing":
        scene_desc = "角色站立在传统中式茶室中，面向镜头。身体姿态挺拔，双脚自然分开。"
    else:  # outdoor
        scene_desc = "角色站在自然环境（庭院或竹林）中，面向镜头。姿态自然放松。"

    # 生成基础提示词
    base_prompt = f"{scene_desc} {script_text[:50]}"

    # 使用专业优化器生成最终提示词
    optimized_prompt = optimize_video_prompt_professional(
        base_prompt=base_prompt,
        action_type=action_type,
        scene_description=scene_desc,
        enforce_physics=True,
        fix_camera=True
    )

    return optimized_prompt


@tool
def fix_physical_physics_issue(
    current_prompt: str,
    specific_issue: str = "passing_through_table"
) -> str:
    """
    修复提示词中的物理问题。

    针对已知的物理错误（如穿桌、穿模），在提示词中添加明确的约束。

    Args:
        current_prompt: 当前的提示词
        specific_issue: 具体问题类型（passing_through_table:穿桌, clipping:穿模, floating:悬空）

    Returns:
        修复后的提示词

    Example:
        fix_physical_physics_issue(
            current_prompt="角色坐在桌前讲解线香",
            specific_issue="passing_through_table"
        )
    """
    # 物理问题修复规则
    fix_rules = {
        "passing_through_table": [
            "【物理约束：防穿桌】",
            "人物坐在桌前时，身体必须在桌子前方，不能穿过桌面",
            "上半身位于桌子前方，背部不接触桌子",
            "双手可以放在桌面上，但不能穿透桌面",
            "如果身体前倾，前倾幅度必须小于到桌面的距离"
        ],
        "clipping": [
            "【物理约束：防穿模】",
            "人物不能穿过任何固体物体",
            "手部不能穿过桌面、椅背、墙壁等物体",
            "手指不能穿透手持的物品",
            "衣物不能穿过身体或家具"
        ],
        "floating": [
            "【物理约束：防悬空】",
            "人物必须与地面保持接触",
            "站立时双脚必须着地，不能悬空",
            "坐下时必须与椅子保持接触，不能悬浮在椅子上方",
            "阴影必须正确地投射在地面上"
        ],
        "broken_perspective": [
            "【物理约束：透视正确】",
            "人物与背景的透视关系必须正确",
            "大小比例符合真实空间关系",
            "远近关系清晰，近大远小"
        ]
    }

    # 获取修复规则
    rules = fix_rules.get(specific_issue, fix_rules["clipping"])

    # 在提示词中添加修复规则
    if "【物理" in current_prompt:
        # 如果已经有物理约束，更新它
        lines = current_prompt.split("\n")
        new_lines = []
        skip_next = False
        in_physics_section = False

        for i, line in enumerate(lines):
            if line.startswith("【物理"):
                in_physics_section = True
                new_lines.extend(rules)
                continue

            if in_physics_section and line.startswith("【"):
                in_physics_section = False
                new_lines.append(line)
            elif not in_physics_section:
                new_lines.append(line)

        return "\n".join(new_lines)
    else:
        # 如果没有物理约束，添加到末尾
        return f"{current_prompt}\n\n" + "\n".join(rules)
