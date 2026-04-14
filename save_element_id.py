#!/usr/bin/env python3
"""
保存角色ID到配置文件
"""
import json

# 角色ID
ELEMENT_ID = "308110838358255"

# 更新角色配置文件
character_config = {
    "element_id": ELEMENT_ID,
    "name": "香道文化传播者",
    "description": "温婉的东方女性，40-50岁，中式服装，低发髻，面带微笑",
    "reference_images": [
        "./assets/character_reference/character_multi_angle_1.png",
        "./assets/character_reference/character_multi_angle_2.png",
        "./assets/character_reference/character_multi_angle_3.png"
    ],
    "created_at": "2026-04-14"
}

# 保存到文件
with open('assets/character_element.json', 'w', encoding='utf-8') as f:
    json.dump(character_config, f, ensure_ascii=False, indent=2)

print(f"✅ 角色主体已保存到配置文件")
print(f"角色 ID: {ELEMENT_ID}")
print(f"配置文件: assets/character_element.json")
