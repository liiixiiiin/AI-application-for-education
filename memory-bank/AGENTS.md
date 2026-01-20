# Repository Guidelines

## 重要提示（Always）
- Always：写任何代码前必须完整阅读 `memory-bank/architecture.md`（包含完整数据库结构）。
- Always：写任何代码前必须完整阅读 `memory-bank/design-document.md`。
- Always：每完成一个重大功能或里程碑后，必须更新 `memory-bank/architecture.md`。
- Always：代码必须模块化（多文件、按职责拆分）；禁止单体巨文件（monolith）。
- Always：前端部分的开发基于现有页面风格继续进行。

## 项目结构与模块组织
- `README.md`：项目简介。
- `design-document.md`：需求范围与系统设计。
- `tech-stack.md`：推荐技术栈与部署方式。
- 代码、测试与资源尚未落地；实施时建议按 `frontend/`、`backend/`、`assets/` 拆分并保持模块化。

## 构建、测试与开发命令
- 前端开发：`npm run dev`（在 `frontend/` 目录）
- 后端开发：`uvicorn app.main:app --reload`（在 `backend/` 目录）
- 构建前端：`npm run build`（在 `frontend/` 目录）

## 编码风格与命名规范
- 未配置格式化或 lint 工具前，遵循语言默认规范。
- 建议约定（落地后可调整）：
  - 前端：2 空格缩进；Vue 文件 `kebab-case`；组件 `PascalCase`。
  - 后端：4 空格缩进；Python 模块与函数使用 `snake_case`。
- 一旦引入格式化/检查工具（如 Prettier、Ruff/Black），需补充配置与运行命令。

## 测试指南
- 当前未配置测试框架。
- 测试落地后建议放在 `frontend/tests/` 与 `backend/tests/`，命名遵循框架默认（如 `*.spec.ts`、`test_*.py`）。
- 在此补充测试运行命令与最小覆盖要求。

## 提交与拉取请求规范
- 现有 Git 历史无统一提交规范。
- 提交信息建议使用简洁祈使句（如“Add lesson generator scaffold”）。
- PR 需包含清晰描述、实现要点；涉及 UI 的变更需附截图，并关联需求或设计文档。

## Agent 说明
- 随着目录结构或开发命令变化，及时更新本文档。
