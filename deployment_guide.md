# VPS 部署与配置最终指南 (v3.2.0 - 认证修复版)

本文档是您配置、部署、使用和维护多提供商代理服务的最终指南。

**核心修复:** v3.1.0 版本中的 `docker run` 命令缺少了加载 `.env` 文件的参数，导致认证失败。本版已修复此问题。

---

### **第 1 部分：获取 API 密钥 (以 Puter.js 为例)**

(此部分内容不变，用于参考)

1.  **登录 Puter.js**: 访问 `https://puter.com/` 并登录。
2.  **进入开发者设置**: 点击右上角头像 -> “**Developer Settings**”。
3.  **复制 API Key**: 在 “**Personal Access Token**” 区域，复制您的密钥。

---

### **第 2 部分：在 VPS 上创建并配置 `.env` 文件**

(此部分内容不变，用于参考)

1.  **进入项目目录**:
    ```bash
    cd ~/ish2api
    ```

2.  **创建/编辑 `.env` 文件**:
    ```bash
    nano .env
    ```

3.  **写入密钥** (确保不包含 `Bearer ` 前缀):
    ```env
    PUTER_API_KEY=<您的真实Key>
    ```

4.  **保存并退出**: `Ctrl + X`, `Y`, `Enter`。

---

### **第 3 部分：部署与更新 (关键修复)**

请严格按照以下命令执行，特别是最后一步的 `docker run` 命令。

1.  **确保代码最新**: 确保您 VPS 上的 `main.py` 是最新版本。

2.  **执行部署命令**:
    在您的项目目录中，依次执行以下命令。
    ```bash
    # 1. 停止并移除旧容器
    docker stop ish2api-proxy-container
    docker rm ish2api-proxy-container

    # 2. 重新构建镜像
    docker build -t ish2api-proxy:latest .

    # 3. 启动新容器 (已加入 --env-file 参数)
    docker run -d -p 8000:8000 --env-file ./.env --name ish2api-proxy-container --restart unless-stopped ish2api-proxy:latest
    ```
    **注意：** 新命令中增加了 `--env-file ./.env`，它会把当前目录下的 `.env` 文件中的所有变量加载到容器中。

---

### **第 4 部分：使用代理服务**

部署完成后，您的认证问题应该已经解决。

- **请求 Puter.js 的 Claude Sonnet 4:**
  - **API 地址:** `http://<你的VPS_IP>:8000/puter/v1/chat/completions`
  - **请求体中的 `model` 字段:** `"operadriver-anthropic/claude-sonnet-4"`