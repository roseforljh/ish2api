# ish2api 🚀

一个为 `ish.junioralive.in` 服务提供 OpenAI 兼容 API 的代理程序，内置广告过滤，并提供一键式 Docker 部署方案。

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-blue)](https://fastapi.tiangolo.com/)
[![Docker Support](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Project Status](https://img.shields.io/badge/status-archived-red.svg)](#-项目状态)

## ✨ 功能特性

*   **OpenAI 兼容**: 提供标准的 `/v1/chat/completions` 接口，可无缝接入支持 OpenAI API 的各类客户端和应用。
*   **模型映射**: 支持通过简单的模型名称调用后端不同的实际模型。
*   **广告过滤**: 自动检测并拦截响应流中的 "Sponsor" 广告内容，保证输出纯净。
*   **流式响应**: 完全支持流式输出，提供实时的打字机效果。
*   **一键部署**: 使用 Docker 实现跨平台的快速、隔离部署。

## 🤖 可用模型

在请求的 `body` 中使用“请求名称”即可调用对应的后端实际模型。

| 请求名称 (model)     | 后端实际模型       |
| -------------------- | ------------------ |
| `grok`               | `grok-3-mini`      |
| `openai-large`       | `gpt-4.1`          |
| `deepseek`           | `deepseek-v3`      |
| `deepseek-reasoning` | `deepseek-r1-0528` |

## 🚀 部署指南 (Docker)

这是本项目推荐的唯一部署方式，它能屏蔽环境差异，实现快速启动。

### 第 1 步：前提准备

确保您的系统已经安装了 [Docker](https://www.docker.com/products/docker-desktop/)。

### 第 2 步：获取源码

使用 `git` 克隆本仓库到您的本地设备。

    git clone https://github.com/Midnight3189381/ish2api.git
    cd ish2api

### 第 3 步：构建 Docker 镜像

在项目根目录下，运行以下命令。此命令会读取 `Dockerfile` 并创建一个名为 `ish2api-proxy` 的本地镜像。

    docker build -t ish2api-proxy:latest .

### 第 4 步：启动容器

使用刚刚构建的镜像来启动服务容器。

    docker run -d -p 8000:8000 --name ish2api-proxy-container --restart unless-stopped ish2api-proxy:latest

**参数说明:**
*   `-d`: 后台模式运行容器。
*   `-p 8000:8000`: 将主机的 8000 端口映射到容器的 8000 端口。
*   `--name ish2api-proxy-container`: 为容器指定一个易于管理的名称。
*   `--restart unless-stopped`: 设置容器的重启策略，确保服务持续可用。

服务现在已经成功运行在 `http://127.0.0.1:8000`。

## ⚙️ 容器管理

您可以使用以下命令来管理正在运行的容器：

*   **查看实时日志**:

        docker logs -f ish2api-proxy-container

*   **停止服务**:

        docker stop ish2api-proxy-container

*   **重新启动服务**:

        docker start ish2api-proxy-container

*   **彻底移除容器 (停止后)**:

        docker rm ish2api-proxy-container

## 💡 使用示例

服务启动后，您可以将任何 OpenAI 客户端的 API 地址指向 `http://127.0.0.1:8000/v1/chat/completions`。

以下是使用 `curl` 的测试示例：

    curl -N http://127.0.0.1:8000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "grok",
        "messages": [{"role": "user", "content": "用中文介绍一下你自己"}],
        "stream": true
      }'

您将会在终端中看到模型实时返回的流式响应，且不包含任何广告内容。

## ⚠️ 项目状态
这是一个初步实现的概念验证项目，作者不打算进行后续更新。欢迎您 Fork 本项目并根据自己的需求进行修改和完善。
