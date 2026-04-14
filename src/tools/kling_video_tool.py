from langchain.tools import tool
import requests
import json
import time
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

# Kling O3 API 配置
KLING_ACCESS_KEY = "AFRYabFrgBmh3nybnYkd9LNJtd4FBFQf"
KLING_SECRET_KEY = "ECQfkNk3narb39fyAyR9A8dtTrrgLrEr"

# Kling API 可能的 endpoints
KLING_API_ENDPOINTS = [
    "https://api.klingai.com/v1/videos/text2video",
    "https://openapi.klingai.com/v1/videos/generations",
    "https://api.klingai.com/api/v1/videos/text2video"
]


@tool
def kling_text_to_video(
    prompt: str,
    character_image_url: str,
    resolution: str = "720p",
    ratio: str = "9:16",
    duration: int = 5
) -> str:
    """
    使用快手 Kling O3 模型生成视频，支持角色参考图片。

    通过指定角色参考图片，确保生成视频中人物保持一致。

    Args:
        prompt: 视频场景的文本描述，需要详细描述画面内容、风格、氛围等
        character_image_url: 角色参考图片的URL，必须是公开访问的图片链接
        resolution: 视频分辨率，支持 720p/1080p，默认720p
        ratio: 视频比例，支持 9:16/16:9，默认9:16（适合竖屏）
        duration: 视频时长（秒），范围5-10秒，默认5秒

    Returns:
        生成的视频URL，如果生成失败则返回错误信息

    Example:
        kling_text_to_video(
            prompt="一位温婉的女性在茶室中手持线香，面带微笑",
            character_image_url="https://example.com/character.jpg"
        )
    """
    ctx = request_context.get() or new_context(method="kling_text_to_video")

    # 尝试多种认证方式
    auth_methods = [
        # 方法1: Bearer Token
        {
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {KLING_ACCESS_KEY}"
            },
            "description": "Bearer Token"
        },
        # 方法2: API Key in header
        {
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": KLING_ACCESS_KEY,
                "X-API-Secret": KLING_SECRET_KEY
            },
            "description": "API Key in header"
        },
        # 方法3: API Key + Secret in body
        {
            "headers": {
                "Content-Type": "application/json"
            },
            "description": "API Key in body"
        }
    ]

    # 构造请求体
    request_body = {
        "prompt": prompt,
        "reference_image": character_image_url,
        "resolution": resolution,
        "ratio": ratio,
        "duration": duration,
        "model": "kling-3.0"
    }

    for endpoint in KLING_API_ENDPOINTS:
        for auth_method in auth_methods:
            try:
                print(f"尝试调用: {endpoint} - {auth_method['description']}")

                # 构造最终的请求体（如果需要 API Key in body）
                final_body = request_body.copy()
                if "API Key in body" in auth_method['description']:
                    final_body["api_key"] = KLING_ACCESS_KEY
                    final_body["secret_key"] = KLING_SECRET_KEY

                # 发送请求
                response = requests.post(
                    endpoint,
                    headers=auth_method["headers"],
                    json=final_body,
                    timeout=30
                )

                print(f"响应状态码: {response.status_code}")
                print(f"响应内容: {response.text[:500]}")

                if response.status_code == 200:
                    result = response.json()

                    # 检查返回数据
                    if isinstance(result, dict):
                        if "data" in result and "video_url" in result["data"]:
                            # 直接返回视频 URL
                            video_url = result["data"]["video_url"]
                            return f"✅ 视频生成成功！（Kling O3）\n📹 模型: Kling O3\n🔗 视频URL: {video_url}\n⏱️ 视频时长: {duration}秒\n📐 分辨率: {resolution} ({ratio})\n📸 角色参考: {character_image_url}"
                        elif "task_id" in result:
                            # 需要轮询任务状态
                            task_id = result["task_id"]
                            return _poll_kling_task(endpoint, task_id, auth_method["headers"])
                        else:
                            return f"⚠️ 未知响应格式: {json.dumps(result, ensure_ascii=False, indent=2)}"
                    else:
                        return f"⚠️ 非字典响应: {response.text[:500]}"

                elif response.status_code == 401:
                    # 认证失败，尝试下一个认证方式
                    print("认证失败，尝试下一个方式...")
                    continue
                elif response.status_code == 404:
                    # 端点不存在，尝试下一个端点
                    print(f"端点不存在: {endpoint}")
                    break
                else:
                    # 其他错误
                    try:
                        error_info = response.json()
                        return f"❌ API 调用失败（{response.status_code}）：{json.dumps(error_info, ensure_ascii=False)}"
                    except:
                        return f"❌ API 调用失败（{response.status_code}）：{response.text[:500]}"

            except Exception as e:
                print(f"请求异常: {str(e)}")
                continue

    return f"❌ 所有尝试均失败。请检查 API Key 和 Secret Key 是否正确，以及 API endpoint 是否有效。\n\n已尝试的端点:\n" + "\n".join([f"- {ep}" for ep in KLING_API_ENDPOINTS])


def _poll_kling_task(endpoint: str, task_id: str, headers: dict) -> str:
    """轮询 Kling 任务状态"""
    max_wait_time = 300  # 最长等待5分钟
    poll_interval = 5    # 每5秒查询一次
    elapsed_time = 0

    while elapsed_time < max_wait_time:
        try:
            response = requests.get(
                f"{endpoint}/task/{task_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if isinstance(result, dict):
                    task_data = result.get("data", result)
                    task_status = task_data.get("status", "")

                    if task_status == "succeeded":
                        video_url = task_data.get("video_url") or task_data.get("result", {}).get("video_url")
                        if video_url:
                            return f"✅ 视频生成成功！（Kling O3）\n📹 模型: Kling O3\n🔗 视频URL: {video_url}"
                        else:
                            return f"❌ 任务完成但未返回视频 URL"

                    elif task_status == "failed":
                        error_msg = task_data.get("error_msg", task_data.get("error", "未知错误"))
                        return f"❌ 视频生成失败：{error_msg}"

                    elif task_status in ["pending", "processing"]:
                        # 任务进行中，继续等待
                        print(f"任务状态: {task_status}, 已等待 {elapsed_time} 秒")
                        pass
                    else:
                        return f"❌ 未知任务状态：{task_status}"

            time.sleep(poll_interval)
            elapsed_time += poll_interval

        except Exception as e:
            print(f"轮询异常: {str(e)}")
            time.sleep(poll_interval)
            elapsed_time += poll_interval

    return f"❌ 视频生成超时（{max_wait_time}秒）"
