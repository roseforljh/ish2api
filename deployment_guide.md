# VPS 部署与配置最终指南 (v3.2.1 - 命令修复版)

本文档是您配置、部署、使用和维护多提供商代理服务的最终指南。

**核心修复:** v3.2.0 版本中的 `docker run` 命令存在拼写错误 (`--env-file` 后缺少文件名)。本版已修复。

---

### **第 1 部分：获取 API 密钥**

(内容不变，供参考)

---

### **第 2 部分：在 VPS 上创建并配置 `.env` 文件**

(内容不变，供参考)

---

### **第 3 部分：部署与更新 (关键修复)**

请严格按照以下命令执行。

1.  **确保代码最新**:
    ```bash
    # 从您的 git 仓库拉取最新代码
    git pull origin main
    ```

2.  **执行部署命令**:
    在您的项目目录中，依次执行以下命令。
    ```bash
    # 1. 停止并移除旧容器 (如果容器不存在，会提示错误，可以安全忽略)
    docker stop ish2api-proxy-container
    docker rm ish2api-proxy-container

    # 2. 重新构建镜像
    docker build -t ish2api-proxy:latest .

    # 3. 启动新容器 (已修正 --env-file 的用法)
    docker run -d -p 8000:8000 --env-file ./.env --name ish2api-proxy-container --restart unless-stopped ish2api-proxy:latest
    ```
    **注意：** 正确的用法是 `--env-file ./.env`，它会把当前目录下的 `.env` 文件中的所有变量加载到容器中。

---

### **第 4 部分：使用代理服务**

部署完成后，您的认证问题应该已经解决。

- **请求 Puter.js 的 Claude Sonnet 4:**
  - **API 地址:** `http://<你的VPS_IP>:8000/puter/v1/chat/completions`
  - **请求体中的 `model` 字段:** `"operadriver-anthropic/claude-sonnet-4"`