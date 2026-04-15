from langchain.tools import tool
import os
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk.s3 import S3SyncStorage

# 初始化对象存储客户端
storage = S3SyncStorage(
    endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
    access_key="",
    secret_key="",
    bucket_name=os.getenv("COZE_BUCKET_NAME"),
    region="cn-beijing"
)


# 提取公共逻辑为普通函数（可被其他函数调用）
def _upload_video_to_storage_raw(
    local_video_path: str,
    file_name: str = None,
    expire_hours: int = 24
) -> str:
    """
    将本地视频上传到对象存储（内部函数，不使用 @tool 装饰）。

    Args:
        local_video_path: 本地视频文件路径
        file_name: 文件名（可选，不传则使用原文件名）
        expire_hours: 链接有效期（小时，默认24小时）

    Returns:
        视频的公开访问URL
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(local_video_path):
            return f"❌ 文件不存在：{local_video_path}"

        # 确定文件名
        if not file_name:
            file_name = os.path.basename(local_video_path)

        # 上传视频文件（使用流式上传，支持大文件）
        print(f"正在上传视频：{local_video_path}")
        with open(local_video_path, "rb") as f:
            # 上传并获取对象key
            file_key = storage.stream_upload_file(
                fileobj=f,
                file_name=file_name,
                content_type="video/mp4",
                multipart_chunksize=5 * 1024 * 1024,  # 5MB分片
                multipart_threshold=5 * 1024 * 1024,  # 5MB触发分片
                max_concurrency=1,
                use_threads=False
            )

        print(f"✅ 上传成功，对象Key：{file_key}")

        # 生成签名URL
        expire_time = expire_hours * 3600  # 转换为秒
        public_url = storage.generate_presigned_url(
            key=file_key,
            expire_time=expire_time
        )

        print(f"✅ 生成公开URL，有效期：{expire_hours}小时")

        # 返回结果
        return f"""✅ 视频上传成功！

📁 文件信息：
  - 本地路径：{local_video_path}
  - 对象Key：{file_key}
  - 文件名：{file_name}

🔗 公开访问URL：
  {public_url}

⏰ 有效期：{expire_hours}小时

💡 提示：
  - 您可以直接使用此URL在飞书中查看视频
  - URL过期后需要重新生成
"""

    except Exception as e:
        return f"❌ 视频上传失败：{str(e)}"


@tool
def upload_video_to_storage(
    local_video_path: str,
    file_name: str = None,
    expire_hours: int = 24
) -> str:
    """
    将本地视频上传到对象存储，获取可访问的公开链接。

    解决视频文件无法通过飞书查看的问题。

    Args:
        local_video_path: 本地视频文件路径
        file_name: 文件名（可选，不传则使用原文件名）
        expire_hours: 链接有效期（小时，默认24小时）

    Returns:
        视频的公开访问URL

    Example:
        upload_video_to_storage(
            local_video_path="/workspace/projects/assets/final_output/video.mp4",
            file_name="product_intro.mp4",
            expire_hours=48
        )
    """
    ctx = request_context.get() or new_context(method="upload_video_to_storage")

    # 调用普通函数完成实际上传
    return _upload_video_to_storage_raw(
        local_video_path=local_video_path,
        file_name=file_name,
        expire_hours=expire_hours
    )


@tool
def upload_and_notify_feishu(
    local_video_path: str,
    title: str = "视频生成完成",
    description: str = None,
    video_duration: int = None,
    file_name: str = None,
    expire_hours: int = 48
) -> str:
    """
    上传视频到对象存储并推送到飞书（一步完成）。

    Args:
        local_video_path: 本地视频文件路径
        title: 飞书通知标题
        description: 视频描述
        video_duration: 视频时长（秒）
        file_name: 存储文件名（可选）
        expire_hours: 链接有效期（小时，默认48小时）

    Returns:
        上传和推送结果

    Example:
        upload_and_notify_feishu(
            local_video_path="/workspace/projects/assets/final_output/video.mp4",
            title="线香产品介绍视频",
            description="这是关于'静谧禅心'线香的介绍视频",
            video_duration=60
        )
    """
    ctx = request_context.get() or new_context(method="upload_and_notify_feishu")

    try:
        # 步骤1：上传视频（调用普通函数，避免 @tool 调用问题）
        upload_result = _upload_video_to_storage_raw(
            local_video_path=local_video_path,
            file_name=file_name,
            expire_hours=expire_hours
        )

        if "❌" in upload_result:
            return f"❌ 上传失败：{upload_result}"

        # 提取公开URL
        import re
        url_match = re.search(r'https?://[^\s]+', upload_result)
        if not url_match:
            return f"❌ 无法提取公开URL：{upload_result}"

        public_url = url_match.group(0)

        # 步骤2：推送到飞书（调用普通函数，避免 @tool 调用问题）
        from tools.feishu_notification_tool import _send_feishu_video_raw

        feishu_result = _send_feishu_video_raw(
            title=title,
            video_url=public_url,
            description=description,
            video_duration=video_duration
        )

        # 返回完整结果
        return f"""✅ 视频上传并推送成功！

📹 视频信息：
  - 标题：{title}
  - 本地路径：{local_video_path}
  - 公开URL：{public_url}
  - 时长：{video_duration}秒（如果提供）

📢 飞书通知：{feishu_result}

💡 提示：
  - 您可以在飞书中直接查看视频
  - URL有效期：{expire_hours}小时
"""

    except Exception as e:
        return f"❌ 上传并推送失败：{str(e)}"
