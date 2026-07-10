# Agnes Media Skill 部署手册

> 部署日期：2026-07-10
> 部署环境：Linux (Hermes Agent, Profile: user001)
> 源路径：`/home/alan/sources/agnes-media-skill`
> 当前版本：1.6.0

---

## 目录

1. [概述](#1-概述)
2. [前提条件](#2-前提条件)
3. [部署步骤详解](#3-部署步骤详解)
4. [配置文件](#4-配置文件)
5. [环境变量](#5-环境变量)
6. [验证清单](#6-验证清单)
7. [使用说明](#7-使用说明)
8. [故障排查](#8-故障排查)
9. [维护与更新](#9-维护与更新)

---

## 1. 概述

**Agnes Media Skill** 是一个 Hermes Agent 插件 + 技能包，通过 Agnes AI API 提供图像和视频生成能力。

### 功能

| 工具名称 | 功能 | 底层模型 |
|----------|------|---------|
| `generate_image_via_pic01` | 文生图 / 图生图 / 多图合成 | `agnes-image-2.0-flash` |
| `generate_video_via_mov01` | 文生视频 / 图生视频 / 关键帧动画 | `agnes-video-v2.0` |

### 项目目录规范

生成的文件按以下结构保存：

```
~/workspace/
└── <project_name>/
    ├── sources/          ← 输入素材：参考图片、源文件
    └── target/           ← 输出结果：生成的媒体文件
        ├── images/       ← 图片输出
        └── videos/       ← 视频输出
```

所有媒体工具自动输出到 `target/images/` 或 `target/videos/`。

### 架构

```
agnes-media-skill/
├── plugins/agnes_router/     ← Hermes Agent 插件（核心代码，提供工具处理器）
├── skills/creative/agnes-media/  ← 技能文档 + 辅助脚本 + API 参考
├── skills/media/agnes-video-async-monitor/  ← 异步视频轮询技能
└── examples/                 ← 示例配置和使用
```

> **说明：** 插件 (Plugin) 提供实际的工具调用能力，技能 (Skill) 提供使用指导和最佳实践。
> 两者配合使用才能发挥完整功能。

---

## 2. 前提条件

### 2.1 系统要求

| 项目 | 要求 | 当前状态 |
|------|------|---------|
| Python | >= 3.9 | 3.12.3 ✓ |
| Hermes Agent | 任意支持插件和技能的版本 | 已安装 ✓ |
| 操作系统 | Linux / macOS / Windows | Linux ✓ |

### 2.2 前置依赖

1. **Agnes AI API Key** — 必须提前获取
   - 来源：https://apihub.agnes-ai.com
   - 需要注册 Agnes AI 账户并创建 API Key

2. **工作区目录** — 默认 `~/workspace`（首次使用时自动创建）
   - 也可通过 `AGNES_WORKSPACE_ROOT` 环境变量自定义

### 2.3 源文件

部署所需源文件均位于：

```
/home/alan/sources/agnes-media-skill/
```

如果尚未克隆：

```bash
git clone <repository-url> /home/alan/sources/agnes-media-skill
```

---

## 3. 部署步骤详解

### 步骤 1：复制插件 (Plugin)

> **作用：** 将工具处理器注册到 Hermes Agent，使其可被调用。

```bash
# 确保插件目录存在
mkdir -p ~/.hermes/profiles/user001/plugins/

# 复制插件
cp -r /home/alan/sources/agnes-media-skill/plugins/agnes_router \
      ~/.hermes/profiles/user001/plugins/agnes_router
```

**复制后的文件清单：**

| 文件 | 大小 | 说明 |
|------|------|------|
| `__init__.py` | 506 B | 工具注册入口，注册 `generate_image_via_pic01` 和 `generate_video_via_mov01` |
| `plugin.yaml` | 1,585 B | 插件清单，定义可配置参数和所需环境变量 |
| `schemas.py` | ~4.4 KB | 工具参数 Schema — 含 image/video 全部参数 |
| `tools.py` | ~11 KB | 核心逻辑：API 调用、重试机制、扩展参数传递 |
| `workspace_manager.py` | 3,261 B | 路径验证 + 安全隔离（防目录穿越攻击） |

### 步骤 2：复制技能 (Skill)

> **作用：** 提供使用文档、辅助脚本和最佳实践指南。

```bash
# 确保技能分类目录存在
mkdir -p ~/.hermes/profiles/user001/skills/creative/
mkdir -p ~/.hermes/profiles/user001/skills/media/

# 复制主技能（文档 + 脚本）
cp -r /home/alan/sources/agnes-media-skill/skills/creative/agnes-media \
      ~/.hermes/profiles/user001/skills/creative/agnes-media

# 复制异步视频监控技能（后台进程轮询工作流）
cp -r /home/alan/sources/agnes-media-skill/skills/media/agnes-video-async-monitor \
      ~/.hermes/profiles/user001/skills/media/agnes-video-async-monitor
```

**主技能文件清单 `skills/creative/agnes-media/`：**

| 文件 | 大小 | 说明 |
|------|------|------|
| `SKILL.md` | ~26 KB | 技能使用文档（主文档，v1.6.0） |
| `references/image-api-guide.md` | 4.4 KB | 图像 API 参考：图生图、多图合成、队列重试、Data URI |
| `references/video-async-guide.md` | 6,294 B | 异步视频工作流指南 |
| `references/deployment-workflow.md` | — | 源码到部署的同步工作流 |
| `references/png-metadata-extraction.md` | 3,228 B | 从 PNG 提取内嵌的提示词元数据 |
| `scripts/check_task.py` | 4,379 B | 视频任务状态查询 CLI 工具 |
| `scripts/to_data_uri.py` | — | 本地图片 → Data URI 转换工具 |
| `templates/image-queue-retry.py` | — | 图像 503 队列重试示例脚本 |

# 异步视频监控技能 `skills/media/agnes-video-async-monitor/`：

| 文件 | 大小 | 说明 |
|------|------|------|
| `SKILL.md` | ~3 KB | 后台进程轮询检查视频任务状态的工作流 |
| `scripts/monitor_video.py` | 2.6 KB | 通用视频监控脚本（30s轮询，自动下载） |
| `scripts/monitor_keyframe.py` | 2.9 KB | 关键帧专用监控脚本 |
| `references/video-api-fields.md` | 3.9 KB | API 响应字段文档 + 大 payload 注意事项 |

### 步骤 3：配置 config.yaml

> **作用：** 启用插件并配置各项参数。

使用 Hermes CLI 命令配置：

```bash
# 启用插件
hermes config set plugins.enabled '["agnes_router"]'

# 配置工作区根目录
hermes config set plugins.entries.agnes_router.workspace_root '~/workspace'

# 配置模型
hermes config set plugins.entries.agnes_router.image_model 'agnes-image-2.0-flash'
hermes config set plugins.entries.agnes_router.video_model 'agnes-video-v2.0'

# 配置超时时间（秒）
hermes config set plugins.entries.agnes_router.image_timeout 180
hermes config set plugins.entries.agnes_router.video_timeout 300
hermes config set plugins.entries.agnes_router.download_timeout 300

# 配置重试策略（图像队列 503 需要 30s 延迟 × 10+ 次）
hermes config set plugins.entries.agnes_router.max_retries 10
hermes config set plugins.entries.agnes_router.retry_delay 30.0
```

> **注意：** 默认 `max_retries=10`、`retry_delay=30.0` 是针对图像 API 频繁返回
> 503 queue full 的优化值。视频重试仍使用较短的内部超时。

**结果（config.yaml 中生成的配置段）：**

```yaml
plugins:
  enabled:
    - agnes_router
  entries:
    agnes_router:
      workspace_root: ~/workspace
      image_model: agnes-image-2.0-flash
      video_model: agnes-video-v2.0
      image_timeout: 180
      video_timeout: 300
      download_timeout: 300
      max_retries: 10
      retry_delay: 30.0
```

> **注意：** `plugins.enabled` 必须是 YAML 列表格式 `[- agnes_router]`，而不是字符串 `'["agnes_router"]'`。

### 步骤 4：配置 API Key

> **作用：** 插件通过此密钥认证并调用 Agnes AI API。

将 API Key 添加到 profile 的环境变量文件：

```bash
echo 'AGNES_API_KEY=sk-你的密钥' >> ~/.hermes/profiles/user001/.env
```

也可通过 shell 环境变量设置：

```bash
export AGNES_API_KEY='sk-你的密钥'
```

**API Key 加载优先级：**
1. `AGNES_API_KEY` 环境变量
2. `API_KEY` 环境变量（后备）

### 步骤 5：验证部署

```bash
# 验证插件文件完整性
ls -la ~/.hermes/profiles/user001/plugins/agnes_router/

# 验证技能文件完整性
find ~/.hermes/profiles/user001/skills/creative/agnes-media -type f
find ~/.hermes/profiles/user001/skills/media/agnes-video-async-monitor -type f

# 验证配置正确性
hermes config check

# 验证 API Key 已配置
printenv AGNES_API_KEY
```

### 步骤 6：重启 Hermes Agent

插件在 Hermes Agent 启动时加载。重启生效：

```bash
# CLI 模式：退出后重新运行
exit
hermes

# 或如果使用网关
hermes gateway restart
```

---

## 4. 配置文件

### 4.1 最终配置文件 (config.yaml)

配置文件路径：`~/.hermes/profiles/user001/config.yaml`

```yaml
plugins:
  enabled:
    - agnes_router
  entries:
    agnes_router:
      workspace_root: ~/workspace
      image_model: agnes-image-2.0-flash
      video_model: agnes-video-v2.0
      image_timeout: 180
      video_timeout: 300
      download_timeout: 300
      max_retries: 10
      retry_delay: 30.0
```

### 4.2 完整参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `workspace_root` | 路径 | `~/workspace` | 媒体文件输出根目录 |
| `image_endpoint` | URL | `https://apihub.agnes-ai.com/v1/images/generations` | 图像 API 端点 |
| `video_endpoint` | URL | `https://apihub.agnes-ai.com/v1/videos` | 视频 API 端点 |
| `image_model` | 字符串 | `agnes-image-2.0-flash` | 图像生成模型 |
| `video_model` | 字符串 | `agnes-video-v2.0` | 视频生成模型 |
| `image_timeout` | 整数 | 180 | 图像请求超时（秒） |
| `video_timeout` | 整数 | 300 | 视频提交超时（秒） |
| `download_timeout` | 整数 | 300 | 下载超时（秒） |
| `max_retries` | 整数 | **10** | 最大重试次数（图像 10+，视频 2） |
| `retry_delay` | 浮点数 | **30.0** | 重试间隔（秒）（图像 30s，视频 3s） |
| `allowed_subdirs` | 列表 | `[images, videos]` | 允许的子目录 |

所有参数均可在 plugin.yaml 中定义默认值，可通过 config.yaml 覆盖，
也可通过同名环境变量（大写、以 `AGNES_` 为前缀）覆盖。

---

## 5. 环境变量

### 5.1 环境变量文件

路径：`~/.hermes/profiles/user001/.env`

```bash
AGNES_API_KEY=sk-...      # 必填：Agnes AI API Key
```

### 5.2 完整环境变量列表

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `AGNES_API_KEY` | **是** | — | Agnes AI API 密钥 |
| `AGNES_IMAGE_MODEL` | 否 | `agnes-image-2.0-flash` | 图像生成模型 |
| `AGNES_VIDEO_MODEL` | 否 | `agnes-video-v2.0` | 视频生成模型 |
| `AGNES_IMAGE_ENDPOINT` | 否 | `https://apihub.agnes-ai.com/v1/images/generations` | 图像 API 端点 |
| `AGNES_VIDEO_ENDPOINT` | 否 | `https://apihub.agnes-ai.com/v1/videos` | 视频 API 端点 |
| `AGNES_WORKSPACE_ROOT` | 否 | `~/workspace` | 媒体输出根目录 |
| `AGNES_IMAGE_TIMEOUT` | 否 | `180` | 图像超时（秒） |
| `AGNES_VIDEO_TIMEOUT` | 否 | `300` | 视频超时（秒） |
| `AGNES_DOWNLOAD_TIMEOUT` | 否 | `300` | 下载超时（秒） |
| `AGNES_MAX_RETRIES` | 否 | **10** | 最大重试次数（图像 10+，视频 2） |
| `AGNES_RETRY_DELAY` | 否 | **30.0** | 重试间隔（秒）（图像 30s，视频 3s） |

---

## 6. 验证清单

### 6.1 文件部署验证

| 检查项 | 路径 | 状态 |
|--------|------|------|
| 插件目录 | `~/.hermes/profiles/user001/plugins/agnes_router/` | ✓ |
| 插件入口 | `plugins/agnes_router/__init__.py` | ✓ |
| 插件清单 | `plugins/agnes_router/plugin.yaml` | ✓ |
| 工具 Schema | `plugins/agnes_router/schemas.py` | ✓ |
| 工具处理器 | `plugins/agnes_router/tools.py` | ✓ |
| 工作区管理 | `plugins/agnes_router/workspace_manager.py` | ✓ |
| 技能目录 (creative) | `~/.hermes/profiles/user001/skills/creative/agnes-media/` | ✓ |
| 技能文档 (creative) | `skills/creative/agnes-media/SKILL.md` | ✓ |
| 图像 API 参考 | `skills/creative/agnes-media/references/image-api-guide.md` | ✓ |
| 异步视频指南 | `skills/creative/agnes-media/references/video-async-guide.md` | ✓ |
| 部署工作流 | `skills/creative/agnes-media/references/deployment-workflow.md` | ✓ |
| PNG 元数据提取 | `skills/creative/agnes-media/references/png-metadata-extraction.md` | ✓ |
| 任务检查脚本 | `skills/creative/agnes-media/scripts/check_task.py` | ✓ |
| Data URI 脚本 | `skills/creative/agnes-media/scripts/to_data_uri.py` | ✓ |
| 队列重试模板 | `skills/creative/agnes-media/templates/image-queue-retry.py` | ✓ |
| 技能目录 (media) | `~/.hermes/profiles/user001/skills/media/agnes-video-async-monitor/` | ✓ |
| 视频轮询技能 | `skills/media/agnes-video-async-monitor/SKILL.md` | ✓ |

### 6.2 配置验证

| 检查项 | 当前值 | 状态 |
|--------|--------|------|
| 插件已启用 | `agnes_router` | ✓ |
| 工作区根目录 | `~/workspace` | ✓ |
| 图像模型 | `agnes-image-2.0-flash` | ✓ |
| 视频模型 | `agnes-video-v2.0` | ✓ |
| 图像超时 | 180s | ✓ |
| 视频超时 | 300s | ✓ |
| 下载超时 | 300s | ✓ |
| 最大重试 | 10 | ✓ |
| 重试延迟 | 30.0s | ✓ |

### 6.3 环境验证

| 检查项 | 状态 |
|--------|------|
| `AGNES_API_KEY` 已设置 | ✓ |
| `.env` 文件存在 | ✓ |

---

## 7. 使用说明

### 7.1 文生图

```python
generate_image_via_pic01(
    project_name="my_project",
    prompt="蓝天下的一只橘猫，阳光明媚",
    file_name="cat.png",
    size="1024x1024"
)
```

### 7.2 图生图

```python
generate_image_via_pic01(
    project_name="my_project",
    prompt="把背景换成未来城市夜景，保持人物面部和服装不变",
    file_name="edited.png",
    image=["https://example.com/input-photo.jpg"]
)
```

### 7.3 多图合成

```python
generate_image_via_pic01(
    project_name="my_project",
    prompt="将两张图片中的人物放在一个电影级科幻战斗场景中",
    file_name="composite.png",
    image=[
        "https://example.com/character1.jpg",
        "https://example.com/character2.jpg"
    ]
)
```

### 7.4 视频生成

```python
generate_video_via_mov01(
    project_name="my_project",
    prompt="产品展示：陶瓷咖啡杯360度旋转",
    file_name="intro.mp4",
    width=1152,
    height=768,
    num_frames=121,
    frame_rate=24
)
```

> **注意：** 视频生成是异步的。使用 `check_task.py` 轮询完成状态。
> 用 `video_id` 查，不要用 `task_id`。

### 7.5 图生视频

```python
generate_video_via_mov01(
    project_name="my_project",
    prompt="猫开始滑滑板，做特技动作",
    file_name="skate_cat.mp4",
    mode="ti2vid",
    image="https://example.com/cat.jpg",
    width=1152,
    height=768,
    num_frames=121,
    frame_rate=24
)
```

### 7.6 检查视频任务状态

```bash
python3 scripts/check_task.py video_d39354f7bafe484cac4c58481d91c171
python3 scripts/check_task.py "video_bGl0ZWxsbTpjdXN0b21fbGxtX3Byb3ZpZGVy..."
```

### 7.7 Cron 定时检查

```yaml
schedule: "2m"
prompt: |
  检查 ~/workspace/my_project/target/videos/intro.mp4 是否存在且大于 1000 bytes。
skills:
  - agnes-media
```

---

## 8. 故障排查

### 8.1 常见错误

| 错误信息 | 可能原因 | 解决方案 |
|----------|----------|----------|
| `"无效的令牌"` | API Key 错误 | 检查 `AGNES_API_KEY` |
| `security_blocked` | 文件名含非法字符 | 使用纯 ASCII |
| HTTP 503 | 图像队列满 | 30s 间隔重试 10+ 次 |
| `response_format` 报错 | 参数放顶层了 | 必须用 `extra_body.response_format` |
| 视频状态始终 `queued` | 查错 endpoint | 用 `/agnesapi?video_id=` 而非 `/v1/videos/{task_id}` |

### 8.2 重启后不生效

1. `ls ~/.hermes/.../plugins/agnes_router/` 检查插件目录
2. `hermes config check` 检查配置
3. `printenv AGNES_API_KEY` 检查 API Key
4. 重启 Hermes Agent

---

## 9. 维护与更新

### 更新插件

```bash
cp -r /home/alan/sources/agnes-media-skill/plugins/agnes_router/* \
      ~/.hermes/profiles/user001/plugins/agnes_router/
# 重启 Hermes Agent
```

### 更新技能

```bash
# 主技能
cp -r /home/alan/sources/agnes-media-skill/skills/creative/agnes-media/* \
      ~/.hermes/profiles/user001/skills/creative/agnes-media/

# 异步视频监控技能
cp -r /home/alan/sources/agnes-media-skill/skills/media/agnes-video-async-monitor/* \
      ~/.hermes/profiles/user001/skills/media/agnes-video-async-monitor/

# 无需重启，`skill agnes-media` 或新会话即可生效
```

### 卸载

```bash
rm -rf ~/.hermes/profiles/user001/plugins/agnes_router/
hermes config set plugins.enabled '[]'
rm -rf ~/.hermes/profiles/user001/skills/creative/agnes-media/
rm -rf ~/.hermes/profiles/user001/skills/media/agnes-video-async-monitor/
```

---

## 附录：文件清单

| 文件 | 说明 |
|------|------|
| `plugins/agnes_router/__init__.py` | 506 B — 工具注册 |
| `plugins/agnes_router/plugin.yaml` | 1,585 B — 插件清单 |
| `plugins/agnes_router/schemas.py` | ~4.4 KB — 完整参数 Schema |
| `plugins/agnes_router/tools.py` | ~11 KB — API 核心逻辑 + 扩展参数 |
| `plugins/agnes_router/workspace_manager.py` | 3,261 B — 安全隔离 |
| `skills/creative/agnes-media/SKILL.md` | ~26 KB — 技能文档 v1.6.0 |
| `skills/media/agnes-video-async-monitor/scripts/monitor_video.py` | 2.6 KB — 通用视频监控脚本 |
| `skills/media/agnes-video-async-monitor/scripts/monitor_keyframe.py` | 2.9 KB — 关键帧监控脚本 |
| `skills/media/agnes-video-async-monitor/references/video-api-fields.md` | 3.9 KB — API 字段文档 |
| `skills/creative/agnes-media/templates/image-queue-retry.py` | 图像 503 队列重试示例 |
| `skills/media/agnes-video-async-monitor/SKILL.md` | ~3 KB — 异步视频轮询技能 |
| `skills/creative/agnes-media/references/image-api-guide.md` | 4.4 KB — 图像 API 参考 |
| `skills/creative/agnes-media/references/video-async-guide.md` | 6,294 B — 异步视频工作流指南 |
| `skills/creative/agnes-media/references/deployment-workflow.md` | — 源码到部署的同步工作流 |
| `skills/creative/agnes-media/references/png-metadata-extraction.md` | 3,228 B — PNG 提示词元数据提取 |
| `skills/creative/agnes-media/scripts/check_task.py` | 4,379 B — 视频任务状态查询 |
| `skills/creative/agnes-media/scripts/to_data_uri.py` | — 本地图片 → Data URI 转换 |
| `skills/creative/agnes-media/templates/image-queue-retry.py` | — 图像 503 队列重试示例 |

---

*源路径：`/home/alan/sources/agnes-media-skill/`*