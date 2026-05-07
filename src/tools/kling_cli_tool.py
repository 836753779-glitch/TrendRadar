from langchain.tools import tool
import subprocess
import json
import os
import re
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

# Kling AI Skill 路径
WORKSPACE_PATH = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
KLING_SKILL_DIR = os.path.join(WORKSPACE_PATH, "klingai")
KLING_SCRIPT_PATH = os.path.join(KLING_SKILL_DIR, "scripts", "kling.mjs")
OUTPUT_DIR = os.path.join(WORKSPACE_PATH, "assets", "kling_output")


@tool
def kling_cli_text_to_video(
    prompt: str,
    character_image_url: str = None,
    element_id: str = "4620676150",  # 用户确认的主讲人女
    model: str = "kling-v3-omni",
    mode: str = "std",
    aspect_ratio: str = "9:16",
    duration: int = 5,
    sound: str = "off"
) -> str:
    """
    使用快手 Kling AI Skill 生成视频，支持角色参考图片，实现人物一致性。

    这是官方的 Kling AI Skill，使用 Node.js CLI 调用，支持最新的 Kling O3 模型。

    ⚠️ 强制标准（用户要求，所有参数必须严格遵守）：
    - 清晰度：720P（mode="std"）
    - 竖屏比例：9:16
    - 音画同步：必须使用外部配音（sound="off"）
    - 主体参考：Element ID 310096591358267（主讲人女）
    - 如需更改标准，用户会明确提醒，在此之前必须严格执行

    Args:
        prompt: 视频场景的文本描述，需要详细描述画面内容、风格、氛围等
        character_image_url: 角色参考图片的URL或本地路径，用于确保人物一致性（可选，但推荐使用）
        element_id: 角色主体ID，用于跨视频保持人物一致性，默认 310096591358267（主讲人女）
        model: 使用的模型，支持 kling-v3, kling-v3-omni, kling-video-o1，默认 kling-v3-omni
        mode: 视频质量模式，std (720P) 或 pro (1080P)，⚠️ 默认 std (720P)
        aspect_ratio: 视频比例，支持 16:9 / 9:16 / 1:1，⚠️ 默认 9:16（竖屏）
        duration: 视频时长（秒），范围 3-15 秒，默认 5 秒
        sound: 是否生成音频，on 或 off，⚠️ 默认 off（音画同步使用外部配音）

    Returns:
        生成的视频信息，包含视频 URL 或本地路径

    Example:
        # 标准生成（720P 竖屏，无音频，音画同步）
        kling_cli_text_to_video(
            prompt="手持线香，优雅地演示点香过程，传统中式茶室场景",
            element_id="310096591358267"
        )

        # 使用角色参考图片
        kling_cli_text_to_video(
            prompt="手持线香，优雅地演示点香过程",
            character_image_url="https://example.com/character.jpg"
        )
    """
    ctx = request_context.get() or new_context(method="kling_cli_text_to_video")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ⚠️ 强制标准验证
    if mode != "std":
        print(f"⚠️ 警告: mode 参数已强制设置为 'std' (720P)，原值 '{mode}' 已被忽略")
        mode = "std"
    
    if aspect_ratio != "9:16":
        print(f"⚠️ 警告: aspect_ratio 参数已强制设置为 '9:16'，原值 '{aspect_ratio}' 已被忽略")
        aspect_ratio = "9:16"
    
    if sound != "off":
        print(f"⚠️ 警告: sound 参数已强制设置为 'off'（音画同步必须使用外部配音），原值 '{sound}' 已被忽略")
        sound = "off"

    # 构建命令
    cmd = [
        "node",
        KLING_SCRIPT_PATH,
        "video",
        "--prompt", prompt,
        "--model", model,
        "--mode", mode,
        "--aspect_ratio", aspect_ratio,
        "--duration", str(duration),
        "--sound", sound,
        "--output_dir", OUTPUT_DIR
    ]

    # ⚠️ 强制使用 Element ID 作为主体参考（主讲人女）
    if element_id:
        cmd.extend(["--element_id", element_id])

    # 如果有角色参考图片，也添加到命令（双重保障）
    if character_image_url:
        # 判断是 URL 还是本地路径
        if character_image_url.startswith("http://") or character_image_url.startswith("https://"):
            # URL 直接使用
            cmd.extend(["--image", character_image_url])
        else:
            # 本地路径，转换为绝对路径
            abs_path = os.path.join(WORKSPACE_PATH, character_image_url.lstrip("/"))
            if os.path.exists(abs_path):
                cmd.extend(["--image", abs_path])
            else:
                return f"❌ 角色参考图片不存在: {abs_path}"

    try:
        # 执行命令
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10分钟超时
            cwd=WORKSPACE_PATH
        )

        output = result.stdout
        error = result.stderr

        print(f"命令输出:\n{output}")
        if error:
            print(f"命令错误:\n{error}")

        if result.returncode != 0:
            # 检查是否是认证错误
            if "Unauthorized" in output or "401" in output:
                return f"❌ Kling API 认证失败。请检查 AK/SK 配置。\n{output}"
            return f"❌ 视频生成失败：{output}"

        # 解析输出，提取视频信息
        return _parse_kling_output(output)

    except subprocess.TimeoutExpired:
        return f"❌ 视频生成超时（10分钟），请稍后检查任务状态"
    except Exception as e:
        return f"❌ 执行异常：{str(e)}"


@tool
def kling_cli_image_to_video(
    prompt: str,
    image_url: str,
    model: str = "kling-v3-omni",
    mode: str = "pro",
    aspect_ratio: str = "9:16",
    duration: int = 5,
    sound: str = "on"
) -> str:
    """
    使用快手 Kling AI Skill 将图片转换为视频（图生视频）。

    Args:
        prompt: 对图片的动作描述，例如"风吹头发"
        image_url: 源图片的 URL 或本地路径
        model: 使用的模型，默认 kling-v3-omni
        mode: 视频质量模式，pro (1080P) 或 std (720P)
        aspect_ratio: 视频比例，默认 9:16
        duration: 视频时长（秒），默认 5 秒
        sound: 是否生成音频，on 或 off

    Returns:
        生成的视频信息
    """
    ctx = request_context.get() or new_context(method="kling_cli_image_to_video")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 处理图片路径
    if image_url.startswith("http://") or image_url.startswith("https://"):
        abs_image_path = image_url
    else:
        abs_image_path = os.path.join(WORKSPACE_PATH, image_url.lstrip("/"))
        if not os.path.exists(abs_image_path):
            return f"❌ 源图片不存在: {abs_image_path}"

    # 构建命令
    cmd = [
        "node",
        KLING_SCRIPT_PATH,
        "video",
        "--prompt", prompt,
        "--image", abs_image_path,
        "--model", model,
        "--mode", mode,
        "--aspect_ratio", aspect_ratio,
        "--duration", str(duration),
        "--sound", sound,
        "--output_dir", OUTPUT_DIR
    ]

    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=WORKSPACE_PATH
        )

        output = result.stdout
        error = result.stderr

        print(f"命令输出:\n{output}")
        if error:
            print(f"命令错误:\n{error}")

        if result.returncode != 0:
            return f"❌ 视频生成失败：{output}"

        return _parse_kling_output(output)

    except subprocess.TimeoutExpired:
        return f"❌ 视频生成超时（10分钟）"
    except Exception as e:
        return f"❌ 执行异常：{str(e)}"


@tool
def kling_cli_create_subject(
    name: str,
    description: str,
    frontal_image: str
) -> str:
    """
    创建可复用的角色/主体，用于跨视频保持人物一致性。

    Args:
        name: 角色名称，例如"香道文化传播者"
        description: 角色描述，例如"一位温婉的女性，穿着中式服装"
        frontal_image: 正面参考图片的本地路径

    Returns:
        创建的角色信息，包含角色 ID

    Example:
        kling_cli_create_subject(
            name="香道文化传播者",
            description="一位温婉的女性，穿着白色中式服装，长发披肩，面带微笑",
            frontal_image="assets/character_reference/frontal.jpg"
        )
    """
    ctx = request_context.get() or new_context(method="kling_cli_create_subject")

    # 处理图片路径
    abs_image_path = os.path.join(WORKSPACE_PATH, frontal_image.lstrip("/"))
    if not os.path.exists(abs_image_path):
        return f"❌ 正面参考图片不存在: {abs_image_path}"

    # 构建命令
    cmd = [
        "node",
        KLING_SCRIPT_PATH,
        "element",
        "--action", "create",
        "--name", name,
        "--description", description,
        "--ref_type", "image_refer",
        "--frontal_image", abs_image_path
    ]

    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2分钟超时
            cwd=WORKSPACE_PATH
        )

        output = result.stdout
        error = result.stderr

        print(f"命令输出:\n{output}")
        if error:
            print(f"命令错误:\n{error}")

        if result.returncode != 0:
            return f"❌ 创建角色失败：{output}"

        # 解析输出，提取角色 ID
        element_id_match = re.search(r'element[_\s]?id[:\s]+(\d+)', output, re.IGNORECASE)
        if element_id_match:
            element_id = element_id_match.group(1)
            return f"✅ 角色创建成功！\n👤 角色名称: {name}\n🆔 角色ID: {element_id}\n📝 描述: {description}\n\n使用角色ID生成视频时，在 kling_cli_text_to_video 中添加 --element_ids 参数。"

        return f"✅ 角色创建成功！\n{output}"

    except subprocess.TimeoutExpired:
        return f"❌ 创建角色超时（2分钟）"
    except Exception as e:
        return f"❌ 执行异常：{str(e)}"


@tool
def kling_cli_list_subjects() -> str:
    """
    列出所有已创建的角色/主体。

    Returns:
        角色列表
    """
    ctx = request_context.get() or new_context(method="kling_cli_list_subjects")

    cmd = [
        "node",
        KLING_SCRIPT_PATH,
        "element",
        "--action", "list"
    ]

    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=WORKSPACE_PATH
        )

        output = result.stdout
        error = result.stderr

        if result.returncode != 0:
            return f"❌ 获取角色列表失败：{output}"

        return f"📋 角色列表:\n{output}"

    except Exception as e:
        return f"❌ 执行异常：{str(e)}"


@tool
def kling_cli_account_info() -> str:
    """
    查询 Kling AI 账号信息和剩余配额。

    Returns:
        账号信息，包含资源包和剩余额度
    """
    ctx = request_context.get() or new_context(method="kling_cli_account_info")

    cmd = [
        "node",
        KLING_SCRIPT_PATH,
        "account",
        "--costs"
    ]

    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=WORKSPACE_PATH
        )

        output = result.stdout
        error = result.stderr

        if result.returncode != 0:
            return f"❌ 获取账号信息失败：{output}"

        return f"📊 账号信息:\n{output}"

    except Exception as e:
        return f"❌ 执行异常：{str(e)}"


def _parse_kling_output(output: str) -> str:
    """
    解析 Kling AI Skill 的输出，提取视频信息。

    Args:
        output: 命令输出

    Returns:
        格式化的视频信息
    """
    # 提取 task_id
    task_id_match = re.search(r'task[_\s]?id[:\s]+([a-zA-Z0-9_-]+)', output, re.IGNORECASE)
    task_id = task_id_match.group(1) if task_id_match else "未知"

    # 提取本地文件路径
    local_paths = []
    path_matches = re.finditer(r'[/\\][\w\-./]+\.(?:mp4|mov|avi|mkv)', output)
    for match in path_matches:
        path = match.group(0)
        if path not in local_paths:
            local_paths.append(path)

    # 提取 URL
    urls = []
    url_matches = re.finditer(r'https?://[^\s<>"]+\.mp4', output)
    for match in url_matches:
        url = match.group(0)
        if url not in urls:
            urls.append(url)

    # 构建返回信息
    result_parts = ["✅ 视频生成成功！", f"🆔 任务ID: {task_id}"]

    if local_paths:
        result_parts.append("\n📁 本地文件:")
        for path in local_paths:
            result_parts.append(f"  - {path}")

    if urls:
        result_parts.append("\n🔗 在线链接:")
        for url in urls:
            result_parts.append(f"  - {url}")

    # 如果没有找到路径，返回原始输出
    if not local_paths and not urls:
        result_parts.append(f"\n📄 原始输出:\n{output}")

    return "\n".join(result_parts)
