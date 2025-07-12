# ish2api

一个为 `ish.junioralive.in` 服务提供 OpenAI 兼容 API 的代理程序。

> ⚠️ **项目状态**: 这是一个初步实现的概念验证项目，作者不打算进行后续更新。欢迎您 Fork 本项目并根据自己的需求进行修改。

## ✨ 功能特性

*   **OpenAI 兼容**: 提供标准的 `/v1/chat/completions` 接口，可无缝接入支持 OpenAI API 的各类客户端和应用。
*   **模型映射**: 支持通过简单的模型名称调用后端不同的实际模型。
*   **流式响应**: 完全支持流式输出，提供实时的打字机效果。
*   **轻松部署**: 基于 FastAPI 构建，轻量且易于部署。

## 🤖 可用模型

在请求的 `body` 中使用“请求名称”即可调用对应的后端实际模型。

| 请求名称 (model)     | 后端实际模型       |
| -------------------- | ------------------ |
| `grok`               | `grok-3-mini`      |
| `openai-large`       | `gpt-4.1`          |
| `deepseek`           | `deepseek-v3`      |
| `deepseek-reasoning` | `deepseek-r1-0528` |

## 🚀 快速开始

pip install fastapi "uvicorn[standard]" httpx pydantic python-dotenv
python main.py
