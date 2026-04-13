#!/usr/bin/env python3
import os
import requests
from coze_coding_dev_sdk.s3 import S3SyncStorage

# 三张新照片的URL
new_character_photos = [
    {
        "name": "character_multi_angle_1.png",
        "url": "https://code.coze.cn/api/sandbox/coze_coding/file/proxy?expire_time=-1&file_path=assets%2F%E7%94%9F%E6%88%90%E7%99%BD%E5%BA%95%E5%A4%9A%E8%A7%92%E5%BA%A6%E7%85%A7%E7%89%87+%285%29.png&nonce=7a4391c9-cff8-4c5d-82b0-9318debe7837&project_id=7628070821923389483&sign=d609dbddf62f3556616bd2feb21152043965909c8d2b599253eec746c661335a"
    },
    {
        "name": "character_multi_angle_2.png",
        "url": "https://code.coze.cn/api/sandbox/coze_coding/file/proxy?expire_time=-1&file_path=assets%2F%E7%94%9F%E6%88%90%E7%99%BD%E5%BA%95%E5%A4%9A%E8%A7%92%E5%BA%A6%E7%85%A7%E7%89%87+%284%29.png&nonce=d32d2956-9e92-425b-80b9-283d44f0bb9e&project_id=7628070821923389483&sign=9b8810b6a74ef8da23bbb61a4f6fbb633d27740a04a25ed80d1fc2b9f48c38ad"
    },
    {
        "name": "character_multi_angle_3.png",
        "url": "https://code.coze.cn/api/sandbox/coze_coding/file/proxy?expire_time=-1&file_path=assets%2F%E7%94%9F%E6%88%90%E7%99%BD%E5%BA%95%E5%A4%9A%E8%A7%92%E5%BA%A6%E7%85%A7%E7%89%87+%283%29.png&nonce=fbeb3aa9-11aa-43db-a794-9306fb2176e3&project_id=7628070821923389483&sign=5bbadf0f772dfab87cd959b86a2dcd70a46a8b8f841d2cedd2766f98ff64ac9f"
    }
]

workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
temp_dir = os.path.join(workspace_path, "assets/new_character_photos")

# 创建临时目录
os.makedirs(temp_dir, exist_ok=True)

# 初始化对象存储
storage = S3SyncStorage(
    endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
    access_key="",
    secret_key="",
    bucket_name=os.getenv("COZE_BUCKET_NAME"),
    region="cn-beijing",
)

print("=" * 60)
print("开始下载并上传新的角色照片")
print("=" * 60)

uploaded_urls = []

for i, photo_info in enumerate(new_character_photos):
    print(f"\n正在处理第 {i+1} 张照片...")
    print(f"  名称: {photo_info['name']}")

    # 下载照片
    try:
        response = requests.get(photo_info['url'], timeout=30)
        response.raise_for_status()

        # 保存到本地
        local_path = os.path.join(temp_dir, photo_info['name'])
        with open(local_path, 'wb') as f:
            f.write(response.content)

        print(f"  ✅ 已下载到: {local_path}")

        # 上传到对象存储
        with open(local_path, 'rb') as f:
            file_key = storage.stream_upload_file(
                fileobj=f,
                file_name=photo_info['name'],
                content_type="image/png"
            )

        print(f"  ✅ 已上传到对象存储")
        print(f"     文件Key: {file_key}")

        # 生成签名 URL（有效期 30 天）
        signed_url = storage.generate_presigned_url(
            key=file_key,
            expire_time=30 * 24 * 60 * 60  # 30 天
        )

        uploaded_urls.append({
            "name": photo_info['name'],
            "key": file_key,
            "url": signed_url
        })

        print(f"  ✅ 访问URL已生成")

    except Exception as e:
        print(f"  ❌ 处理失败: {str(e)}")
        continue

print("\n" + "=" * 60)
print(f"成功上传 {len(uploaded_urls)} 张新的角色照片")
print("=" * 60)

# 输出JSON格式的结果
import json
print("\n角色参考图片 URL 列表（JSON格式）：")
print(json.dumps(uploaded_urls, indent=2, ensure_ascii=False))
