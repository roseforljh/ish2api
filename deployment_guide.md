# VPS 部署与配置最终指南 (v4.2.0 - 终极修复版)

本文档是您配置、部署、使用和维护多提供商代理服务的最终指南。

**核心修复:** 之前的部署由于 `git pull` 未能更新 `main.py`，导致新功能代码没有生效。本版将代码更新方式明确为**手动复制粘贴**。

---

### **第 1 部分：获取并配置 API 密钥**

(内容不变，供参考)

---

### **第 2 部分：在 VPS 上更新代码与配置**

#### **2.1 手动更新 `main.py` (最关键步骤)**

1.  **复制最新代码**: 在与 AI 的聊天界面中，复制最新版本 (v4.0.0 或更高) 的 `main.py` 的**全部**代码。
2.  **登录 VPS 并进入目录**:
    ```bash
    cd ~/ish2api
    ```
3.  **编辑 `main.py`**:
    ```bash
    nano main.py
    ```
4.  **粘贴并覆盖**: 在 `nano` 编辑器中，删除所有旧代码，然后粘贴您复制的最新代码。
5.  **保存并退出**: 按 `Ctrl + X`，然后按 `Y`，最后按 `Enter`。

#### **2.2 配置 `.env` 文件**

1.  **编辑 `.env` 文件**:
    ```bash
    nano .env
    ```
2.  **写入密钥** (确保不包含 `Bearer ` 前缀):
    ```env
    PUTER_API_KEY=<您的真实Key>
    ```
3.  **保存并退出**。

---

### **第 3 部分：部署与更新**

在您的项目目录中，依次执行以下命令。

```bash
# 1. 停止并移除旧容器
docker stop ish2api-proxy-container
docker rm ish2api-proxy-container

# 2. 重新构建镜像 (使用 --no-cache 确保使用最新的 main.py)
docker build --no-cache -t ish2api-proxy:latest .

# 3. 启动新容器 (使用 --env-file 加载密钥)
docker run -d -p 8000:8000 --env-file ./.env --name ish2api-proxy-container --restart unless-stopped ish2api-proxy:latest
```

---

### **第 4 部分：使用代理服务**

部署完成后，您的 Puter.js 模型应该可以正常工作了。

- **请求 Puter.js 的 Claude Sonnet 4:**
  - **API 地址:** `http://<你的VPS_IP>:8000/puter/v1/chat/completions`
  - **请求体中的 `model` 字段:** `"openrouter:anthropic/claude-sonnet-4"`