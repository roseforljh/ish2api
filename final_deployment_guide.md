# 最终部署指南 (GitHub 工作流)

本指南适用于您已将最终版 `main.py` (v4.0.0) 提交并推送到您的 GitHub 仓库后的部署流程。

---

### **第 1 步：在 VPS 上配置 API 密钥**

如果您尚未在 VPS 上配置 `.env` 文件，请执行此步骤。

1.  **登录 VPS 并进入项目目录**:
    ```bash
    cd ~/ish2api  # 替换为您的项目目录
    ```

2.  **创建并编辑 `.env` 文件**:
    ```bash
    nano .env
    ```

3.  **写入您的 Puter.js API Key** (确保不包含 `Bearer ` 前缀):
    ```env
    PUTER_API_KEY=<您的真实Puter.js_API_Key>
    ```

4.  **保存并退出**: 按 `Ctrl + X`，然后按 `Y`，最后按 `Enter`。

---

### **第 2 步：从 GitHub 更新并部署**

现在，我们将从您的 GitHub 仓库拉取最新的代码，并重启 Docker 容器。

1.  **进入项目目录**:
    ```bash
    cd ~/ish2api
    ```

2.  **拉取最新代码**:
    ```bash
    git pull origin main
    ```
    *(这次您应该能看到 `main.py` 文件被更新的提示)*

3.  **重建并重启容器**:
    ```bash
    # 停止并移除旧容器
    docker stop ish2api-proxy-container
    docker rm ish2api-proxy-container

    # 使用 --no-cache 重新构建镜像，确保使用最新代码
    docker build --no-cache -t ish2api-proxy:latest .

    # 启动加载了 .env 文件的新容器
    docker run -d -p 8000:8000 --env-file ./.env --name ish2api-proxy-container --restart unless-stopped ish2api-proxy:latest
    ```

---

部署完成。您的代理服务现在运行的就是您 GitHub 仓库中的最新代码。