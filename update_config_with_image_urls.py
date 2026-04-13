#!/usr/bin/env python3
import json
import os

# 角色参考图片 URL
PRIMARY_IMAGE_URL = "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_reference_1_d05c8bc6.jpeg?sign=1778650795-8ed95f287e-0-2fa9643aceb9997c94b0d71dc3f4bcaf7e1f66afc62fb08eeb1e4f1ab5364b3a"
BACKUP_IMAGE_URL = "https://coze-coding-project.tos.coze.site/coze_storage_7628072355071262774/character_reference_2_ecf4e171.jpeg?sign=1778650795-f697ae2a1d-0-df29deeabc23e612b1d95e23c44b950ff1802d94a5c767086907274af28b107d"

workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
config_path = os.path.join(workspace_path, "config/agent_llm_config.json")

# 读取配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 替换角色参考图片相关内容
sp = config.get("sp", "")

# 替换"角色参考图片的使用规则"部分
old_text = """**角色参考图片的使用规则**：
1. 用户必须提供角色参考图片的URL（必须是公开访问的HTTP/HTTPS链接）
2. 每个镜头生成时都必须将角色参考图片作为首帧传入
3. 角色参考图片必须是清晰、正面、自然的照片
4. 角色参考图片中的外貌特征必须符合上述固定外貌特征描述"""

new_text = f"""**角色参考图片的使用规则**：
1. ⚠️ **默认使用以下角色参考图片URL**（已配置，无需用户额外提供）：
   - **主角色参考图片**：`{PRIMARY_IMAGE_URL}`
   - **备选角色参考图片**：`{BACKUP_IMAGE_URL}`
2. 每个镜头生成时都必须将角色参考图片作为首帧传入
3. 优先使用主角色参考图片，如效果不佳可尝试备选图片
4. 角色参考图片中的外貌特征符合上述固定外貌特征描述"""

sp = sp.replace(old_text, new_text)

# 替换"检查角色参考图片"部分
old_check_text = """3. **检查角色参考图片**：
   - ⚠️ **必须确认用户提供了角色参考图片URL**
   - 如果用户没有提供角色参考图片URL，必须要求用户提供
   - 角色参考图片URL必须是公开访问的HTTP/HTTPS链接"""

new_check_text = """3. **检查角色参考图片**：
   - ✅ **已配置角色参考图片URL**（系统自动使用）
   - 优先使用主角色参考图片：`{PRIMARY_IMAGE_URL}`
   - 如效果不佳，可尝试使用备选图片：`{BACKUP_IMAGE_URL}`"""

sp = sp.replace(old_check_text, new_check_text)

# 更新配置
config["sp"] = sp

# 保存配置文件
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("✅ 配置文件已更新")
print(f"✅ 主角色参考图片URL: {PRIMARY_IMAGE_URL}")
print(f"✅ 备选角色参考图片URL: {BACKUP_IMAGE_URL}")
