#!/usr/bin/env python3
import os
from coze_coding_dev_sdk.s3 import S3SyncStorage

# 初始化对象存储
storage = S3SyncStorage(
    endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
    access_key="",
    secret_key="",
    bucket_name=os.getenv("COZE_BUCKET_NAME"),
    region="cn-beijing",
)

# 角色照片文件路径
workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
character_photos = [
    os.path.join(workspace_path, "assets/cd49a217-6f46-4a44-8f6b-f3f0288942a0.jpeg"),
    os.path.join(workspace_path, "assets/mmexport1742522627339.jpg"),
]

# 上传照片并获取 URL
print("开始上传角色照片到对象存储...")
uploaded_urls = []

for i, photo_path in enumerate(character_photos):
    if not os.path.exists(photo_path):
        print(f"❌ 文件不存在: {photo_path}")
        continue

    file_name = f"character_reference_{i+1}.jpeg"

    # 上传文件
    with open(photo_path, 'rb') as f:
        file_key = storage.stream_upload_file(
            fileobj=f,
            file_name=file_name,
            content_type="image/jpeg"
        )

    print(f"✅ 已上传: {file_name}")
    print(f"   文件Key: {file_key}")

    # 生成签名 URL（有效期 30 天）
    signed_url = storage.generate_presigned_url(
        key=file_key,
        expire_time=30 * 24 * 60 * 60  # 30 天
    )

    uploaded_urls.append({
        "name": file_name,
        "key": file_key,
        "url": signed_url
    })

    print(f"   访问URL: {signed_url}")
    print()

print("=" * 60)
print(f"成功上传 {len(uploaded_urls)} 张角色照片")
print("=" * 60)
print("\n角色参考图片 URL 列表：")
for item in uploaded_urls:
    print(f"{item['name']}: {item['url']}")
