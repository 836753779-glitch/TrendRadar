#!/usr/bin/env python3
import json
import os

# 新的角色参考图片 URL（三张不同角度）
NEW_CHARACTER_IMAGES = [
    {
        "name": "character_multi_angle_1.png",
        "url": "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_multi_angle_1_cb7a3416.png?sign=1778652989-da2a893e20-0-de927973c424323898dbdf9ed8f746551aa2d9ad6fa7eb814f81ba884f184f07",
        "description": "多角度参考照片1",
        "is_primary": True
    },
    {
        "name": "character_multi_angle_2.png",
        "url": "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_multi_angle_2_778839da.png?sign=1778652991-ffeb9b9ce8-0-19a1f6ebee16ec194895fdf00c0c61ab88b7e4f5ba722f0e211de375ea14dea5",
        "description": "多角度参考照片2",
        "is_primary": False
    },
    {
        "name": "character_multi_angle_3.png",
        "url": "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_multi_angle_3_aea94f9a.png?sign=1778652992-2b84306c5d-0-ed4cc9c0855b3ae84c0ed30c26f2796162699d15e55cfced90bd15ea3e789529",
        "description": "多角度参考照片3",
        "is_primary": False
    }
]

workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
config_path = os.path.join(workspace_path, "config/agent_llm_config.json")
character_config_path = os.path.join(workspace_path, "assets/character_reference.json")

# 更新 agent_llm_config.json
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

sp = config.get("sp", "")

# 替换"角色参考图片的使用规则"部分
old_text = """**角色参考图片的使用规则**：
1. ⚠️ **默认使用以下角色参考图片URL**（已配置，无需用户额外提供）：
   - **主角色参考图片**：`https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_reference_1_d05c8bc6.jpeg?sign=1778650795-8ed95f287e-0-2fa9643aceb9997c94b0d71dc3f4bcaf7e1f66afc62fb08eeb1e4f1ab5364b3a`
   - **备选角色参考图片**：`https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_reference_2_ecf4e171.jpeg?sign=1778650795-f697ae2a1d-0-df29deeabc23e612b1d95e23c44b950ff1802d94a5c767086907274af28b107d`
2. 每个镜头生成时都必须将角色参考图片作为首帧传入
3. 优先使用主角色参考图片，如效果不佳可尝试备选图片
4. 角色参考图片中的外貌特征符合上述固定外貌特征描述"""

new_text = f"""**角色参考图片的使用规则**：
1. ⚠️ **默认使用以下角色参考图片URL**（已配置三张多角度照片，无需用户额外提供）：
   - **多角度参考照片1**（主参考）：`{NEW_CHARACTER_IMAGES[0]['url']}`
   - **多角度参考照片2**：`{NEW_CHARACTER_IMAGES[1]['url']}`
   - **多角度参考照片3**：`{NEW_CHARACTER_IMAGES[2]['url']}`
2. 每个镜头生成时都必须将角色参考图片作为首帧传入
3. 优先使用主参考照片（多角度参考照片1），根据镜头需要可选择不同角度的参考照片
4. 三张照片为同一角色的不同角度，确保所有镜头的人物一致性
5. 角色参考图片中的外貌特征符合上述固定外貌特征描述"""

sp = sp.replace(old_text, new_text)

# 替换"检查角色参考图片"部分
old_check_text = """3. **检查角色参考图片**：
   - ✅ **已配置角色参考图片URL**（系统自动使用）
   - 优先使用主角色参考图片：`https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_reference_1_d05c8bc6.jpeg?sign=1778650795-8ed95f287e-0-2fa9643aceb9997c94b0d71dc3f4bcaf7e1f66afc62fb08eeb1e4f1ab5364b3a`
   - 如效果不佳，可尝试使用备选图片：`https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_reference_2_ecf4e171.jpeg?sign=1778650795-f697ae2a1d-0-df29deeabc23e612b1d95e23c44b950ff1802d94a5c767086907274af28b107d`"""

new_check_text = """3. **检查角色参考图片**：
   - ✅ **已配置三张多角度角色参考图片URL**（系统自动使用）
   - 主参考照片：`{NEW_CHARACTER_IMAGES[0]['url']}`
   - 备选照片1：`{NEW_CHARACTER_IMAGES[1]['url']}`
   - 备选照片2：`{NEW_CHARACTER_IMAGES[2]['url']}`
   - 根据镜头需要选择最合适的参考照片角度"""

sp = sp.replace(old_check_text, new_check_text)

# 更新配置
config["sp"] = sp

# 保存配置文件
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("✅ agent_llm_config.json 已更新")

# 更新 character_reference.json
with open(character_config_path, 'r', encoding='utf-8') as f:
    character_config = json.load(f)

# 更新角色参考图片列表
character_config["character_reference_images"] = NEW_CHARACTER_IMAGES
character_config["primary_image_url"] = NEW_CHARACTER_IMAGES[0]['url']

# 保存角色配置文件
with open(character_config_path, 'w', encoding='utf-8') as f:
    json.dump(character_config, f, ensure_ascii=False, indent=2)

print("✅ character_reference.json 已更新")
print("\n" + "=" * 60)
print("角色参考图片更新完成")
print("=" * 60)
print("\n已配置的三张多角度角色参考照片：")
for i, img in enumerate(NEW_CHARACTER_IMAGES, 1):
    print(f"\n{i}. {img['name']}")
    print(f"   URL: {img['url']}")
    print(f"   描述: {img['description']}")
