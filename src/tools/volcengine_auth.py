"""
火山引擎 API 签名认证工具
用于使用 AccessKey 和 SecretKey 调用火山引擎 API
"""
import hashlib
import hmac
import time
import json
from typing import Dict, Optional
import requests


class VolcengineAuth:
    """火山引擎 API 签名认证"""

    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key

    def sign(self, method: str, path: str, headers: Dict[str, str], params: Dict = None, body: str = "") -> str:
        """
        生成签名

        Args:
            method: HTTP 方法（GET/POST/PUT/DELETE）
            path: 请求路径
            headers: 请求头
            params: 查询参数
            body: 请求体

        Returns:
            签名字符串
        """
        # 1. 构造规范化查询字符串
        if params:
            sorted_params = sorted(params.items())
            query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        else:
            query_string = ""

        # 2. 构造规范化请求
        canonical_headers = []
        for k in sorted(headers.keys()):
            canonical_headers.append(f"{k.lower()}:{headers[k].strip()}")

        canonical_headers_str = '\n'.join(canonical_headers)
        signed_headers = ';'.join([k.lower() for k in sorted(headers.keys())])

        canonical_request = f"{method}\n{path}\n{query_string}\n{canonical_headers_str}\n\n{signed_headers}\n{hashlib.sha256(body.encode()).hexdigest()}"

        # 3. 构造待签名字符串
        date = headers.get('X-Date', time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
        credential_scope = f"{date[:8]}/cn-beijing/ark/request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode()).hexdigest()

        string_to_sign = f"HMAC-SHA256\n{date}\n{credential_scope}\n{hashed_canonical_request}"

        # 4. 计算签名
        k_date = hmac.new(self.secret_key.encode(), date[:8].encode(), hashlib.sha256).digest()
        k_region = hmac.new(k_date, 'cn-beijing'.encode(), hashlib.sha256).digest()
        k_service = hmac.new(k_region, 'ark'.encode(), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, 'request'.encode(), hashlib.sha256).digest()

        signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

        # 5. 构造 Authorization 头
        authorization = f"HMAC-SHA256 Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

        return authorization


class VolcengineVideoClient:
    """火山引擎视频生成客户端"""

    def __init__(self, access_key: str, secret_key: str):
        self.auth = VolcengineAuth(access_key, secret_key)
        self.base_url = "https://ark.cn-beijing.volces.com"
        self.access_key = access_key

    def generate_video(
        self,
        model: str,
        content_items: list,
        return_last_frame: bool = False
    ) -> tuple[str, dict]:
        """
        生成视频

        Args:
            model: 模型 ID（如 doubao-seedance-2-0）
            content_items: 内容项列表
            return_last_frame: 是否返回最后一帧

        Returns:
            (视频URL, 完整响应)
        """
        path = "/api/v3/contents/generations/tasks"
        url = f"{self.base_url}{path}"

        date = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())

        headers = {
            "Content-Type": "application/json",
            "X-Date": date,
            "Host": "ark.cn-beijing.volces.com",
        }

        request_body = {
            "model": model,
            "content": content_items,
            "return_last_frame": return_last_frame,
        }

        body_str = json.dumps(request_body, separators=(',', ':'))

        # 生成签名
        authorization = self.auth.sign("POST", path, headers, body=body_str)
        headers["Authorization"] = authorization

        try:
            # 创建任务
            response = requests.post(url, json=request_body, headers=headers)
            response.raise_for_status()
            data = response.json()
            task_id = data.get("id")

            if not task_id:
                return "", data

            # 轮询任务状态
            return self._poll_task_status(task_id, headers)

        except Exception as e:
            raise Exception(f"视频生成失败: {str(e)}")

    def _poll_task_status(self, task_id: str, headers: dict) -> tuple[str, dict]:
        """
        轮询任务状态

        Args:
            task_id: 任务 ID
            headers: 请求头（需要包含 Authorization）

        Returns:
            (视频URL, 完整响应)
        """
        path = f"/api/v3/contents/generations/tasks/{task_id}"
        url = f"{self.base_url}{path}"

        import time

        max_wait_time = 900  # 最大等待时间 15 分钟
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                status = data.get('status')

                if status == 'cancelled':
                    return '', data
                elif status == 'failed':
                    error_msg = data.get('error', {}).get('message', '未知错误')
                    raise Exception(f"视频生成失败: {error_msg}")
                elif status in ['queued', 'running']:
                    time.sleep(2)
                    continue
                elif status == 'succeeded':
                    video_url = data.get('content', {}).get('video_url', '')
                    return video_url, data
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
    # 使用用户提供的 LIBTV 密钥
    ACCESS_KEY = "gZJBpcV_KfpTNerz5VLWYg"
    SECRET_KEY = "kI_O7iwXioLkdgZvcpsYg63ZsDCdQBcl"

    client = VolcengineVideoClient(ACCESS_KEY, SECRET_KEY)

    # 测试 Seedance 2.0 模型
    try:
        content_items = [
            {
                "type": "text",
                "text": "一个女孩在海边散步，夕阳西下，暖金色的阳光洒满海面和沙滩，电影感"
            }
        ]

        video_url, response = client.generate_video(
            model="doubao-seedance-2-0",
            content_items=content_items
        )

        print(f"视频 URL: {video_url}")
        print(f"完整响应: {json.dumps(response, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"测试失败: {str(e)}")
