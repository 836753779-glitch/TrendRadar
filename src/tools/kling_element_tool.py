from langchain.tools import tool
import subprocess
import os
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

# Kling AI Skill 路径
WORKSPACE_PATH = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
KLING_SCRIPT_PATH = os.path.join(WORKSPACE_PATH, "klingai", "scripts", "kling.mjs")
OUTPUT_DIR = os.path.join(WORKSPACE_PATH, "assets", "kling_output")

# 角色ID配置
ELEMENT_CONFIG_PATH = os.path.join(WORKSPACE_PATH, "assets", "character_element.json")


def _get_element_id() -> str:
    """获取角色ID"""
    try:
        with open(ELEMENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("element_id", "")
    except:
        return ""


@tool
def kling_cli_text_to_video_with_element(
    prompt: str,
    element_id: str = None,
    model: str = "kling-v3-omni",
    mode: str = "pro",
    aspect_ratio: str = "9:16",
    duration: int = 5,
    sound: str = "off"
) -> str:
    """
    使用 Kling AI 角色主体生成视频，确保人物完全一致。

    这是最佳的人物一致性方案！使用预先创建的角色主体（Element ID）生成视频，
    所有视频都使用同一个角色，人物100%一致。

    Args:
        prompt: 视频场景的文本描述（只需描述场景和动作，不需要描述人物）
        element_id: 角色主体ID（可选，不传则使用默认角色"香道文化传播者"）
        model: 使用的模型，默认 kling-v3-omni（最新 O3 模型）
        mode: 视频质量模式，pro (1080P) 或 std (720P)
        aspect_ratio: 视频比例，16:9 / 9:16 / 1:1
        duration: 视频时长（秒），3-15 秒
        sound: 是否生成音频，on 或 off

    Returns:
        生成的视频信息

    Example:
        # 使用默认角色（香道文化传播者）
        kling_cli_text_to_video_with_element(
            prompt="手持线香，优雅展示",
            duration=5
        )

        # 使用特定角色ID
        kling_cli_text_to_video_with_element(
            prompt="手持线香，优雅展示",
            element_id="308110838358255"
        )
    """
    ctx = request_context.get() or new_context(method="kling_cli_text_to_video_with_element")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 获取角色ID
    if not element_id:
        element_id = _get_element_id()

    if not element_id:
        return f"❌ 错误：未找到角色主体ID。请先创建角色主体或明确传入 element_id 参数。"

    # 构建命令
    cmd = [
        "node",
        KLING_SCRIPT_PATH,
        "video",
        "--prompt", prompt,
        "--element_ids", element_id,
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


def _parse_kling_output(output: str) -> str:
    """解析 Kling AI Skill 的输出"""
    # 提取 task_id
    import re
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
    result_parts = [
        "✅ 视频生成成功！（使用角色主体）",
        f"🆔 任务ID: {task_id}",
        f"👤 角色主体ID: {_get_element_id()}"
    ]

    if local_paths:
        result_parts.append("\n📁 本地文件:")
        for path in local_paths:
            result_parts.append(f"  - {path}")

    if urls:
        result_parts.append("\n🔗 在线链接:")
        for url in urls:
            result_parts.append(f"  - {url}")

    if not local_paths and not urls:
        result_parts.append(f"\n📄 原始输出:\n{output}")

    return "\n".join(result_parts)


# 导入 json 模块
import json
