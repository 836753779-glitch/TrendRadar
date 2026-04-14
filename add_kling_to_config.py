#!/usr/bin/env python3
import json
import os

workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
config_path = os.path.join(workspace_path, "config/agent_llm_config.json")

# 读取配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

sp = config.get("sp", "")

# 在视频生成工具部分添加 Kling O3
old_tools_section = "### text_to_video_with_character（首选，人物类视频必须使用）"
new_tools_section = """### kling_text_to_video（快手 Kling O3，高质量视频生成）
- **用途**：使用快手 Kling O3 模型和角色参考图片生成高质量视频
- **优势**：快手出品，电影级画质，优秀的人物一致性
- **适用场景**：追求最高质量的视频生成、电影级效果
- **必填参数**：
  - `prompt`: 文本描述
  - `character_image_url`: 角色参考图片URL
- **可选参数**：resolution, ratio, duration
- **使用规则**：⚠️ **需要配置 Kling API 密钥**

### text_to_video_with_character（Seedance，人物类视频推荐）"""

sp = sp.replace(old_tools_section, new_tools_section)

# 在当前可用模型部分添加 Kling O3
old_models_section = "### text_to_video_with_character（首选，人物类视频必须使用）"

# 添加一个新的章节说明 Kling O3
kling_info = """

## Kling O3（快手可灵）- 新增

**Kling O3** 是快手 Kling AI 出品的高质量视频生成模型，支持电影级画质和优秀的人物一致性。

### 模型特点
- **提供商**：快手 Kling AI
- **模型ID**：kling-3.0
- **工具名称**：kling_text_to_video
- **优势**：电影级画质、人物一致性好、生成速度快
- **状态**：✅ 已配置 API 密钥

### 使用方式
- 工具：`kling_text_to_video`
- 必填参数：prompt, character_image_url
- 可选参数：resolution (720p/1080p), ratio (9:16/16:9), duration (5-10秒)

### API 配置
- **Access Key**: AFRYabFrgBmh3nybnYkd9LNJtd4FBFQf
- **Secret Key**: ECQfkNk3narb39fyAyR9A8dtTrrgLrEr
- **API Endpoint**: https://api.klingai.com/v1/videos/text2video

"""

# 在"# 当前可用模型"章节之前插入 Kling O3 信息
sp = sp.replace("# 当前可用模型", kling_info + "\n# 当前可用模型")

# 更新配置
config["sp"] = sp

# 更新 tools 列表
tools_list = config.get("tools", [])
if "kling_text_to_video" not in tools_list:
    tools_list.insert(0, "kling_text_to_video")  # 添加到第一个位置
    config["tools"] = tools_list

# 保存配置文件
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("✅ 配置文件已更新")
print("✅ 已添加 Kling O3 模型到可用工具列表")
print("✅ API 密钥已配置")
