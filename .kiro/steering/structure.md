# 项目结构

## 顶层目录

```
optimus-plugins-official/
├── .claude-plugin/          # 插件仓库元数据
│   └── marketplace.json     # 版本号、插件注册表
├── .claude/skills/          # 项目级 Skills（不进 marketplace，仅本仓库开发用）
│   ├── commit-cc-plugin/    # 提交发布专用 Skill
│   └── sync-cc-tips/        # tips.jsonl 自动同步 Skill
├── .kiro/                   # Kiro CLI 配置
│   ├── steering/            # 项目指导文档
│   └── skills/              # Kiro Skills（符号链接）
├── plugins/                 # ⭐ 8 个领域插件（核心内容）
├── docs/                    # 参考文档（Claude 官方博客、C# 文档等）
├── CLAUDE.md                # Claude Code 项目指导文档
├── README.md                # 仓库说明
└── LICENSE                  # MIT License
```

## 插件目录规范

每个插件遵循统一目录结构：

```
plugins/{plugin-name}/
├── skills/                  # 必须 — Skill 定义
│   └── {skill-name}/
│       ├── SKILL.md         # Skill 主文件（含 frontmatter 版本号）
│       ├── CHANGELOG.md     # 变更日志（必须）
│       ├── references/      # 参考文档（可选）
│       ├── scripts/         # 辅助脚本（可选）
│       ├── templates/       # 模板文件（可选）
│       ├── assets/          # 资源文件（可选）
│       └── test-prompts.json # 测试用例（可选）
├── hooks/                   # 可选 — Hook 配置
│   ├── hooks.json           # Hook 声明
│   └── {hook-type}/         # Hook 实现脚本
├── commands/                # 可选 — Command 定义
├── subagents/               # 可选 — Subagent 定义
└── mcp/                     # 可选 — MCP 服务器（或用 .mcp.json）
```

## 8 个插件一览

| 插件 | 路径 | Skills 数量 | 特殊组件 |
|------|------|-------------|----------|
| optimus-frontend-plugin | `plugins/optimus-frontend-plugin` | 3 | 含唯一复合 Skill |
| optimus-backend-plugin | `plugins/optimus-backend-plugin` | 3 | Python 辅助脚本 |
| optimus-qa-plugin | `plugins/optimus-qa-plugin` | 7 | 最多 Skills 的插件 |
| optimus-prd-plugin | `plugins/optimus-prd-plugin` | 3 | — |
| optimus-feishu-plugin | `plugins/optimus-feishu-plugin` | 3 | — |
| optimus-office-plugin | `plugins/optimus-office-plugin` | 7 | Node.js 脚本 |
| optimus-devops-plugin | `plugins/optimus-devops-plugin` | 5 | Hooks + 脚本 |
| optimus-mcp-servers | `plugins/optimus-mcp-servers` | 0 | 仅 .mcp.json |

## 命名约定

- **插件目录名**：`optimus-{domain}-plugin`（MCP 例外：`optimus-mcp-servers`）
- **Skill 目录名**：`optimus-{domain}-{功能}` 或 `{功能名}`（较新的独立 skill）
- **文件名**：全小写，连字符分隔
- **SKILL.md frontmatter**：必须包含 `name`、`version`、`description`

## 关键文件速查

| 文件 | 用途 |
|------|------|
| `.claude-plugin/marketplace.json` | 仓库版本号和插件注册 |
| `.claude/skills/commit-cc-plugin/SKILL.md` | 提交发布工作流（强制使用） |
| `.claude/skills/sync-cc-tips/SKILL.md` | tips 文件同步 Skill |
| `plugins/optimus-devops-plugin/hooks/hooks.json` | Hooks 配置入口 |
| `plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl` | 280 条使用技巧 |
| `plugins/optimus-mcp-servers/.mcp.json` | MCP 服务器声明 |
| `plugins/optimus-frontend-plugin/skills/optimus-fe-dev/ARCHITECTURE.md` | 复合 Skill 架构参考 |
