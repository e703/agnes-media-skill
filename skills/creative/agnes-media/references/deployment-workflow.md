# Agnes Media Skill — 源码到部署的同步工作流

## 目录结构

```
sources/agnes-media-skill/           ← 源码主目录（编辑入口）
├── plugins/agnes_router/            ← 插件代码（tools.py, schemas.py, workspace_manager.py ...）
├── skills/                          ← 技能文件
│   ├── creative/agnes-media/        ← 主技能
│   │   ├── SKILL.md
│   │   ├── references/
│   │   ├── templates/
│   │   └── scripts/
│   └── media/agnes-video-async-monitor/  ← 异步监控技能
│       └── SKILL.md
├── examples/                        ← 示例配置
├── README.md, README_CN.md, DEPLOYMENT_MANUAL.md
└── LICENSE

~/.hermes/profiles/user001/         ← 部署目录（运行时生效）
├── plugins/agnes_router/            ← 插件代码（与 sources 同步）
├── skills/                          ← 技能（与 sources 同步）
├── config.yaml                      ← 实际配置文件
└── ...
```

## 同步规则

1. **始终在 `sources/agnes-media-skill/` 中编辑源码**（包括插件代码和技能文件）
2. 修改后拷贝到 `~/.hermes/profiles/user001/` 对应路径
3. 插件代码需要 **重启 Hermes**（`/new` 或 `/exit` 后重新运行）才能生效
4. 技能文件（SKILL.md）立即生效，无需重启
5. 新技能如果在 profile 中直接创建（通过 `skill_manage`），必须同时拷贝到 `sources/agnes-media-skill/skills/` 下

## 单向同步（源码 → 部署）

```bash
# 全量同步插件
cp -r sources/agnes-media-skill/plugins/agnes_router/* \
      ~/.hermes/profiles/user001/plugins/agnes_router/

# 全量同步主技能
cp -r sources/agnes-media-skill/skills/creative/agnes-media/* \
      ~/.hermes/profiles/user001/skills/creative/agnes-media/

# 全量同步异步视频监控
cp -r sources/agnes-media-skill/skills/media/agnes-video-async-monitor/* \
      ~/.hermes/profiles/user001/skills/media/agnes-video-async-monitor/
```

## 反向同步（部署 → 源码）

⚠️ **部署目录可能比源码更新**。以下场景会导致部署目录有源码没有的文件：

- 通过 `skill_manage(action='write_file')` 直接在 profile 中创建了参考文件
- 技能被其他工具或脚本修改过
- 手动编辑了部署目录但忘了回写源码

### 一致性检查

```bash
# 主技能
diff -rq sources/agnes-media-skill/skills/creative/agnes-media \
         ~/.hermes/profiles/user001/skills/creative/agnes-media \
         --exclude=__pycache__

# 插件
diff -rq sources/agnes-media-skill/plugins/agnes_router \
         ~/.hermes/profiles/user001/plugins/agnes_router \
         --exclude=__pycache__

# 异步视频监控
diff -rq sources/agnes-media-skill/skills/media/agnes-video-async-monitor \
         ~/.hermes/profiles/user001/skills/media/agnes-video-async-monitor \
         --exclude=__pycache__
```

`diff -rq` 输出解读：

| 输出模式 | 含义 | 动作 |
|----------|------|------|
| `Only in sources/...: file` | 源码有，部署没有 | 执行单向同步 `cp` 到部署目录 |
| `Only in deploy/...: file` | 部署有，源码没有（**反同步**） | `cp` 回源码目录 |
| `Files ... differ` | 两边内容不同 | 用 `diff` 具体查看差异，取较新版本同步 |

### 反同步操作

```bash
# 将部署目录新增/修改的文件复制回源码
cp ~/.hermes/profiles/user001/skills/creative/agnes-media/references/new_file.md \
   sources/agnes-media-skill/skills/creative/agnes-media/references/new_file.md

# 全量反同步（当部署目录整体更新时）
cp -r ~/.hermes/profiles/user001/skills/creative/agnes-media/* \
      sources/agnes-media-skill/skills/creative/agnes-media/
```

## 验证

确认双向一致后，运行 `diff -rq` 检查应输出空（零差异）。

## 注意

- 两边文件应始终一致 — diff 检查确认无误后再部署
- 部署后必须重启 Hermes 才能加载新的插件代码（普通的 `/reload` 或 `/reload-skills` 不够）
- **反同步后**必须提交 git commit，否则下次克隆会丢失部署目录中的修改
- `__pycache__` 目录应始终排除在同步和 diff 之外