from langchain.tools import tool
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage


@tool
def optimize_video_prompt_with_llm(
    scene_description: str,
    action_type: str = "speaking",
    character_name: str = "香道文化传播者"
) -> str:
    """
    使用大语言模型智能优化视频生成提示词。

    解决以下核心问题：
    1. 物理错误（人物穿桌、穿模、悬空）
    2. 口型与配音不同步
    3. 画面诡异、不稳定
    4. 人物与环境不协调

    Args:
        scene_description: 基础场景描述（简洁明了）
        action_type: 动作类型（speaking:说话, demonstrating:演示, holding:手持）
        character_name: 角色名称

    Returns:
        优化后的专业提示词

    Example:
        optimize_video_prompt_with_llm(
            scene_description="角色坐在传统中式茶桌前，讲解线香产品",
            action_type="speaking"
        )
    """
    ctx = new_context(method="optimize_video_prompt_with_llm")

    # 使用 LLM 客户端
    client = LLMClient(ctx=ctx)

    # 构建系统提示词（大模型的专家指令）
    system_prompt = """你是一位专业的视频生成提示词专家，精通AI视频生成模型的特性。

你的任务是为用户的场景描述生成高质量的、专业的视频生成提示词。

## 必须解决的问题

1. **物理合理性约束**
   - 人物与场景中的物体（桌子、椅子、茶具等）必须保持正确的物理关系
   - 人物身体不能穿过任何固体物体（不能穿桌、穿椅、穿墙）
   - 手部动作必须在合理空间范围内，不能穿透物体
   - 站立时双脚必须着地，不能悬空或嵌入地面
   - 坐下时必须与椅子保持接触，不能悬浮在椅子上方
   - 手持物体时，手指必须真实地握住物体，不能穿透
   - 阴影和光照必须符合物理规律，不能出现错误的投影

2. **口型同步约束**
   - 角色必须根据语音内容产生对应的嘴型变化
   - 嘴唇开合必须与说话节奏完全同步
   - 张嘴幅度与说话音量匹配（大声则张大嘴，小声则微张）
   - 说话时舌头有自然的内部运动（不露出来）
   - 发音要有细微的咬合动作（如发p/b/t/d/k/g音）
   - 面部肌肉随说话内容自然收缩和舒张

3. **镜头稳定性**
   - 使用固定镜头，避免剧烈晃动
   - 镜头焦点稳定地保持在角色面部
   - 画面构图稳定，避免突然的视角切换
   - 背景清晰稳定，不会出现扭曲或变形

4. **人物与环境一致性**
   - 人物必须与场景中的物体保持正确的空间关系
   - 如果坐在桌前，身体必须位于桌子前方，不能穿过桌子
   - 如果手持物品，手部必须在合理位置，不能反关节或异常弯曲
   - 人物与背景的透视关系必须正确

## 固定角色描述

香道文化传播者：
- 40-50岁女性，看上去只有30-40岁，偏圆润的鹅蛋脸，面部线条柔和
- 深褐色杏眼，眼尾微微上扬，双眼皮自然清晰，眼神温和清澈
- 平直眉，深棕色，眉形规整温婉
- 鼻梁适中，鼻头圆润，鼻型柔和
- 饱满的嘴唇，粉豆沙色，嘴角微微上扬
- 白皙细腻的皮肤，脸颊有自然红晕
- 发型：乌黑亮泽，向后梳理成低发髻，额前无刘海，两侧碎发自然垂落
- 穿着：米白色中式改良立领上衣，淡绿色一字盘扣，带有水墨风格印花，搭配浅米色阔腿长裤
- 不佩戴任何首饰配饰
- 气质：中式温婉知性，端庄优雅，目光温和沉静，面带浅浅的微笑，从容友善，亲切自然

## 输出格式要求

请按照以下结构输出优化后的提示词：

1. [场景描述] - 详细描述场景环境、光线、氛围
2. [人物描述] - 使用上述固定角色描述
3. [动作描述] - 详细描述角色的动作，包括说话、手势、表情
4. [物理约束] - 明确说明物理合理性要求（防穿桌、防穿模等）
5. [口型约束] - 明确说明口型同步要求
6. [镜头约束] - 明确说明镜头稳定性要求
7. [环境约束] - 明确说明人物与环境的一致性
8. [最终要求] - 强调角色一致性、物理正确性、口型同步

请直接输出提示词内容，不要有其他解释文字。"""

    # 构建用户消息
    user_message = f"""场景描述：{scene_description}
动作类型：{action_type}
角色：{character_name}

请生成一个专业的视频生成提示词，确保：
1. 物理合理性（人物不穿桌、不穿模、不悬空）
2. 口型与配音完全同步
3. 镜头稳定，画面不诡异
4. 人物与环境保持正确的关系"""

    # 调用 LLM
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    response = client.invoke(
        messages=messages,
        model="doubao-seed-2-0-pro-260215",
        temperature=0.7,
        max_completion_tokens=2000
    )

    # 处理响应内容（可能是字符串或列表）
    if isinstance(response.content, str):
        return response.content
    elif isinstance(response.content, list):
        # 提取文本内容
        text_parts = []
        for item in response.content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return "\n".join(text_parts)
    else:
        return str(response.content)


@tool
def generate_video_prompt_smart(
    script_text: str,
    scene_context: str = "坐在传统中式茶桌前"
) -> str:
    """
    智能生成视频提示词（基于脚本内容）。

    根据脚本内容和上下文，自动生成包含物理约束和口型同步约束的专业提示词。

    Args:
        script_text: 脚本文本内容
        scene_context: 场景上下文（如"坐在茶桌前"、"站立讲解"）

    Returns:
        生成的专业提示词

    Example:
        generate_video_prompt_smart(
            script_text="大家好，今天我来介绍这款线香",
            scene_context="坐在传统中式茶桌前"
        )
    """
    # 判断动作类型
    action_type = "speaking"
    if "演示" in script_text or "点燃" in script_text or "展示" in script_text:
        action_type = "demonstrating"
    elif "手持" in script_text or "拿" in script_text:
        action_type = "holding"

    # 构建场景描述
    scene_description = f"{scene_context}，{script_text[:50]}"

    # 使用 LLM 优化
    return optimize_video_prompt_with_llm(
        scene_description=scene_description,
        action_type=action_type,
        character_name="香道文化传播者"
    )
