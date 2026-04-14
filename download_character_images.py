#!/usr/bin/env python3
"""
下载角色参考图片到本地
"""
import requests
import os

# 创建输出目录
output_dir = "assets/character_reference"
os.makedirs(output_dir, exist_ok=True)

# 角色参考图片 URL
image_urls = [
    {
        "name": "character_multi_angle_1.png",
        "url": "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_multi_angle_1_cb7a3416.png?sign=1778652989-da2a893e20-0-de927973c424323898dbdf9ed8f746551aa2d9ad6fa7eb814f81ba884f184f07",
        "is_primary": True
    },
    {
        "name": "character_multi_angle_2.png",
        "url": "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_multi_angle_2_778839da.png?sign=1778652991-ffeb9b9ce8-0-19a1f6ebee16ec194895fdf00c0c61ab88b7e4f5ba722f0e211de375ea14dea5",
        "is_primary": False
    },
    {
        "name": "character_multi_angle_3.png",
        "url": "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_multi_angle_3_aea94f9a.png?sign=1778652992-2b84306c5d-0-ed4cc9c0855b3ae84c0ed30c26f2796162699d15e55cfced90bd15ea3e789529",
        "is_primary": False
    }
]

print("开始下载角色参考图片...")

for image in image_urls:
    output_path = os.path.join(output_dir, image["name"])

    print(f"下载 {image['name']}...")

    try:
        response = requests.get(image["url"], timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        file_size = os.path.getsize(output_path)
        print(f"✅ {image['name']} 下载成功 ({file_size} bytes)")
        print(f"   保存路径: {output_path}")

    except Exception as e:
        print(f"❌ {image['name']} 下载失败: {str(e)}")

print(f"\n✅ 所有图片下载完成！")
print(f"输出目录: {output_dir}")
