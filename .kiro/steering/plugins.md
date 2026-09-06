# 插件详情

## optimus-frontend-plugin — 前端开发工具集

**Skills:**
- `optimus-fe-dev` — 前端全流程开发（唯一复合 Skill，5阶段：需求收集→分析规划→代码生成→交付物生成→验证完成）
- `optimus-design-ui` — UI 设计规范管理
- `wpf-code-review` — WPF 全量代码审查

**特色:** 复合 Skill 采用 Subagent 驱动并行生成，详见 ARCHITECTURE.md。

---

## optimus-backend-plugin — 后端开发工具集

**Skills:**
- `optimus-backend-dev` — 后端开发（架构设计、API开发）
- `optimus-backend-api-connect` — API 连接和文档生成
- `csharp-code-review` — C# 代码审查

**辅助脚本:** fetch_swagger.py、fetch_feishu_doc.py、fetch_webpage_api.py

---

## optimus-qa-plugin — 测试 QA 工具集

**Skills（7个，最多的插件）:**
- `optimus-qa-test-design` — 测试用例设计
- `optimus-qa-test-report` — 测试报告生成
- `optimus-qa-jmeter-scripts` — JMeter 性能测试脚本
- `optimus-qa-ui-scripts` — UI 自动化测试脚本
- `optimus-qa-ui-consistency-check` — UI 一致性检查
- `optimus-qa-feishu-project-sync` — 飞书测试项目同步
- `optimus-qa-feishu-project-xmind` — 飞书项目转 XMind（含 converter.py）

---

## optimus-prd-plugin — PRD 管理工具集

**Skills:**
- `prd-creator` — PRD 文档创建
- `prd-optimizer` — PRD 文档优化
- `prd-reviewer` — PRD 文档审查

---

## optimus-feishu-plugin — 飞书集成工具集

**Skills:**
- `optimus-feishu-doc-transfer` — 飞书文档读写（通用/临时，不走部门规范）
- `optimus-feishu-project-docs-push` — 项目文档规范化推送到飞书
- `optimus-feishu-project-docs-pull` — 项目文档从飞书拉取到本地

---

## optimus-office-plugin — Office 文档处理工具集

**Skills（7个）:**
- `docx-writer` — Word 文档生成（含模板和脚本）
- `optimus-office-docx` — Office DOCX 处理
- `xlsx-editor` — Excel 编辑和报表
- `pptx-editor` — PowerPoint 演示文稿
- `pdf-creator` — PDF 文档生成
- `file-to-markdown` — 本地文件转 Markdown
- `web-to-markdown` — 网页内容抓取转 Markdown

---

## optimus-devops-plugin — DevOps 工具集

**Skills（4个）:**
- `jenkins-build` — Jenkins CI/CD 构建触发
- `weekly-report` — 工作周报转写（四段式标准格式）
- `sync-skill-symlinks` — skill 目录符号链接同步（Claude/Kiro/Codex）
- `project-analyze` — 项目结构分析

**Hooks（内置自动加载）:**
- `SessionStart` — 会话启动展示技巧（267条智能轮播，带进度追踪）
- `Notification` — Windows 权限提示通知

**关键文件:**
- `hooks/hooks.json` — Hook 配置
- `hooks/sessionstart/tips.jsonl` — 280条技巧库
- `hooks/sessionstart/show-tip.sh` — 轮播脚本
- `hooks/notification/permission-notify.ps1` — 通知脚本

---

## optimus-mcp-servers — MCP 服务器集成

**无 Skills，仅 MCP 配置（.mcp.json）:**

| 服务名 | 连接方式 | 认证 |
|--------|----------|------|
| GitHub Copilot | HTTP (api.githubcopilot.com) | GITHUB_TOKEN |
| MasterGo Magic | stdio (npx @mastergo/magic-mcp) | MASTERGO_TOKEN |
| Feishu Project | stdio (npx @lark-project/mcp) | FEISHU_PROJECT_TOKEN |

---

## 项目级 Skills（.claude/skills/，不进 marketplace）

- `commit-cc-plugin` — 提交发布工作流（强制使用，替代手动 git）
- `sync-cc-tips` — tips.jsonl 自动同步（从 Claude Code changelog 同步技巧）
