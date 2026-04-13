"""
火山方舟视频生成工具（使用 Bearer Token 认证）
用于调用 Seedance 2.0、Seedance 1.0 Pro 等火山方舟视频生成模型
"""
import time
import requests


class VolcanoArkVideoClient:
    """火山方舟视频生成客户端（Bearer Token 认证）"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://ark.cn-beijing.volces.com"

    def generate_video(
        self,
        model: str,
        content_items: list,
        return_last_frame: bool = False,
        callback_url: str = None
    ) -> tuple[str, dict, str]:
        """
        生成视频

        Args:
            model: 模型 ID（如 doubao-seedance-2-0, doubao-seedance-1-0-pro-250528）
            content_items: 内容项列表（TextContent, ImageURLContent）
            return_last_frame: 是否返回最后一帧
            callback_url: 回调 URL

        Returns:
            (视频URL, 完整响应, 最后一帧URL)
        """
        path = "/api/v3/contents/generations/tasks"
        url = f"{self.base_url}{path}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Client-Request-Id": "Coze,Integrations",
        }

        request_body = {
            "model": model,
            "content": content_items,
            "return_last_frame": return_last_frame,
        }

        if callback_url:
            request_body["callback_url"] = callback_url

        try:
            # 创建任务
            response = requests.post(url, json=request_body, headers=headers)
            response.raise_for_status()
            data = response.json()
            task_id = data.get("id")

            if not task_id:
                error = data.get('error', {})
                raise Exception(f"创建任务失败: {error.get('message', '未知错误')}")

            # 轮询任务状态
            return self._poll_task_status(task_id, headers)

        except requests.exceptions.RequestException as e:
            raise Exception(f"视频生成任务创建失败: {str(e)}")

    def _poll_task_status(self, task_id: str, headers: dict) -> tuple[str, dict, str]:
        """
        轮询任务状态

        Args:
            task_id: 任务 ID
            headers: 请求头

        Returns:
            (视频URL, 完整响应, 最后一帧URL)
        """
        path = f"/api/v3/contents/generations/tasks/{task_id}"
        url = f"{self.base_url}{path}"

        max_wait_time = 900  # 最大等待时间 15 分钟
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                error = data.get('error')
                if error:
                    raise Exception(f"视频生成失败: {error.get('message', '未知错误')}")

                status = data.get('status')

                if status == 'cancelled':
                    return '', data, ''
                elif status == 'failed':
                    error_msg = data.get('error', {}).get('message', '未知错误')
                    raise Exception(f"视频生成失败: {error_msg}")
                elif status in ['queued', 'running']:
                    time.sleep(2)
                    continue
                elif status == 'succeeded':
                    video_url = data.get('content', {}).get('video_url', '')
                    last_frame_url = data.get('content', {}).get('last_frame_url', '')
                    return video_url, data, last_frame_url
                else:
                    time.sleep(2)
                    continue

            except requests.exceptions.RequestException as e:
                raise Exception(f"网络请求失败: {str(e)}")
            except Exception as e:
                raise Exception(f"轮询任务状态失败: {str(e)}")

        raise Exception("视频生成超时")


# 测试代码
if __name__ == "__main__":
    # 使用用户提供的火山方舟 API Key
    API_KEY = "5debae72-3ff1-48f3-ab82-dcbb19b83646"

    client = VolcanoArkVideoClient(API_KEY)

    # 测试 Seedance 2.0 模型
    print("=== 测试 Seedance 2.0 模型 ===")
    try:
        content_items = [
            {
                "type": "text",
                "text": "一个女孩在海边散步，夕阳西下，暖金色的阳光洒满海面和沙滩，女孩穿着白色连衣裙，长发被海风轻轻吹动，电影感，高质量"
            }
        ]

        video_url, response, last_frame_url = client.generate_video(
            model="doubao-seedance-2-0",
            content_items=content_items,
            return_last_frame=True
        )

        print(f"✅ 视频生成成功！")
        print(f"视频 URL: {video_url}")
        print(f"最后一帧 URL: {last_frame_url}")
        print(f"视频时长: {response.get('duration', 0)} 秒")
        print(f"分辨率: {response.get('resolution', 'unknown')}")

    except Exception as e:
        print(f"❌ Seedance 2.0 测试失败: {str(e)}")

    # 测试 Seedance 1.0 Pro 模型
    print("\n=== 测试 Seedance 1.0 Pro 模型 ===")
    try:
        content_items = [
            {
                "type": "text",
                "text": "一个男孩在城市街道上行走，霓虹灯闪烁，赛博朋克风格，电影感"
            }
        ]

        video_url, response, last_frame_url = client.generate_video(
            model="doubao-seedance-1-0-pro-250528",
            content_items=content_items
        )

        print(f"✅ 视频生成成功！")
        print(f"视频 URL: {video_url}")
        print(f"视频时长: {response.get('duration', 0)} 秒")
        print(f"分辨率: {response.get('resolution', 'unknown')}")

    except Exception as e:
        print(f"❌ Seedance 1.0 Pro 测试失败: {str(e)}")
