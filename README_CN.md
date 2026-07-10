# Agnes Media Skill

Hermes Agent 插件和技能包，用于 Agnes AI 媒体生成。提供安全、可配置的**文生图**、**图生图**、**多图合成**和**视频生成**工具，具备工作区隔离、自动重试和异步视频轮询机制。

## 快速开始

1. 克隆本仓库
2. 设置 `AGNES_API_KEY` 环境变量
3. 作为 Hermes Agent 插件或技能部署

## 项目结构

```
agnes-media-skill/
├── plugins/
│   └── agnes_router/           # Hermes Agent 插件（工具处理器）
│       ├── __init__.py         # 工具注册
│       ├── plugin.yaml         # 插件清单 + 可配置参数
│       ├── schemas.py          # 工具参数 Schema
│       ├── tools.py            # 图像/视频生成处理器
│       └── workspace_manager.py # 路径验证 + 安全校验
├── skills/
│   ├── creative/
│   │   └── agnes-media/        # Hermes Agent 技能（主）
│   │       ├── SKILL.md        # 技能文档
│   │       ├── scripts/
│   │       │   ├── check_task.py        # 视频任务状态检查器
│   │       │   └── to_data_uri.py       # 文件 → Data URI 转换
│   │       ├── templates/
│   │       │   └── image-queue-retry.py # 图像 503 重试示例
│       │       └── references/
│       │           ├── image-api-guide.md            # 图像 API 参考（图生图、多图合成、队列重试）
│       │           ├── video-async-guide.md          # 异步视频工作流指南
│       │           ├── deployment-workflow.md        # 源码到部署的同步工作流
│       │           └── png-metadata-extraction.md    # 从 PNG 提取内嵌的提示词元数据
│   └── media/
│       └── agnes-video-async-monitor/   # 异步视频轮询技能
│           └── SKILL.md                  # 后台进程轮询工作流
├── examples/                   # 示例提示词和配置
├── DEPLOYMENT_MANUAL.md        # 部署手册
├── README.md                   # 英文文档
├── README_CN.md                # 本文档
├── LICENSE
└── .gitignore
```

## 功能特性

- **三种图像生成模式** — 文生图、图生图、多图合成。支持 URL 和 Data URI 图片输入
- **三种视频生成模式** — 文生视频、图生视频 (ti2vid)、关键帧动画。可配置分辨率、帧数、帧率、种子和反向提示词
- **安全的工作区隔离** — 所有生成的文件保存在可配置的工作区根目录下，带有路径遍历保护
- **自动重试机制** — 瞬态错误（超时、503、限速）会自动重试，支持可配置延迟（图像队列 30s，通用错误 3s）
- **异步视频支持** — 正确处理视频生成的异步行为，后台进程每30秒轮询，完成自动下载通知
- **全环境变量可配置** — 每个参数（端点、超时时间、模型、工作区根目录）均可通过环境变量覆盖
- **Cron 安全** — 在定时任务中正常工作，自动处理 API key 提取。注意：视频轮询使用后台进程（非 cron），因 cron 最短循环间隔为30分钟。

## 项目目录规范

生成的媒体文件按以下目录结构保存。首次使用时自动创建完整的项目骨架：

```
~/workspace/
└── <project_name>/
    ├── sources/          ← 输入素材：参考图片、源文件
    │   ├── images/       ← 参考图片（如从聊天工具接收的）
    │   ├── videos/       ← 源视频文件
    │   ├── scripts/      ← 生成脚本
    │   └── others/       ← 其他输入文件（配置文件、请求 payload）
    └── target/           ← 输出结果：生成的媒体文件
        ├── images/       ← 图片输出（来自 generate_image_via_pic01）
        ├── videos/       ← 视频输出（来自 generate_video_via_mov01）
        ├── scripts/      ← 输出脚本、日志
        └── others/       ← 其他输出文件（URL 列表、元数据）
```

所有媒体工具自动将输出保存到 `target/images/` 或 `target/videos/`。
输入素材（从聊天工具接收的图片、本地文件等）应放置到对应的 `sources/<category>/` 子目录中。

## 配置

### 环境变量

除 `AGNES_API_KEY` 外，其余均为可选。

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `AGNES_API_KEY` | string | **必填** | Agnes AI API 密钥 |
| `AGNES_IMAGE_MODEL` | string | `agnes-image-2.0-flash` | 图像生成模型 |
| `AGNES_VIDEO_MODEL` | string | `agnes-video-v2.0` | 视频生成模型 |
| `AGNES_IMAGE_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/images/generations` | 图像 API 端点 |
| `AGNES_VIDEO_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/videos` | 视频 API 端点 |
| `AGNES_WORKSPACE_ROOT` | path | `~/workspace` | 媒体输出根目录 |
| `AGNES_IMAGE_TIMEOUT` | int | `180` | 图像请求超时时间（秒） |
| `AGNES_VIDEO_TIMEOUT` | int | `300` | 视频提交超时时间（秒） |
| `AGNES_DOWNLOAD_TIMEOUT` | int | `300` | 媒体下载超时时间（秒） |
| `AGNES_MAX_RETRIES` | int | `10` | 最大重试次数（图像 10+，视频 2） |
| `AGNES_RETRY_DELAY` | float | `30.0` | 重试间隔（秒）（图像 30s，视频 3s） |

### 插件 YAML 配置

`plugins/agnes_router/plugin.yaml` 定义了可在 Hermes Agent 配置中设置的额外参数：

```yaml
plugins:
  entries:
    agnes_router:
      workspace_root: /data/media        # 覆盖默认工作区
      image_endpoint: https://...        # 自定义 API 端点
      video_endpoint: https://...        # 自定义 API 端点
      image_model: agnes-image-2.0-flash
      video_model: agnes-video-v2.0
      image_timeout: 180
      video_timeout: 300
      download_timeout: 300
      max_retries: 10
      retry_delay: 30.0
```

## 部署方式

### 方式一：Hermes Agent 插件（推荐）

1. 将 `plugins/agnes_router` 目录复制到 Hermes Agent 插件路径：

   ```bash
   cp -r plugins/agnes_router ~/.hermes/profiles/<profile>/plugins/
   ```

2. 在 `config.yaml` 中启用插件：

   ```yaml
   plugins:
     enabled:
       - agnes_router
   ```

3. 设置 API 密钥：

   ```bash
   export AGNES_API_KEY="sk-你的密钥"
   ```

4. 重启 Hermes Agent。

### 方式二：Hermes Agent 技能

1. 将技能复制到技能路径：

   ```bash
   # 主技能（文档 + 脚本）
   cp -r skills/creative/agnes-media ~/.hermes/profiles/<profile>/skills/creative/

   # 异步视频监控技能（后台进程轮询工作流）
   cp -r skills/media/agnes-video-async-monitor ~/.hermes/profiles/<profile>/skills/media/
   ```

2. 这些技能文档化了工具的使用模式和最佳实践。实际的工具处理器来自插件（方式一）。

### 方式三：独立脚本使用

独立使用 `check_task.py`：

```bash
python3 skills/creative/agnes-media/scripts/check_task.py <video_id>
```

## 工具参考

### generate_image_via_pic01

从文本生成图像、编辑现有图像或合成多张图像。

**参数：**

| 参数 | 必填 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_name` | 是 | string | — | 项目标识（仅限 ASCII，不含斜杠） |
| `prompt` | 是 | string | — | 详细的视觉描述或编辑指令 |
| `file_name` | 是 | string | — | 带扩展名的输出文件名 |
| `size` | 否 | string | `1024x1024` | 图像尺寸（宽x高） |
| `image` | 否 | array[string] | — | 图生图/多图合用的图片 URL 或 Data URI |

**模式：**
- **文生图**: 不传 `image` — 从 prompt 生成
- **图生图**: `image: [1 URL]` — 编辑/变换现有图片
- **多图合成**: `image: [2+ URLs]` — 合成多张参考图

**输出：** 图像保存到 `<workspace>/<project>/target/images/<file_name>`

### generate_video_via_mov01

从文本、图像或关键帧序列生成视频。

**参数：**

| 参数 | 必填 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_name` | 是 | string | — | 项目标识（仅限 ASCII，不含斜杠） |
| `prompt` | 是 | string | — | 详细的视频/分镜描述 |
| `file_name` | 是 | string | — | 带扩展名的输出文件名 |
| `mode` | 否 | string | — | `"ti2vid"`（图生视频）或 `"keyframes"`（关键帧动画） |
| `image` | 否 | string | — | 图生视频的单张图片 URL |
| `height` | 否 | int | 768 | 视频高度（自动映射到标准预设） |
| `width` | 否 | int | 1152 | 视频宽度 |
| `num_frames` | 否 | int | 121 | 总帧数（81, 121, 241, 441） |
| `frame_rate` | 否 | number | 24 | 帧率 |
| `num_inference_steps` | 否 | int | — | 推理步数 |
| `seed` | 否 | int | — | 随机种子 |
| `negative_prompt` | 否 | string | — | 反向提示词 |
| `extra_body` | 否 | object | — | 关键帧动画：`{mode: "keyframes", image: [...]}` |

**输出：** 视频保存到 `<workspace>/<project>/target/videos/<file_name>`

**注意：** 视频生成是异步的。工具会立即返回任务 ID。使用 `agnes-video-async-monitor` 技能的 `monitor_video.py`（或关键帧用 `monitor_keyframe.py`）进行后台轮询，或使用 `check_task.py` 手动查询状态。
**务必使用** `GET /agnesapi?video_id=<real_video_id>` 查询，不要用 `GET /v1/videos/{task_id}`。

## 安全与行为规范

### 主控 Agent 身份

你是主控 Agent，负责所有的日常对话交互、文档编写、信息检索、项目空间管理和下级媒体任务调度。

你拥有两个下级专用能力接口。除非用户询问架构细节，否则不需要主动暴露内部代号：

1. `generate_image_via_pic01` — 图像生成服务，专职文生图、图生图、图像修改。底层 Agnes 模型为 `agnes-image-2.0-flash`。
2. `generate_video_via_mov01` — 音视频/视频生成服务，专职视频、动画和多媒体生成。底层 Agnes 模型为 `agnes-video-v2.0`。

### 工作空间与项目隔离准则

1. 所有文件写入、读取和媒体生成任务，必须在一个具体项目目录下进行。
2. 统一工作空间根目录是 `~/workspace`（可通过 `AGNES_WORKSPACE_ROOT` 配置）。
3. 如果用户没有显式指定当前项目，必须先询问或引导用户定义一个合规项目名，例如 `brand_retro`、`game_design`、`project_alpha`。
4. 调用下级媒体工具时，必须准确传入当前项目名 `project_name`，并拟定合理文件名，包含正确后缀名。
5. `project_name` 只能是单个目录名，不得包含 `../`、斜杠、反斜杠、绝对路径或任何试图跳出 workspace 的内容。
6. 绝对不要尝试构造 `/etc`、`../`、`~/.ssh` 等越界路径。
7. 遵循项目目录规范：`<project>/sources/` 存放输入素材，`<project>/target/` 存放输出结果。

### 交互与行为规范

- 只有当用户明确提出图像、海报、插画、视觉设计、视频、动画或多媒体生成诉求时，才触发对应媒体工具。
- 文本、检索、文档、代码、规划等普通任务由你自己处理，不调用媒体工具。
- 媒体工具成功后，在最终回复中告知用户本地保存路径；如果工具返回 `remote_url`，也可同时展示远程 URL。
- 媒体工具失败时，清楚报告失败原因。若是安全拦截，直接说明该路径请求被拦截。
- 默认对外只运行 `chat_01`；`pic_01` 和 `mov_01` 是内部/备用调试 profile，不对外启动 gateway。

## 错误处理

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `ok: false` 附带异步消息 | 视频已排队 | 通过 `/agnesapi?video_id=` 轮询任务状态 |
| `ok: false` 附带 `security_blocked` | 无效的项目/文件名 | 使用纯 ASCII 标识 |
| `ok: false` 附带 HTTP 503 | 图像队列已满 | 30 秒间隔重试，最多 10+ 次 |
| `ok: false` 附带 HTTP 错误 | API 返回错误 | 检查日志，重试 |
| `ok: false` 附带连接错误 | 网络问题 | 重试（自动） |
| `ok: false` 附带 "无效的令牌" | API 密钥错误 | 检查 AGNES_API_KEY |
| `ok: false` 附带 400 错误 | 参数错误 | 检查请求 body 格式 |

## 维护

### 更新插件

1. 编辑 `plugins/agnes_router/` 中的文件
2. 重启 Hermes Agent 以应用更改
3. 使用简单的图像生成进行测试

### 更新技能

1. 编辑 `skills/creative/agnes-media/SKILL.md` 或 `skills/media/agnes-video-async-monitor/SKILL.md`
2. 更新 frontmatter 中的版本号
3. 提交更改

### 故障排查

1. **API 密钥不工作**：验证 `AGNES_API_KEY` 已设置且不是字面量字符串
2. **视频一直未完成**：通过 `check_task.py` 检查状态 — 使用 `video_id` 而非 `task_id`
3. **图像返回 503 错误**：增加 `AGNES_MAX_RETRIES` 到 10+、`AGNES_RETRY_DELAY` 到 30s
4. **路径错误**：确保 project_name 仅包含 ASCII 字母、数字、`-`、`_`
5. **限速**：增加 `AGNES_MAX_RETRIES` 或 `AGNES_RETRY_DELAY`
6. **超时**：增加 `AGNES_IMAGE_TIMEOUT` 或 `AGNES_VIDEO_TIMEOUT`
7. **response_format 报错**：必须放在 `extra_body` 内，不能放在顶层

## 许可证

MIT 许可证 — 详见 LICENSE 文件。

## 兼容性

- Python 3.9+
- Hermes Agent（支持插件和技能的任意版本）
- Linux、macOS、Windows
- Agnes AI API（apihub.agnes-ai.com）