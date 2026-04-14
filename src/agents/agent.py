import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

# 导入工具
from tools.video_generation_tool import text_to_video
from tools.image_to_video_tool import image_to_video
from tools.video_with_character_tool import text_to_video_with_character
from tools.kling_video_tool import kling_text_to_video
from tools.kling_cli_tool import (
    kling_cli_text_to_video,
    kling_cli_image_to_video,
    kling_cli_create_subject,
    kling_cli_list_subjects,
    kling_cli_account_info
)
from tools.kling_element_tool import kling_cli_text_to_video_with_element
from tools.video_edit_tool import concat_videos, trim_video

# 导入语音合成和视频合成工具
from tools.tts_tool import text_to_speech, batch_text_to_speech
from tools.video_audio_tool import compile_video_audio, extract_video_audio
from tools.subtitle_tool import (
    generate_subtitle_from_audio,
    add_subtitles_to_video,
    auto_subtitle_pipeline
)
from tools.complete_video_tool import (
    generate_complete_video,
    batch_generate_videos
)
from tools.long_video_tool import generate_long_video
from tools.feishu_notification_tool import (
    send_feishu_text_message,
    send_feishu_video_notification,
    send_feishu_card_notification,
    send_feishu_batch_notification
)
from tools.prompt_optimizer_tool import (
    optimize_prompt_for_speaking,
    create_narration_prompt,
    analyze_script_for_actions
)
from tools.video_upload_tool import (
    upload_video_to_storage,
    upload_and_notify_feishu
)
from tools.video_prompt_smart import (
    optimize_video_prompt_with_llm,
    generate_video_prompt_smart
)
from tools.video_advanced_generation import (
    generate_video_with_both_frames,
    generate_video_fixed_camera
)

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:] # type: ignore

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=[
            # 完整视频生成（推荐）
            generate_complete_video,
            batch_generate_videos,
            generate_long_video,

            # 语音合成
            text_to_speech,
            batch_text_to_speech,

            # 视频音频合成
            compile_video_audio,
            extract_video_audio,

            # 字幕生成
            generate_subtitle_from_audio,
            add_subtitles_to_video,
            auto_subtitle_pipeline,

            # 视频生成（原有）
            text_to_video,
            text_to_video_with_character,
            kling_text_to_video,
            # Kling O3 角色主体生成（人物一致性最佳方案）
            kling_cli_text_to_video_with_element,
            kling_cli_text_to_video,
            kling_cli_image_to_video,
            kling_cli_create_subject,
            kling_cli_list_subjects,
            kling_cli_account_info,
            image_to_video,
            concat_videos,
            trim_video,

            # 飞书消息推送
            send_feishu_text_message,
            send_feishu_video_notification,
            send_feishu_card_notification,
            send_feishu_batch_notification,

            # 提示词优化工具（口型同步）
            optimize_prompt_for_speaking,
            create_narration_prompt,
            analyze_script_for_actions,

            # LLM 智能视频提示词优化（使用大模型解决物理错误、口型同步、画面诡异等问题）
            optimize_video_prompt_with_llm,
            generate_video_prompt_smart,

            # 高级视频生成（使用首帧+尾帧、固定镜头等专业技术）
            generate_video_with_both_frames,
            generate_video_fixed_camera,

            # 视频上传到对象存储
            upload_video_to_storage,
            upload_and_notify_feishu
        ],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
