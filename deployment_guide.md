# VPS 部署与配置指南 (v3.0.0)

本文档将指导您如何配置、部署并使用您的多提供商代理服务。

**核心变更:**
- **移除模型映射:** 客户端现在必须直接使用后端真实模型ID。
- **`.env` 文件管理密钥:** API Key 将通过 `.env` 文件进行管理，更加安全和标准。

---

### 第 1 步：找到并配置 Puter.js API Key

Puter.js 的 API 需要认证。您需要先找到您的个人 API Key。

1.  **登录 Puter.js**: 在浏览器中访问 `https://puter.com/` 并登录您的账户。
2.  **进入开发者设置**: 登录后，点击页面右上角的您的头像或账户图标，在下拉菜单中找到并点击“**Developer Settings**”（开发者设置）。
3.  **复制 API Key**: 在开发者设置页面，您会看到一个名为 “**Personal Access Token**” 或 “**API Key**” 的区域。点击“复制”按钮，将这个 Key 复制到您的剪贴板。**请妥善保管此 Key，不要泄露给他人。**

---

### 第 2 步：在 VPS 上创建 `.env` 文件

现在，我们将把复制好的 Key 保存到您 VPS 的项目目录下的一个 `.env` 文件中。

1.  **进入项目目录**:
    通过 SSH 登录到您的 VPS，并确保您位于正确的项目目录中。
    ```bash
    cd ~/ish2api  # 如果您的目录名不同，请替换
    ```

2.  **创建并编辑 `.env` 文件**:
    使用 `nano` 编辑器创建一个新文件。
    ```bash
    nano .env
    ```

3.  **写入 Key**:
    在 `nano` 编辑器中，粘贴以下内容，并将 `<这里替换成您从Puter.js复制的真实Key>` 替换为您真实的 API Key。
    ```
    PUTER_API_KEY=<这里替换成您从Puter.js复制的真实Key>
    ```

4.  **保存并退出**: 按 `Ctrl + X`，然后按 `Y`，最后按 `Enter`。

---

### 第 3 步：更新并重新部署 Docker 容器

1.  **更新 `main.py`**:
    确保您 VPS 上的 `main.py` 文件是我们刚刚修改过的最新版本（即移除了模型映射功能的版本）。如果不是，请从本地复制最新代码并覆盖它。

2.  **重新部署**:
    在您的项目目录中，依次执行以下命令来重建并重启您的服务。
    ```bash
    # 停止并移除旧容器
    docker stop ish2api-proxy-container
    docker rm ish2api-proxy-container

    # 重新构建镜像
    docker build -t ish2api-proxy:latest .

    # 启动新容器
    docker run -d -p 8000:8000 --name ish2api-proxy-container --restart unless-stopped ish2api-proxy:latest
    ```

---

### 第 4 步：如何使用

部署完成后，您需要在客户端发送请求时，**直接使用后端模型 ID**。

- **请求 Puter.js 的 Claude Sonnet 4:**
  - **API 地址:** `http://<你的VPS_IP>:8000/puter/v1/chat/completions`
  - **请求体中的 `model` 字段:** `"operadriver-anthropic/claude-sonnet-4"`