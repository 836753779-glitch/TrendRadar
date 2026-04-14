# 心跳机制使用说明

## 功能概述

心跳机制用于监控视频生成任务的运行状态，定期发送心跳通知到飞书，确保长时间任务能够被实时监控，及时发现任务超时或异常。

## 可用工具

### 1. `start_heartbeat` - 启动心跳监控

启动心跳监控机制，开始定期发送心跳通知。

**参数：**
- `task_name`（必填）：任务名称（如"视频生成任务"）
- `interval`（可选）：心跳间隔时间（秒），默认60秒
- `max_duration`（可选）：最大监控时长（秒），超过则自动停止并报警，None表示不限制

**示例：**
```python
start_heartbeat(
    task_name="沉香视频生成",
    interval=60,
    max_duration=600  # 10分钟后自动报警
)
```

**返回：**
```
✅ 心跳机制已启动
任务名称：沉香视频生成
心跳间隔：60秒
最大监控时长：600秒
```

---

### 2. `send_heartbeat` - 发送一次心跳

手动发送一次心跳通知到飞书。

**参数：**
- `message`（可选）：附加消息
- `task_status`（可选）：任务状态（running/progress/completed/failed）

**示例：**
```python
# 发送常规心跳
send_heartbeat()

# 发送进度更新
send_heartbeat(
    message="视频生成进度：50%",
    task_status="progress"
)

# 发送完成通知
send_heartbeat(
    message="视频生成成功",
    task_status="completed"
)
```

**返回：**
```
✅ 心跳已发送（第5次）
```

---

### 3. `stop_heartbeat` - 停止心跳监控

停止心跳监控机制，并发送最终状态通知。

**参数：**
- `final_status`（可选）：最终状态（completed/failed）
- `final_message`（可选）：最终消息

**示例：**
```python
# 任务完成
stop_heartbeat(
    final_status="completed",
    final_message="视频生成成功，时长60秒"
)

# 任务失败
stop_heartbeat(
    final_status="failed",
    final_message="视频生成失败，提示词超长"
)
```

**返回：**
```
✅ 心跳机制已停止

任务名称：沉香视频生成
最终状态：completed
总运行时间：0:03:45
总心跳次数：4
```

---

### 4. `check_heartbeat_status` - 检查心跳状态

检查当前心跳机制的运行状态。

**参数：** 无

**示例：**
```python
check_heartbeat_status()
```

**返回：**
```
📊 **心跳机制状态**

**运行状态**：🟢 运行中
**任务名称**：沉香视频生成
**启动时间**：2026-04-14 20:00:29
**运行时长**：0:02:15
**心跳间隔**：60秒
**总心跳次数**：2
**上次心跳**：0:00:15前
```

---

### 5. `monitor_video_generation` - 监控视频生成（一键启动）

专门用于监控视频生成任务的一键启动工具。

**参数：**
- `task_name`（必填）：任务名称
- `interval`（可选）：心跳间隔（秒），默认60秒
- `max_duration`（可选）：最大监控时长（秒），默认600秒（10分钟）

**示例：**
```python
monitor_video_generation(
    task_name="沉香视频生成",
    interval=60,
    max_duration=600
)
```

---

## 完整使用流程

### 场景：生成长视频

```python
# 1. 启动心跳监控
start_heartbeat(
    task_name="沉香产品视频生成",
    interval=60,
    max_duration=600
)

# 2. 生成测试视频（3-5秒）
test_video = generate_test_video(
    prompt="...",
    narration_text="..."
)
# Agent会自动发送心跳通知

# 3. 推送测试视频到飞书，等待用户确认
upload_and_notify_feishu(test_video_url, "测试视频已生成，请确认")

# 4. 用户确认后，生成长视频
long_video = confirm_and_generate_long_video(
    test_video_id=xxx
)
# Agent会自动发送进度心跳

# 5. 停止心跳监控
stop_heartbeat(
    final_status="completed",
    final_message="视频生成成功，时长60秒"
)
```

---

## 心跳通知格式

### 常规心跳（running）
```
💓 **心跳通知**

**任务名称**：沉香视频生成
**任务状态**：running
**运行时间**：0:02:00
**心跳次数**：2
**当前时间**：2026-04-14 20:02:29
```

### 进度更新（progress）
```
🔄 **心跳通知**

**任务名称**：沉香视频生成
**任务状态**：progress
**运行时间**：0:03:00
**心跳次数**：3
**当前时间**：2026-04-14 20:03:29
**附加信息**：视频生成进度：50%
```

### 任务完成（completed）
```
✅ **任务完成通知**

**任务名称**：沉香视频生成
**最终状态**：completed
**总运行时间**：0:05:00
**总心跳次数**：5
**附加信息**：视频生成成功，时长60秒
```

### 任务失败（failed）
```
❌ **任务超时报警**

**任务名称**：沉香视频生成
**运行时长**：620秒
**最大监控时长**：600秒
**总心跳次数**：10
**报警信息**：任务已超过最大监控时长，可能存在异常！
```

---

## 重要提示

1. **心跳间隔建议**：
   - 短任务（<5分钟）：间隔30-60秒
   - 中等任务（5-15分钟）：间隔60-120秒
   - 长任务（>15分钟）：间隔120-300秒

2. **最大监控时长**：
   - 测试视频：建议300秒（5分钟）
   - 长视频：建议600-1200秒（10-20分钟）

3. **使用场景**：
   - ✅ 所有生成长视频的任务
   - ✅ 批量生成多个视频的任务
   - ❌ 短时间测试任务（<1分钟）

4. **注意事项**：
   - 心跳通知会自动发送到飞书群组
   - 超时会自动报警，但不会停止任务
   - 停止心跳时会发送最终状态通知
   - 心跳机制是独立的线程，不会阻塞主流程

---

## 与两阶段生产流程的配合

```python
# 阶段1：生成测试视频
monitor_video_generation(task_name="沉香视频生成")
test_video = generate_test_video(...)
upload_and_notify_feishu(...)

# 阶段2：等待用户确认
# Agent会自动发送心跳通知，显示任务正在等待

# 阶段3：生成长视频
long_video = confirm_and_generate_long_video(...)
# Agent会继续发送心跳通知

# 完成
stop_heartbeat(final_status="completed", final_message="视频生成完成")
```
