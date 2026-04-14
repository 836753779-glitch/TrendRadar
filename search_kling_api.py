#!/usr/bin/env python3
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.runtime_ctx.context import new_context

ctx = new_context(method="search.kling_o3_api")
client = SearchClient(ctx=ctx)

# 搜索 Kling O3 API 文档
print("正在搜索 Kling O3 API 文档...")
response = client.web_search(
    query="Kling O3 API 文档 快手可灵视频生成接口",
    count=5,
    need_summary=True
)

print("\n" + "=" * 60)
print("AI 摘要:")
print("=" * 60)
print(response.summary)

print("\n" + "=" * 60)
print("搜索结果:")
print("=" * 60)

for i, item in enumerate(response.web_items, 1):
    print(f"\n{i}. {item.title}")
    print(f"   来源: {item.site_name}")
    print(f"   URL: {item.url}")
    if item.snippet:
        print(f"   摘要: {item.snippet[:200]}...")
